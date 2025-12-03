"""
API Documentation Generator

Automated documentation platform for generating comprehensive API documentation
from source code and OpenAPI specifications.
"""

__version__ = "1.0.0"
__author__ = "DevCrew Team"

from .spec_generator import SpecGenerator
from .doc_renderer import DocRenderer
from .code_parser import CodeParser
from .example_generator import ExampleGenerator

__all__ = [
    "SpecGenerator",
    "DocRenderer",
    "CodeParser",
    "ExampleGenerator",
]
