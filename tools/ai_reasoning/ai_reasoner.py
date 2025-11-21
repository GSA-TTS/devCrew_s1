"""
Main CLI Interface for AI Reasoning Framework.

This provides a command-line interface for all reasoning operations
including CoT, ToT, context management, and tracing.
"""

import argparse
import asyncio
import logging
import sys
import json
from pathlib import Path
from typing import Optional, Dict, Any

# Import framework modules
from chain_of_thought import ChainOfThoughtReasoner, ReasoningStrategy
from tree_of_thought import TreeOfThoughtsExplorer, SearchStrategy, ToTVisualizer
from context_manager import ContextManager
from llm_providers import LLMProviderFactory, LLMProvider
from prompt_templates import PromptTemplateLibrary
from evaluator import ReasoningEvaluator
from tracer import LangSmithTracer, TracingContext
from cost_tracker import CostTracker


logger = logging.getLogger(__name__)


class AIReasoner:
    """Main AI Reasoning CLI application."""

    def __init__(self, config_path: Optional[str] = None):
        """Initialize AI Reasoner with configuration."""
        self.config = self._load_config(config_path)
        self.setup_logging()

        # Initialize components
        self.llm_provider = None
        self.context_manager = None
        self.template_library = PromptTemplateLibrary()
        self.tracer = LangSmithTracer(
            project_name=self.config.get("project_name", "ai-reasoning"),
            api_key=self.config.get("langsmith_api_key"),
            enabled=self.config.get("enable_tracing", False)
        )
        self.cost_tracker = CostTracker(
            budget_limit=self.config.get("budget_limit"),
            warning_threshold=self.config.get("budget_warning_threshold", 0.8)
        )

    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """Load configuration from file or use defaults."""
        if config_path and Path(config_path).exists():
            with open(config_path, 'r') as f:
                import yaml
                return yaml.safe_load(f)

        # Default configuration
        return {
            "llm_provider": "mock",
            "model": "gpt-4",
            "max_tokens": 8000,
            "temperature": 0.7,
            "enable_tracing": False,
            "budget_limit": None,
            "log_level": "INFO"
        }

    def setup_logging(self):
        """Setup logging configuration."""
        log_level = getattr(logging, self.config.get("log_level", "INFO"))
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

    def initialize_llm_provider(self):
        """Initialize LLM provider based on configuration."""
        if self.llm_provider:
            return

        provider_type = LLMProvider[self.config.get("llm_provider", "MOCK").upper()]
        api_key = self.config.get("api_key", "")
        model = self.config.get("model", "gpt-4")

        self.llm_provider = LLMProviderFactory.create(
            provider_type=provider_type,
            api_key=api_key,
            model=model
        )

        logger.info(f"Initialized LLM provider: {provider_type.value}/{model}")

    async def cot_reason(self, args):
        """Execute Chain-of-Thought reasoning."""
        self.initialize_llm_provider()

        strategy = ReasoningStrategy[args.strategy.upper()]
        reasoner = ChainOfThoughtReasoner(
            llm_provider=self.llm_provider,
            max_steps=args.max_steps,
            temperature=args.temperature
        )

        with TracingContext(self.tracer, "CoT Reasoning", tags=["cot"]) as trace_id:
            result = await reasoner.reason(
                question=args.question,
                strategy=strategy,
                context=args.context
            )

            # Track cost
            self.cost_tracker.track_usage(
                operation_id=trace_id,
                model=self.config.get("model", "gpt-4"),
                input_tokens=result.token_count // 2,
                output_tokens=result.token_count // 2
            )

        # Output results
        self._output_cot_result(result, args.output_format)

        if args.evaluate:
            await self._evaluate_result(result, args.ground_truth)

    async def tot_explore(self, args):
        """Execute Tree-of-Thoughts exploration."""
        self.initialize_llm_provider()

        strategy = SearchStrategy[args.strategy.upper()]
        explorer = TreeOfThoughtsExplorer(
            llm_provider=self.llm_provider,
            max_depth=args.max_depth,
            branching_factor=args.branching_factor,
            beam_width=args.beam_width
        )

        with TracingContext(self.tracer, "ToT Exploration", tags=["tot"]) as trace_id:
            result = await explorer.explore(
                question=args.question,
                strategy=strategy,
                context=args.context
            )

            # Track cost
            self.cost_tracker.track_usage(
                operation_id=trace_id,
                model=self.config.get("model", "gpt-4"),
                input_tokens=result.token_count // 2,
                output_tokens=result.token_count // 2
            )

        # Output results
        if args.visualize:
            ToTVisualizer.print_tree(result)
        else:
            self._output_tot_result(result, args.output_format)

    async def manage_context(self, args):
        """Manage conversation context."""
        if not self.context_manager:
            self.context_manager = ContextManager(
                max_tokens=self.config.get("max_tokens", 8000)
            )

        if args.action == "add":
            await self.context_manager.add_entry(
                content=args.content,
                role=args.role,
                tokens=len(args.content.split()) * 1.3  # Estimate
            )
            print("Entry added to context")

        elif args.action == "list":
            entries = await self.context_manager.get_context()
            for entry in entries:
                print(f"[{entry.role}] {entry.content[:100]}...")

        elif args.action == "clear":
            await self.context_manager.clear_context()
            print("Context cleared")

        elif args.action == "stats":
            stats = self.context_manager.get_stats()
            print(json.dumps(stats, indent=2))

        elif args.action == "compress":
            self.initialize_llm_provider()
            result = await self.context_manager.compress_context(self.llm_provider)
            print(f"Compression result: {json.dumps(result, indent=2)}")

    async def test_prompt(self, args):
        """Test prompt templates."""
        template = self.template_library.get(args.template_name, args.version)

        if not template:
            print(f"Template not found: {args.template_name}")
            return

        # Parse variables from args
        variables = {}
        if args.variables:
            for var_def in args.variables:
                key, value = var_def.split("=", 1)
                variables[key] = value

        # Render template
        rendered = template.render(**variables)
        print(f"\n=== Rendered Template: {template.name} ===\n")
        print(rendered)

        if args.execute:
            self.initialize_llm_provider()
            response = await self.llm_provider.generate(
                prompt=rendered,
                temperature=args.temperature,
                max_tokens=args.max_tokens
            )
            print(f"\n=== LLM Response ===\n")
            print(response.text)

    def show_cost_report(self, args):
        """Show cost tracking report."""
        stats = self.cost_tracker.get_statistics()
        print("\n=== Cost Report ===\n")
        print(f"Total Operations: {stats['total_operations']}")
        print(f"Total Tokens: {stats['total_tokens']:,}")
        print(f"Total Cost: ${stats['total_cost']:.4f}")

        if stats['budget_limit']:
            print(f"Budget Limit: ${stats['budget_limit']:.2f}")
            print(f"Utilization: {stats['budget_utilization']:.1%}")

        print("\n=== Model Breakdown ===")
        for model, breakdown in stats['model_breakdown'].items():
            print(f"\n{model}:")
            print(f"  Tokens: {breakdown['total_tokens']:,}")
            print(f"  Cost: ${breakdown['total_cost']:.4f}")

        if args.export:
            self.cost_tracker.export_report(args.export)
            print(f"\nReport exported to: {args.export}")

    def _output_cot_result(self, result, format_type):
        """Output CoT result in specified format."""
        if format_type == "json":
            print(json.dumps(result.to_dict(), indent=2))
        else:
            print(f"\n=== Chain-of-Thought Result ===\n")
            print(f"Question: {result.question}")
            print(f"\nReasoning Steps:")
            for step in result.steps:
                print(f"\nStep {step.step_number}: {step.thought}")
            print(f"\nFinal Answer: {result.final_answer}")
            print(f"Confidence: {result.confidence:.2%}")
            print(f"Tokens: {result.token_count}")
            print(f"Time: {result.execution_time:.2f}s")

    def _output_tot_result(self, result, format_type):
        """Output ToT result in specified format."""
        if format_type == "json":
            print(json.dumps(result.to_dict(), indent=2))
        else:
            print(f"\n=== Tree-of-Thoughts Result ===\n")
            print(f"Question: {result.question}")
            print(f"Total Nodes: {result.total_nodes}")
            print(f"Pruned Nodes: {result.pruned_nodes}")
            print(f"Best Path Score: {result.best_path.total_score:.2f}")
            print(f"\nBest Path:")
            for i, node in enumerate(result.best_path.nodes):
                print(f"  {i}. [{node.score:.2f}] {node.thought[:80]}...")

    async def _evaluate_result(self, result, ground_truth):
        """Evaluate reasoning result."""
        evaluator = ReasoningEvaluator(self.llm_provider)
        evaluations = await evaluator.evaluate_cot(result, ground_truth)

        print("\n=== Evaluation Results ===\n")
        for metric, eval_result in evaluations.items():
            print(f"{metric}: {eval_result.percentage():.1f}%")


def create_parser():
    """Create argument parser."""
    parser = argparse.ArgumentParser(
        description="AI Reasoning & Cognitive Pattern Framework"
    )

    parser.add_argument(
        "--config", "-c",
        help="Path to configuration file"
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # CoT reasoning command
    cot_parser = subparsers.add_parser("cot-reason", help="Chain-of-Thought reasoning")
    cot_parser.add_argument("question", help="Question to reason about")
    cot_parser.add_argument("--strategy", default="zero_shot",
                           choices=["zero_shot", "few_shot", "self_consistency", "reflection"])
    cot_parser.add_argument("--context", help="Additional context")
    cot_parser.add_argument("--max-steps", type=int, default=5)
    cot_parser.add_argument("--temperature", type=float, default=0.7)
    cot_parser.add_argument("--evaluate", action="store_true")
    cot_parser.add_argument("--ground-truth", help="Ground truth for evaluation")
    cot_parser.add_argument("--output-format", choices=["text", "json"], default="text")

    # ToT exploration command
    tot_parser = subparsers.add_parser("tot-explore", help="Tree-of-Thoughts exploration")
    tot_parser.add_argument("question", help="Question to explore")
    tot_parser.add_argument("--strategy", default="best_first",
                           choices=["breadth_first", "depth_first", "best_first", "beam_search"])
    tot_parser.add_argument("--context", help="Additional context")
    tot_parser.add_argument("--max-depth", type=int, default=3)
    tot_parser.add_argument("--branching-factor", type=int, default=3)
    tot_parser.add_argument("--beam-width", type=int, default=2)
    tot_parser.add_argument("--visualize", action="store_true")
    tot_parser.add_argument("--output-format", choices=["text", "json"], default="text")

    # Context management command
    ctx_parser = subparsers.add_parser("context", help="Manage conversation context")
    ctx_parser.add_argument("action", choices=["add", "list", "clear", "stats", "compress"])
    ctx_parser.add_argument("--content", help="Content to add")
    ctx_parser.add_argument("--role", default="user", choices=["user", "assistant", "system"])

    # Prompt testing command
    prompt_parser = subparsers.add_parser("prompt", help="Test prompt templates")
    prompt_parser.add_argument("template_name", help="Template name")
    prompt_parser.add_argument("--version", help="Template version")
    prompt_parser.add_argument("--variables", nargs="*", help="Variables (key=value)")
    prompt_parser.add_argument("--execute", action="store_true")
    prompt_parser.add_argument("--temperature", type=float, default=0.7)
    prompt_parser.add_argument("--max-tokens", type=int, default=500)

    # Cost reporting command
    cost_parser = subparsers.add_parser("cost", help="Show cost report")
    cost_parser.add_argument("--export", help="Export report to file")

    return parser


async def main():
    """Main entry point."""
    parser = create_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    reasoner = AIReasoner(config_path=args.config)

    try:
        if args.command == "cot-reason":
            await reasoner.cot_reason(args)
        elif args.command == "tot-explore":
            await reasoner.tot_explore(args)
        elif args.command == "context":
            await reasoner.manage_context(args)
        elif args.command == "prompt":
            await reasoner.test_prompt(args)
        elif args.command == "cost":
            reasoner.show_cost_report(args)
    except Exception as e:
        logger.error(f"Error executing command: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
