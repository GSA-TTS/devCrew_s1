"""
API Testing & Contract Validation Platform

A comprehensive automated testing solution for API contract validation, schema
validation, and consumer-driven contract testing supporting OpenAPI 3.0/3.1.
"""

__version__ = "1.0.0"
__author__ = "DevCrew Team"

from .contract_validator import ContractValidator, ValidationResult
from .test_generator import TestGenerator
from .api_client import APIClient
from .pact_manager import PactManager
from .schema_validator import SchemaValidator
from .regression_engine import RegressionEngine

__all__ = [
    "ContractValidator",
    "ValidationResult",
    "TestGenerator",
    "APIClient",
    "PactManager",
    "SchemaValidator",
    "RegressionEngine",
]
