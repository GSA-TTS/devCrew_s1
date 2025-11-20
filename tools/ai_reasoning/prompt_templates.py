"""
Prompt Template Library.

This module provides templates for CoT, ToT, few-shot learning,
and meta-prompts with versioning support.

Protocol Coverage:
- P-COG-COT: Chain-of-Thought protocol
- P-COG-TOT: Tree-of-Thought protocol
"""

import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from enum import Enum
import json


logger = logging.getLogger(__name__)


class TemplateType(Enum):
    """Prompt template types."""
    CHAIN_OF_THOUGHT = "chain_of_thought"
    TREE_OF_THOUGHT = "tree_of_thought"
    FEW_SHOT = "few_shot"
    META_PROMPT = "meta_prompt"
    REFLECTION = "reflection"
    EVALUATION = "evaluation"


@dataclass
class PromptTemplate:
    """Represents a prompt template."""
    name: str
    type: TemplateType
    version: str
    template: str
    variables: List[str]
    description: str
    examples: List[Dict[str, str]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def render(self, **kwargs) -> str:
        """
        Render template with provided variables.

        Args:
            **kwargs: Variable values

        Returns:
            Rendered prompt
        """
        # Check for missing variables
        missing = [var for var in self.variables if var not in kwargs]
        if missing:
            logger.warning(f"Missing variables: {missing}")

        # Simple variable substitution
        rendered = self.template
        for var, value in kwargs.items():
            placeholder = f"{{{var}}}"
            rendered = rendered.replace(placeholder, str(value))

        return rendered

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "type": self.type.value,
            "version": self.version,
            "template": self.template,
            "variables": self.variables,
            "description": self.description,
            "examples": self.examples,
            "metadata": self.metadata
        }


class PromptTemplateLibrary:
    """Library of prompt templates with versioning."""

    def __init__(self):
        """Initialize template library."""
        self.templates: Dict[str, Dict[str, PromptTemplate]] = {}
        self._load_default_templates()

    def _load_default_templates(self) -> None:
        """Load default templates."""
        # Chain-of-Thought templates
        self.register(PromptTemplate(
            name="cot_zero_shot",
            type=TemplateType.CHAIN_OF_THOUGHT,
            version="1.0",
            template="""Let's think step by step to solve this problem.

{context}

Question: {question}

Step 1:""",
            variables=["question", "context"],
            description="Zero-shot Chain-of-Thought template"
        ))

        self.register(PromptTemplate(
            name="cot_few_shot",
            type=TemplateType.CHAIN_OF_THOUGHT,
            version="1.0",
            template="""Here are some examples of step-by-step reasoning:

{examples}

Now, let's solve this question step by step:

{context}

Question: {question}

Step 1:""",
            variables=["question", "examples", "context"],
            description="Few-shot Chain-of-Thought template with examples",
            examples=[
                {
                    "question": "What is 15 + 27?",
                    "reasoning": "Step 1: Add the ones place: 5 + 7 = 12. Step 2: Write down 2 and carry 1. Step 3: Add tens place: 1 + 2 + 1 = 4. Step 4: Combine: 42",
                    "answer": "42"
                }
            ]
        ))

        # Tree-of-Thought templates
        self.register(PromptTemplate(
            name="tot_branching",
            type=TemplateType.TREE_OF_THOUGHT,
            version="1.0",
            template="""We are solving the following problem:

Question: {question}
{context}

Current thought path (depth {depth}):
{current_path}

Generate {num_branches} different possible next steps or approaches.
Think creatively and explore alternative directions.

Next thought {branch_num}:""",
            variables=["question", "context", "depth", "current_path", "num_branches", "branch_num"],
            description="Tree-of-Thought branching template"
        ))

        self.register(PromptTemplate(
            name="tot_evaluation",
            type=TemplateType.TREE_OF_THOUGHT,
            version="1.0",
            template="""Evaluate the following thought in the context of solving this problem:

Question: {question}
{context}

Thought: {thought}

Rate this thought on a scale of 0.0 to 1.0 based on:
1. Relevance to the question
2. Logical soundness
3. Progress toward solution
4. Clarity and specificity

Provide only the numerical score (e.g., 0.75):""",
            variables=["question", "context", "thought"],
            description="Tree-of-Thought evaluation template"
        ))

        # Reflection templates
        self.register(PromptTemplate(
            name="reflection",
            type=TemplateType.REFLECTION,
            version="1.0",
            template="""Review the following reasoning process and identify any flaws, gaps, or areas for improvement:

Question: {question}

Reasoning Steps:
{steps}

Final Answer: {answer}

Provide a critical reflection on:
1. Logical consistency
2. Completeness of reasoning
3. Potential biases or assumptions
4. Alternative perspectives

Reflection:""",
            variables=["question", "steps", "answer"],
            description="Reflection and self-critique template"
        ))

        # Meta-prompt templates
        self.register(PromptTemplate(
            name="meta_prompt_architect",
            type=TemplateType.META_PROMPT,
            version="1.0",
            template="""You are an expert AI assistant helping with architectural decisions.

Task: {task}
Context: {context}

Your approach should:
1. Break down complex problems into manageable steps
2. Consider multiple perspectives and trade-offs
3. Provide specific, actionable recommendations
4. Reference best practices and patterns

Begin your analysis:""",
            variables=["task", "context"],
            description="Meta-prompt for architectural reasoning"
        ))

        self.register(PromptTemplate(
            name="meta_prompt_security",
            type=TemplateType.META_PROMPT,
            version="1.0",
            template="""You are a cybersecurity expert analyzing potential vulnerabilities.

System Description: {system}
Security Concern: {concern}

Your analysis should:
1. Identify specific vulnerabilities and attack vectors
2. Assess risk levels and potential impact
3. Recommend concrete mitigation strategies
4. Consider compliance and regulatory requirements

Security Analysis:""",
            variables=["system", "concern"],
            description="Meta-prompt for security analysis"
        ))

        # Evaluation templates
        self.register(PromptTemplate(
            name="evaluation_consistency",
            type=TemplateType.EVALUATION,
            version="1.0",
            template="""Compare the following reasoning paths for consistency:

Question: {question}

Path 1: {path1}
Path 2: {path2}

Are these paths logically consistent? Do they reach similar conclusions?
Identify any contradictions or major differences.

Analysis:""",
            variables=["question", "path1", "path2"],
            description="Evaluation template for consistency checking"
        ))

    def register(self, template: PromptTemplate) -> None:
        """
        Register a new template.

        Args:
            template: Template to register
        """
        if template.name not in self.templates:
            self.templates[template.name] = {}

        self.templates[template.name][template.version] = template
        logger.debug(f"Registered template: {template.name} v{template.version}")

    def get(
        self,
        name: str,
        version: Optional[str] = None
    ) -> Optional[PromptTemplate]:
        """
        Get template by name and version.

        Args:
            name: Template name
            version: Template version (latest if not specified)

        Returns:
            PromptTemplate or None
        """
        if name not in self.templates:
            logger.warning(f"Template not found: {name}")
            return None

        versions = self.templates[name]

        if version:
            return versions.get(version)
        else:
            # Return latest version
            latest_version = max(versions.keys())
            return versions[latest_version]

    def list_templates(
        self,
        template_type: Optional[TemplateType] = None
    ) -> List[PromptTemplate]:
        """
        List all templates.

        Args:
            template_type: Filter by type (optional)

        Returns:
            List of templates
        """
        all_templates = []
        for name, versions in self.templates.items():
            for version, template in versions.items():
                if template_type is None or template.type == template_type:
                    all_templates.append(template)

        return all_templates

    def delete(self, name: str, version: Optional[str] = None) -> bool:
        """
        Delete template.

        Args:
            name: Template name
            version: Template version (all versions if not specified)

        Returns:
            True if deleted
        """
        if name not in self.templates:
            return False

        if version:
            if version in self.templates[name]:
                del self.templates[name][version]
                if not self.templates[name]:
                    del self.templates[name]
                return True
        else:
            del self.templates[name]
            return True

        return False

    def export_templates(self, filepath: str) -> None:
        """
        Export templates to JSON file.

        Args:
            filepath: Output file path
        """
        export_data = {}
        for name, versions in self.templates.items():
            export_data[name] = {
                version: template.to_dict()
                for version, template in versions.items()
            }

        with open(filepath, 'w') as f:
            json.dump(export_data, f, indent=2)

        logger.info(f"Exported templates to {filepath}")

    def import_templates(self, filepath: str) -> int:
        """
        Import templates from JSON file.

        Args:
            filepath: Input file path

        Returns:
            Number of templates imported
        """
        with open(filepath, 'r') as f:
            import_data = json.load(f)

        count = 0
        for name, versions in import_data.items():
            for version, template_dict in versions.items():
                template = PromptTemplate(
                    name=template_dict["name"],
                    type=TemplateType(template_dict["type"]),
                    version=template_dict["version"],
                    template=template_dict["template"],
                    variables=template_dict["variables"],
                    description=template_dict["description"],
                    examples=template_dict.get("examples", []),
                    metadata=template_dict.get("metadata", {})
                )
                self.register(template)
                count += 1

        logger.info(f"Imported {count} templates from {filepath}")
        return count


class FewShotExample:
    """Helper for managing few-shot examples."""

    def __init__(self):
        """Initialize few-shot example manager."""
        self.examples: Dict[str, List[Dict[str, str]]] = {
            "math": [
                {
                    "question": "What is 15 + 27?",
                    "reasoning": "Step 1: Add ones place: 5 + 7 = 12. Step 2: Carry 1. Step 3: Add tens: 1 + 2 + 1 = 4. Result: 42",
                    "answer": "42"
                },
                {
                    "question": "What is 8 × 9?",
                    "reasoning": "Step 1: Multiply 8 × 9. Step 2: 8 × 9 = 72",
                    "answer": "72"
                }
            ],
            "architecture": [
                {
                    "question": "Should I use microservices for a small startup?",
                    "reasoning": "Step 1: Assess team size - small team. Step 2: Consider complexity overhead. Step 3: Evaluate deployment complexity. Step 4: Recommend starting with monolith.",
                    "answer": "Start with a monolith for simplicity, consider microservices as you scale."
                },
                {
                    "question": "How to handle authentication in a distributed system?",
                    "reasoning": "Step 1: Consider JWT for stateless auth. Step 2: Centralize auth service. Step 3: Use API gateway. Step 4: Implement token refresh.",
                    "answer": "Use JWT tokens with a centralized authentication service and API gateway."
                }
            ],
            "security": [
                {
                    "question": "How to prevent SQL injection?",
                    "reasoning": "Step 1: Use parameterized queries. Step 2: Validate input. Step 3: Use ORM. Step 4: Apply least privilege.",
                    "answer": "Use parameterized queries and input validation consistently."
                }
            ]
        }

    def get_examples(
        self,
        category: str,
        limit: Optional[int] = None
    ) -> List[Dict[str, str]]:
        """
        Get examples for category.

        Args:
            category: Example category
            limit: Maximum examples to return

        Returns:
            List of examples
        """
        examples = self.examples.get(category, [])
        if limit:
            examples = examples[:limit]
        return examples

    def add_example(
        self,
        category: str,
        question: str,
        reasoning: str,
        answer: str
    ) -> None:
        """
        Add new example.

        Args:
            category: Example category
            question: Example question
            reasoning: Reasoning process
            answer: Final answer
        """
        if category not in self.examples:
            self.examples[category] = []

        self.examples[category].append({
            "question": question,
            "reasoning": reasoning,
            "answer": answer
        })

    def format_examples(self, examples: List[Dict[str, str]]) -> str:
        """
        Format examples for prompt.

        Args:
            examples: List of example dicts

        Returns:
            Formatted string
        """
        formatted = []
        for i, example in enumerate(examples, 1):
            formatted.append(f"Example {i}:")
            formatted.append(f"Question: {example['question']}")
            formatted.append(f"Reasoning: {example['reasoning']}")
            formatted.append(f"Answer: {example['answer']}")
            formatted.append("")

        return "\n".join(formatted)


# Example usage
if __name__ == "__main__":
    # Initialize library
    library = PromptTemplateLibrary()

    # Get template
    cot_template = library.get("cot_zero_shot")
    if cot_template:
        # Render template
        prompt = cot_template.render(
            question="What is the best database for a social media application?",
            context="Context: High read/write ratio, needs scalability"
        )
        print("Rendered prompt:")
        print(prompt)

    # List all templates
    print("\n\nAvailable templates:")
    for template in library.list_templates():
        print(f"- {template.name} v{template.version} ({template.type.value})")

    # Few-shot examples
    few_shot_manager = FewShotExample()
    examples = few_shot_manager.get_examples("architecture", limit=2)
    formatted = few_shot_manager.format_examples(examples)
    print(f"\n\nFormatted examples:\n{formatted}")
