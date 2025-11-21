# AI Reasoning & Cognitive Pattern Framework (TOOL-AI-001)

A comprehensive Python framework for advanced AI reasoning using Chain-of-Thought (CoT), Tree-of-Thoughts (ToT), and context management with LLM integration.

## Overview

This framework implements sophisticated reasoning patterns for AI-powered decision making, supporting:

- **Chain-of-Thought (CoT)**: Multi-step reasoning with explicit intermediate thoughts
- **Tree-of-Thoughts (ToT)**: Branching exploration with pruning and backtracking
- **Context Management**: History tracking, compression, and retrieval
- **LLM Integration**: OpenAI (GPT-4) and Anthropic (Claude 3) support
- **Evaluation & Metrics**: Quality assessment and self-consistency checking
- **Cost Tracking**: Token usage monitoring and budget management
- **Tracing**: LangSmith integration for observability

## Protocol Coverage

This tool implements 9 protocols (11% coverage):

- `P-COG-COT`: Chain-of-Thought protocol
- `P-COG-TOT`: Tree-of-Thought protocol
- `P-ASR-ADR-ALIGNMENT`: ASR to ADR reasoning and alignment
- `P-PATTERN-MANAGEMENT`: Architectural pattern selection
- `P-CONTEXT-VALIDATION`: Context integrity checking
- `P-KNOW-KG-INTERACTION`: Knowledge graph reasoning
- `P-KNOW-RAG`: Retrieval-Augmented Generation
- `P-ORCHESTRATION`: Multi-agent coordination
- `P-RESOURCE`: Resource allocation and optimization

## Installation

### Prerequisites

- Python 3.8+
- pip or uv package manager

### Install Dependencies

```bash
# Install all dependencies
pip install -r requirements.txt

# Or using uv (faster)
uv pip install -r requirements.txt
```

### API Keys Setup

Set your API keys as environment variables:

```bash
# For OpenAI
export OPENAI_API_KEY="your-openai-api-key"

# For Anthropic
export ANTHROPIC_API_KEY="your-anthropic-api-key"

# For LangSmith (optional)
export LANGSMITH_API_KEY="your-langsmith-api-key"
```

## Quick Start

### 1. Chain-of-Thought Reasoning

```python
import asyncio
from chain_of_thought import ChainOfThoughtReasoner, ReasoningStrategy
from llm_providers import LLMProviderFactory, LLMProvider

async def main():
    # Initialize LLM provider
    provider = LLMProviderFactory.create(
        provider_type=LLMProvider.OPENAI,
        api_key="your-api-key",
        model="gpt-4"
    )

    # Create reasoner
    reasoner = ChainOfThoughtReasoner(
        llm_provider=provider,
        max_steps=5,
        temperature=0.7
    )

    # Perform reasoning
    result = await reasoner.reason(
        question="What is the best database for a social media application?",
        strategy=ReasoningStrategy.ZERO_SHOT,
        context="High read/write ratio, needs scalability"
    )

    # Display results
    print(f"Answer: {result.final_answer}")
    print(f"Confidence: {result.confidence:.2%}")
    print(f"\nReasoning Steps:")
    for step in result.steps:
        print(f"Step {step.step_number}: {step.thought}")

asyncio.run(main())
```

### 2. Tree-of-Thoughts Exploration

```python
import asyncio
from tree_of_thought import TreeOfThoughtsExplorer, SearchStrategy

async def main():
    # Initialize explorer
    explorer = TreeOfThoughtsExplorer(
        llm_provider=provider,
        max_depth=3,
        branching_factor=3,
        beam_width=2
    )

    # Explore solution space
    result = await explorer.explore(
        question="Design a scalable notification system",
        strategy=SearchStrategy.BEST_FIRST
    )

    # Display best path
    print(f"Best Path Score: {result.best_path.total_score:.2f}")
    for i, node in enumerate(result.best_path.nodes):
        print(f"{i}. [{node.score:.2f}] {node.thought}")

asyncio.run(main())
```

### 3. Using the CLI

```bash
# Chain-of-Thought reasoning
python ai_reasoner.py cot-reason \
    "What architecture should we use?" \
    --strategy zero_shot \
    --context "Small team, MVP timeline" \
    --evaluate

# Tree-of-Thoughts exploration
python ai_reasoner.py tot-explore \
    "Design a caching strategy" \
    --strategy beam_search \
    --max-depth 3 \
    --visualize

# Context management
python ai_reasoner.py context add \
    --content "User wants microservices architecture" \
    --role user

# Cost report
python ai_reasoner.py cost --export cost_report.json
```

## Configuration

Create a `config.yaml` file (see `config.yaml` for template):

```yaml
llm_provider: "openai"
model: "gpt-4"
temperature: 0.7
max_tokens: 8000

cot:
  max_steps: 5
  enable_reflection: true

tot:
  max_depth: 3
  branching_factor: 3

cost:
  budget_limit: 10.0
  budget_warning_threshold: 0.8
```

Then use with CLI:

```bash
python ai_reasoner.py --config config.yaml cot-reason "Your question"
```

## Features

### Chain-of-Thought (CoT) Reasoning

**Strategies:**
- **Zero-Shot**: Direct reasoning without examples
- **Few-Shot**: Learning from provided examples
- **Self-Consistency**: Multiple reasoning paths with voting
- **Reflection**: Self-critique and refinement

**Usage:**

```python
# Zero-shot reasoning
result = await reasoner.reason(
    question="Should we use REST or GraphQL?",
    strategy=ReasoningStrategy.ZERO_SHOT
)

# Few-shot with examples
examples = [
    {
        "question": "SQL vs NoSQL?",
        "reasoning": "Step 1: Analyze data... Step 2: Consider scale...",
        "answer": "Use PostgreSQL for structured data"
    }
]

result = await reasoner.reason(
    question="What database to use?",
    strategy=ReasoningStrategy.FEW_SHOT,
    examples=examples
)

# Self-consistency (3 attempts, vote for best)
result = await reasoner.reason(
    question="Best caching strategy?",
    strategy=ReasoningStrategy.SELF_CONSISTENCY
)
```

### Tree-of-Thoughts (ToT) Exploration

**Search Strategies:**
- **Breadth-First**: Explore all options at each level
- **Depth-First**: Deep exploration of paths
- **Best-First**: Greedy selection of highest-scored nodes
- **Beam Search**: Balance between exploration and efficiency

**Usage:**

```python
# Best-first search
result = await explorer.explore(
    question="Design a rate limiting system",
    strategy=SearchStrategy.BEST_FIRST
)

# Beam search with width 3
explorer = TreeOfThoughtsExplorer(
    llm_provider=provider,
    max_depth=4,
    beam_width=3
)

result = await explorer.explore(
    question="Choose authentication method",
    strategy=SearchStrategy.BEAM_SEARCH
)

# Visualize the tree
from tree_of_thought import ToTVisualizer
ToTVisualizer.print_tree(result)
```

### Context Management

**Features:**
- Conversation history tracking
- Automatic compression when context is full
- Semantic similarity search (with embeddings)
- Redis persistence (optional)
- Context validation

**Usage:**

```python
from context_manager import ContextManager

manager = ContextManager(
    max_tokens=8000,
    sliding_window_size=10,
    compression_threshold=0.8
)

# Add entries
await manager.add_entry(
    content="User asks about microservices",
    role="user",
    tokens=50
)

# Get context
context = await manager.get_context(max_entries=5)

# Compress when needed
stats = await manager.compress_context(llm_provider)

# Search similar entries (requires embedding model)
similar = await manager.search_similar("microservices", top_k=3)

# Validate integrity
validation = await manager.validate_context()
```

### Evaluation & Metrics

**Metrics:**
- Accuracy (against ground truth)
- Consistency (self-consistency across attempts)
- Completeness (sufficient reasoning depth)
- Quality (logical coherence and clarity)
- Efficiency (token and time usage)

**Usage:**

```python
from evaluator import ReasoningEvaluator

evaluator = ReasoningEvaluator(llm_provider)

# Evaluate CoT result
evaluations = await evaluator.evaluate_cot(
    result,
    ground_truth="Expected answer"
)

for metric, eval_result in evaluations.items():
    print(f"{metric}: {eval_result.percentage():.1f}%")

# Self-consistency evaluation
results = [result1, result2, result3]
consistency = await evaluator.evaluate_self_consistency(
    results,
    question="Original question"
)
```

### Cost Tracking

**Features:**
- Token counting with tiktoken
- Cost estimation for all models
- Budget alerts and warnings
- Usage breakdown by model
- Cost optimization recommendations

**Usage:**

```python
from cost_tracker import CostTracker, CostOptimizer

tracker = CostTracker(
    budget_limit=10.0,
    warning_threshold=0.8
)

# Track usage
tracker.track_usage(
    operation_id="op_1",
    model="gpt-4",
    input_tokens=1000,
    output_tokens=500
)

# Get statistics
stats = tracker.get_statistics()
print(f"Total cost: ${stats['total_cost']:.4f}")
print(f"Budget utilization: {stats['budget_utilization']:.1%}")

# Export report
tracker.export_report("cost_report.json")

# Get recommendations
model = CostOptimizer.recommend_model(
    task_complexity="moderate",
    budget_conscious=True
)
```

### LangSmith Tracing

**Features:**
- Trace lifecycle management
- Event logging (LLM calls, reasoning steps, errors)
- Performance metrics
- Trace export and analysis

**Usage:**

```python
from tracer import LangSmithTracer, TracingContext

tracer = LangSmithTracer(
    project_name="my-project",
    api_key="your-langsmith-key",
    enabled=True
)

# Use context manager
with TracingContext(tracer, "CoT Reasoning", tags=["production"]) as trace_id:
    result = await reasoner.reason(question)

    # Add custom events
    tracer.trace_llm_call(
        trace_id=trace_id,
        provider="openai",
        model="gpt-4",
        prompt="...",
        response="...",
        token_count=150,
        duration_ms=1500.0
    )

# Analyze performance
analysis = tracer.analyze_performance(trace_id)
print(f"Total duration: {analysis['total_duration_ms']:.2f}ms")
print(f"LLM calls: {analysis['llm_calls']}")
```

## Examples

Run the provided examples:

```bash
# Chain-of-Thought example
python example_cot.py

# Tree-of-Thoughts example
python example_tot.py
```

These demonstrate:
- Different reasoning strategies
- Evaluation metrics
- Cost tracking
- Best practices

## Testing

Run the comprehensive test suite:

```bash
# Run all tests
pytest test_ai_reasoning.py -v

# With coverage
pytest test_ai_reasoning.py -v --cov=. --cov-report=term-missing

# Run specific test
pytest test_ai_reasoning.py::test_cot_zero_shot_reasoning -v
```

Test coverage: 80%+

All tests use mocked LLM calls, so no API keys are required.

## Best Practices

### Model Selection

**Simple tasks (FAQ, classification):**
- GPT-3.5-turbo (cost-effective)
- Claude 3 Haiku (fast, cheap)

**Moderate complexity (analysis, recommendations):**
- GPT-4o (balanced)
- Claude 3 Sonnet (good quality)

**Complex reasoning (architecture, design):**
- GPT-4 Turbo (comprehensive)
- Claude 3 Opus (highest quality)

### Temperature Tuning

- **0.0-0.3**: Deterministic, factual tasks
- **0.4-0.7**: Balanced creativity and consistency (recommended)
- **0.8-1.0**: High creativity, exploratory tasks

### Cost Optimization

1. **Use few-shot when possible**: Reduce steps needed
2. **Set appropriate max_steps**: Don't over-reason
3. **Enable pruning in ToT**: Reduce explored nodes
4. **Compress context regularly**: Reduce token usage
5. **Use cheaper models for evaluation**: GPT-3.5 for scoring

### Context Management

1. **Set compression threshold wisely**: 0.7-0.8 recommended
2. **Use sliding window**: Keep recent context fresh
3. **Enable Redis for persistence**: Across sessions
4. **Validate regularly**: Ensure integrity

### Tracing

1. **Enable in production**: For debugging and monitoring
2. **Use meaningful names**: Easy to identify traces
3. **Tag appropriately**: Filter and analyze
4. **Export periodically**: For long-term analysis

## Troubleshooting

### Issue: API Rate Limits

**Solution:**
```python
# Increase retry delay
provider = LLMProviderFactory.create(
    provider_type=LLMProvider.OPENAI,
    api_key=key,
    max_retries=5,
    retry_delay=2.0,
    rate_limit_per_minute=30
)
```

### Issue: High Token Usage

**Solutions:**
1. Reduce `max_steps` in CoT
2. Reduce `max_depth` and `branching_factor` in ToT
3. Enable context compression
4. Use more concise prompts

### Issue: Low Quality Results

**Solutions:**
1. Use higher temperature for creativity
2. Try few-shot with good examples
3. Enable reflection for self-critique
4. Use better model (GPT-4 vs GPT-3.5)

### Issue: Slow Execution

**Solutions:**
1. Use beam search instead of breadth-first
2. Increase pruning threshold
3. Reduce max depth/steps
4. Use faster model (GPT-4o vs GPT-4)

### Issue: Context Overflow

**Solutions:**
```python
# Enable automatic compression
manager = ContextManager(
    max_tokens=8000,
    compression_threshold=0.7,  # Compress earlier
    sliding_window_size=8  # Reduce window
)

# Manual compression
if manager.context_window.is_full():
    await manager.compress_context(llm_provider)
```

## Architecture

```
ai_reasoner.py          # Main CLI interface
├── chain_of_thought.py # CoT reasoning engine
├── tree_of_thought.py  # ToT exploration engine
├── context_manager.py  # Context management
├── llm_providers.py    # LLM integrations
├── prompt_templates.py # Template library
├── evaluator.py        # Quality metrics
├── tracer.py           # LangSmith tracing
└── cost_tracker.py     # Cost monitoring
```

## Performance Targets

- **CoT reasoning**: <5s for 3-5 steps
- **ToT exploration**: <30s for depth 3
- **Token usage**: <10K tokens per reasoning task
- **Context compression**: >50% size reduction
- **Reasoning accuracy**: >80% on benchmark tasks

## Protocol Integration Details

### P-COG-COT: Chain-of-Thought
- Implemented in `chain_of_thought.py`
- Supports zero-shot, few-shot, self-consistency, reflection
- Automatic step generation and conclusion detection

### P-COG-TOT: Tree-of-Thought
- Implemented in `tree_of_thought.py`
- Multiple search strategies (BFS, DFS, Best-First, Beam)
- Automatic pruning and path scoring

### P-CONTEXT-VALIDATION
- Implemented in `context_manager.py`
- Token count validation, chronological ordering
- Duplicate detection, integrity checks

### P-KNOW-RAG: Retrieval-Augmented Generation
- Context search with semantic similarity
- Embedding-based retrieval
- Context compression for efficiency

### P-ORCHESTRATION: Multi-agent Coordination
- Tracer provides observability across components
- Event tracking for coordination
- Performance metrics for optimization

### P-RESOURCE: Resource Allocation
- Token tracking and cost estimation
- Budget management and alerts
- Cost optimization recommendations

## Contributing

This framework follows the devCrew_s1 development guidelines:

1. Run code quality checks:
```bash
black *.py
isort *.py
flake8 *.py
mypy *.py --ignore-missing-imports
```

2. Run tests with coverage:
```bash
pytest test_ai_reasoning.py -v --cov=. --cov-report=html
```

3. Follow project naming conventions for all files

## License

Part of devCrew_s1 project - See project LICENSE file.

## Support

For issues, questions, or contributions, refer to the main devCrew_s1 repository.

## Changelog

### Version 1.0 (Initial Release)
- Chain-of-Thought reasoning (4 strategies)
- Tree-of-Thoughts exploration (4 search strategies)
- Context management with compression
- OpenAI and Anthropic LLM support
- Evaluation and quality metrics
- LangSmith tracing integration
- Cost tracking and budget management
- Comprehensive test suite (80%+ coverage)
- CLI interface with 5 commands
- Complete documentation and examples
