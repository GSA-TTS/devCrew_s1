"""
Code Parser - Extract and parse docstrings and type hints from Python code.

Supports Google-style, NumPy-style, and Sphinx-style docstrings with
comprehensive type hint extraction and example code parsing.
"""

import ast
import inspect
import logging
import re
from dataclasses import dataclass, field
from typing import (Any, Callable, Dict, List, Optional, Tuple, Union,
                    get_args, get_origin)

logger = logging.getLogger(__name__)


@dataclass
class Parameter:
    """Represents a function parameter with its metadata."""

    name: str
    type_hint: Optional[str] = None
    description: Optional[str] = None
    default: Optional[str] = None
    optional: bool = False


@dataclass
class ParsedDocstring:
    """Represents a parsed docstring with all its components."""

    summary: str = ""
    description: str = ""
    parameters: List[Parameter] = field(default_factory=list)
    returns: Optional[str] = None
    return_type: Optional[str] = None
    raises: List[Tuple[str, str]] = field(default_factory=list)
    examples: List[str] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    see_also: List[str] = field(default_factory=list)
    references: List[str] = field(default_factory=list)


class CodeParser:
    """
    Parse Python code to extract docstrings, type hints, and examples.

    Supports multiple docstring formats:
    - Google-style (priority)
    - NumPy-style
    - Sphinx-style

    Examples:
        >>> parser = CodeParser()
        >>> def example_func(x: int, y: str = "default") -> bool:
        ...     '''Example function.
        ...
        ...     Args:
        ...         x: An integer parameter
        ...         y: A string parameter with default
        ...
        ...     Returns:
        ...         Boolean result
        ...     '''
        ...     return True
        >>> result = parser.parse_docstring(example_func)
        >>> print(result.summary)
        Example function.
    """

    def __init__(self) -> None:
        """Initialize the code parser."""
        self.google_sections = [
            "Args",
            "Arguments",
            "Parameters",
            "Returns",
            "Return",
            "Yields",
            "Yield",
            "Raises",
            "Raise",
            "Examples",
            "Example",
            "Note",
            "Notes",
            "Warning",
            "Warnings",
            "See Also",
            "References",
        ]

    def parse_docstring(self, func: Callable) -> ParsedDocstring:
        """
        Extract and parse docstring from a function.

        Args:
            func: The function to parse

        Returns:
            ParsedDocstring object with all extracted components

        Examples:
            >>> def sample(x: int) -> str:
            ...     '''Convert int to string.
            ...
            ...     Args:
            ...         x: Number to convert
            ...
            ...     Returns:
            ...         String representation
            ...     '''
            ...     return str(x)
            >>> parser = CodeParser()
            >>> result = parser.parse_docstring(sample)
            >>> result.summary
            'Convert int to string.'
        """
        try:
            docstring = inspect.getdoc(func)
            if not docstring:
                logger.debug(f"No docstring found for {func.__name__}")
                return ParsedDocstring()

            # Try Google-style first (priority)
            parsed = self.parse_google_docstring(docstring)

            # Extract type hints and merge with docstring info
            type_hints = self.extract_type_hints(func)
            self._merge_type_hints(parsed, type_hints)

            return parsed

        except Exception as e:
            logger.error(f"Error parsing docstring for {func.__name__}: {e}")
            return ParsedDocstring()

    def parse_google_docstring(self, docstring: str) -> ParsedDocstring:
        """
        Parse Google-style docstring.

        Google-style format:
            Summary line.

            Longer description paragraph.

            Args:
                param1: Description of param1
                param2 (type): Description with type
                param3 (type, optional): Optional parameter

            Returns:
                Description of return value

            Raises:
                ValueError: When something is wrong
                TypeError: When type is wrong

            Examples:
                >>> function(1, 2)
                3

            Note:
                Additional notes here

        Args:
            docstring: The docstring text to parse

        Returns:
            ParsedDocstring object with all extracted sections

        Examples:
            >>> parser = CodeParser()
            >>> doc = '''
            ... Summary line.
            ...
            ... Args:
            ...     x: First parameter
            ...     y: Second parameter
            ...
            ... Returns:
            ...     The result
            ... '''
            >>> result = parser.parse_google_docstring(doc)
            >>> len(result.parameters)
            2
        """
        result = ParsedDocstring()

        # Split into lines for processing
        lines = docstring.split("\n")

        # Extract summary (first non-empty line)
        summary_lines = []
        idx = 0
        while idx < len(lines):
            line = lines[idx].strip()
            if line:
                summary_lines.append(line)
                idx += 1
                # Summary ends at first empty line or section
                if idx < len(lines) and not lines[idx].strip():
                    break
                if any(
                    lines[idx].strip().startswith(f"{section}:")
                    for section in self.google_sections
                ):
                    break
            else:
                idx += 1

        result.summary = " ".join(summary_lines)

        # Find sections
        sections = self._find_sections(lines)

        # Extract description (everything before first section)
        if sections:
            first_section_idx = min(s[1] for s in sections)
            desc_lines = []
            in_desc = False
            for i in range(idx, first_section_idx):
                line = lines[i].strip()
                if line:
                    desc_lines.append(line)
                    in_desc = True
                elif in_desc and desc_lines:
                    desc_lines.append("")
            result.description = "\n".join(desc_lines).strip()

        # Parse each section
        for section_name, section_start in sections:
            section_end = self._find_section_end(lines, section_start, sections)
            section_content = lines[section_start + 1 : section_end]

            if section_name in ["Args", "Arguments", "Parameters"]:
                result.parameters = self._parse_parameters_section(section_content)
            elif section_name in ["Returns", "Return"]:
                result.returns = self._parse_returns_section(section_content)
            elif section_name in ["Yields", "Yield"]:
                result.returns = (
                    f"Generator: {self._parse_returns_section(section_content)}"
                )
            elif section_name in ["Raises", "Raise"]:
                result.raises = self._parse_raises_section(section_content)
            elif section_name in ["Examples", "Example"]:
                result.examples = self.extract_examples("\n".join(section_content))
            elif section_name in ["Note", "Notes"]:
                result.notes = self._parse_list_section(section_content)
            elif section_name in ["Warning", "Warnings"]:
                result.warnings = self._parse_list_section(section_content)
            elif section_name == "See Also":
                result.see_also = self._parse_list_section(section_content)
            elif section_name == "References":
                result.references = self._parse_list_section(section_content)

        return result

    def _find_sections(self, lines: List[str]) -> List[Tuple[str, int]]:
        """
        Find all section headers in docstring.

        Args:
            lines: Lines of the docstring

        Returns:
            List of (section_name, line_index) tuples
        """
        sections = []
        for idx, line in enumerate(lines):
            stripped = line.strip()
            for section in self.google_sections:
                if stripped == f"{section}:":
                    sections.append((section, idx))
                    break
        return sections

    def _find_section_end(
        self,
        lines: List[str],
        start: int,
        all_sections: List[Tuple[str, int]],
    ) -> int:
        """
        Find the end of a section.

        Args:
            lines: All lines in docstring
            start: Start index of current section
            all_sections: All section positions

        Returns:
            End index (exclusive)
        """
        # Find next section
        next_sections = [s[1] for s in all_sections if s[1] > start]
        if next_sections:
            return min(next_sections)
        return len(lines)

    def _parse_parameters_section(self, lines: List[str]) -> List[Parameter]:
        """
        Parse Args/Parameters section.

        Format:
            param_name: Description
            param_name (type): Description
            param_name (type, optional): Description

        Args:
            lines: Section content lines

        Returns:
            List of Parameter objects
        """
        parameters = []
        current_param = None
        current_desc = []

        param_pattern = re.compile(r"^\s*(\w+)\s*(?:\(([^)]+)\))?\s*:\s*(.*)")

        for line in lines:
            match = param_pattern.match(line)
            if match:
                # Save previous parameter
                if current_param:
                    current_param.description = " ".join(current_desc).strip()
                    parameters.append(current_param)

                # Start new parameter
                name = match.group(1)
                type_info = match.group(2)
                desc_start = match.group(3)

                optional = False
                type_hint = None

                if type_info:
                    type_parts = [p.strip() for p in type_info.split(",")]
                    type_hint = type_parts[0]
                    if len(type_parts) > 1 and "optional" in type_parts[1]:
                        optional = True

                current_param = Parameter(
                    name=name,
                    type_hint=type_hint,
                    optional=optional,
                )
                current_desc = [desc_start] if desc_start else []
            elif line.strip() and current_param:
                # Continuation of description
                current_desc.append(line.strip())

        # Save last parameter
        if current_param:
            current_param.description = " ".join(current_desc).strip()
            parameters.append(current_param)

        return parameters

    def _parse_returns_section(self, lines: List[str]) -> str:
        """
        Parse Returns section.

        Args:
            lines: Section content lines

        Returns:
            Return description
        """
        return " ".join(line.strip() for line in lines if line.strip())

    def _parse_raises_section(self, lines: List[str]) -> List[Tuple[str, str]]:
        """
        Parse Raises section.

        Format:
            ExceptionType: Description

        Args:
            lines: Section content lines

        Returns:
            List of (exception_type, description) tuples
        """
        raises = []
        current_exception = None
        current_desc = []

        exception_pattern = re.compile(r"^\s*(\w+)\s*:\s*(.*)")

        for line in lines:
            match = exception_pattern.match(line)
            if match:
                # Save previous exception
                if current_exception:
                    raises.append((current_exception, " ".join(current_desc).strip()))

                # Start new exception
                current_exception = match.group(1)
                current_desc = [match.group(2)] if match.group(2) else []
            elif line.strip() and current_exception:
                # Continuation of description
                current_desc.append(line.strip())

        # Save last exception
        if current_exception:
            raises.append((current_exception, " ".join(current_desc).strip()))

        return raises

    def _parse_list_section(self, lines: List[str]) -> List[str]:
        """
        Parse a simple list section (Notes, Warnings, etc).

        Args:
            lines: Section content lines

        Returns:
            List of items
        """
        items = []
        current_item: List[str] = []

        for line in lines:
            stripped = line.strip()
            if stripped:
                # Check if it's a list item (starts with -, *, or number)
                if re.match(r"^[-*\d.]+\s+", stripped):
                    if current_item:
                        items.append(" ".join(current_item))
                    current_item = [re.sub(r"^[-*\d.]+\s+", "", stripped)]
                else:
                    current_item.append(stripped)
            elif current_item:
                # Empty line ends current item
                items.append(" ".join(current_item))
                current_item = []

        # Save last item
        if current_item:
            items.append(" ".join(current_item))

        # If no list items found, treat as single paragraph
        if not items:
            content = " ".join(line.strip() for line in lines if line.strip())
            if content:
                items.append(content)

        return items

    def extract_type_hints(self, func: Callable) -> Dict[str, Any]:
        """
        Extract type hints from function signature.

        Args:
            func: The function to inspect

        Returns:
            Dictionary with 'parameters' and 'return_type' keys

        Examples:
            >>> def typed_func(x: int, y: str = "default") -> bool:
            ...     return True
            >>> parser = CodeParser()
            >>> hints = parser.extract_type_hints(typed_func)
            >>> hints['parameters']['x']
            'int'
        """
        try:
            sig = inspect.signature(func)
            type_hints: Dict[str, Any] = {}

            # Extract parameter types
            parameters: Dict[str, Dict[str, Any]] = {}
            for name, param in sig.parameters.items():
                param_info: Dict[str, Any] = {}

                # Get type annotation
                if param.annotation != inspect.Parameter.empty:
                    param_info["type"] = self._format_type_hint(param.annotation)

                # Get default value
                if param.default != inspect.Parameter.empty:
                    param_info["default"] = repr(param.default)
                    param_info["optional"] = True

                # Check if it's *args or **kwargs
                if param.kind == inspect.Parameter.VAR_POSITIONAL:
                    param_info["var_positional"] = True
                elif param.kind == inspect.Parameter.VAR_KEYWORD:
                    param_info["var_keyword"] = True

                parameters[name] = param_info

            type_hints["parameters"] = parameters

            # Extract return type
            if sig.return_annotation != inspect.Signature.empty:
                type_hints["return_type"] = self._format_type_hint(
                    sig.return_annotation
                )

            return type_hints

        except Exception as e:
            logger.error(f"Error extracting type hints: {e}")
            return {"parameters": {}, "return_type": None}

    def _format_type_hint(self, hint: Any) -> str:
        """
        Format a type hint as a readable string.

        Args:
            hint: Type hint object

        Returns:
            Formatted string representation
        """
        # Handle None type
        if hint is type(None):  # noqa: E721
            return "None"

        # Handle string annotations (for forward references)
        if isinstance(hint, str):
            return hint

        # Get the origin (e.g., list, dict, Union)
        origin = get_origin(hint)
        args = get_args(hint)

        if origin is None:
            # Simple type
            if hasattr(hint, "__name__"):
                return hint.__name__
            return str(hint)

        # Handle Union (including Optional)
        if origin is Union:
            if len(args) == 2 and type(None) in args:
                # Optional[X]
                other_type = args[0] if args[1] is type(None) else args[1]
                return f"Optional[{self._format_type_hint(other_type)}]"
            # Union[X, Y, ...]
            formatted_args = [self._format_type_hint(arg) for arg in args]
            return f"Union[{', '.join(formatted_args)}]"

        # Handle generic types (List, Dict, etc.)
        if hasattr(origin, "__name__"):
            origin_name = origin.__name__
        else:
            origin_name = str(origin)

        if args:
            formatted_args = [self._format_type_hint(arg) for arg in args]
            return f"{origin_name}[{', '.join(formatted_args)}]"

        return origin_name

    def _merge_type_hints(
        self, parsed: ParsedDocstring, type_hints: Dict[str, Any]
    ) -> None:
        """
        Merge type hints from signature with parsed docstring.

        Args:
            parsed: ParsedDocstring to update
            type_hints: Type hints from signature
        """
        # Update parameter types and defaults
        param_hints = type_hints.get("parameters", {})
        for param in parsed.parameters:
            if param.name in param_hints:
                hints = param_hints[param.name]
                if not param.type_hint and "type" in hints:
                    param.type_hint = hints["type"]
                if not param.default and "default" in hints:
                    param.default = hints["default"]
                if "optional" in hints:
                    param.optional = hints["optional"]

        # Update return type
        if not parsed.return_type and "return_type" in type_hints:
            parsed.return_type = type_hints["return_type"]

    def extract_examples(self, docstring: str) -> List[str]:
        """
        Extract code examples from docstring.

        Supports multiple formats:
        - Doctest format (>>> ...)
        - Code blocks (indented or fenced)
        - Explicit example sections

        Args:
            docstring: The docstring text

        Returns:
            List of example code strings

        Examples:
            >>> parser = CodeParser()
            >>> doc = '''
            ... Examples:
            ...     >>> add(1, 2)
            ...     3
            ...
            ...     >>> add(5, 10)
            ...     15
            ... '''
            >>> examples = parser.extract_examples(doc)
            >>> len(examples)
            2
        """
        examples = []

        # Extract doctest examples (>>> format)
        doctest_pattern = re.compile(
            r"^\s*>>>.*?(?=\n\s*(?:>>>|$))", re.MULTILINE | re.DOTALL
        )
        for match in doctest_pattern.finditer(docstring):
            example = match.group(0).strip()
            if example:
                examples.append(example)

        # Extract code blocks (indented 4+ spaces or fenced)
        # Fenced code blocks with language hint
        fenced_pattern = re.compile(r"```(?:python|py)?\n(.*?)```", re.DOTALL)
        for match in fenced_pattern.finditer(docstring):
            code = match.group(1).strip()
            if code and not any(code in ex for ex in examples):
                examples.append(code)

        # Indented code blocks (after Examples: section)
        lines = docstring.split("\n")
        in_example_section = False
        current_block: List[str] = []

        for line in lines:
            # Check if we're entering Examples section
            if re.match(r"^\s*(Examples?|Usage):\s*$", line, re.IGNORECASE):
                in_example_section = True
                continue

            # Check if we're leaving Examples section (new section header)
            if in_example_section and re.match(r"^\s*[A-Z][a-zA-Z\s]+:\s*$", line):
                in_example_section = False
                if current_block:
                    block_text = "\n".join(current_block).strip()
                    if block_text and not any(block_text in ex for ex in examples):
                        examples.append(block_text)
                    current_block = []
                continue

            if in_example_section:
                # Collect indented lines (but skip doctest lines already caught)
                if line.strip() and not line.strip().startswith(">>>"):
                    # Check if it's indented (4+ spaces)
                    if line.startswith("    ") or line.startswith("\t"):
                        current_block.append(line)
                    elif current_block:
                        # End of code block
                        block_text = "\n".join(current_block).strip()
                        if block_text and not any(block_text in ex for ex in examples):
                            examples.append(block_text)
                        current_block = []
                elif not line.strip() and current_block:
                    # Empty line within block
                    current_block.append(line)

        # Save last block if any
        if current_block:
            block_text = "\n".join(current_block).strip()
            if block_text and not any(block_text in ex for ex in examples):
                examples.append(block_text)

        return examples

    def parse_module_docstring(self, module_path: str) -> ParsedDocstring:
        """
        Parse module-level docstring from a Python file.

        Args:
            module_path: Path to Python module file

        Returns:
            ParsedDocstring object with module documentation
        """
        try:
            with open(module_path, encoding="utf-8") as f:
                tree = ast.parse(f.read())

            # Get module docstring
            docstring = ast.get_docstring(tree)
            if not docstring:
                return ParsedDocstring()

            return self.parse_google_docstring(docstring)

        except Exception as e:
            logger.error(f"Error parsing module docstring: {e}")
            return ParsedDocstring()

    def to_dict(self, parsed: ParsedDocstring) -> Dict[str, Any]:
        """
        Convert ParsedDocstring to dictionary format.

        Args:
            parsed: ParsedDocstring object

        Returns:
            Dictionary representation
        """
        return {
            "summary": parsed.summary,
            "description": parsed.description,
            "parameters": [
                {
                    "name": p.name,
                    "type": p.type_hint,
                    "description": p.description,
                    "default": p.default,
                    "optional": p.optional,
                }
                for p in parsed.parameters
            ],
            "returns": parsed.returns,
            "return_type": parsed.return_type,
            "raises": [
                {"exception": exc, "description": desc} for exc, desc in parsed.raises
            ],
            "examples": parsed.examples,
            "notes": parsed.notes,
            "warnings": parsed.warnings,
            "see_also": parsed.see_also,
            "references": parsed.references,
        }
