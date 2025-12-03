"""
Container Platform Management

Comprehensive Docker container and registry management solution with security
scanning, optimization, and multi-registry support.

Protocol Coverage:
- P-DOCKER-CLEANUP: Container and image cleanup automation
- P-INFRASTRUCTURE-SETUP: Container-based infrastructure deployment
"""

__version__ = "1.0.0"
__author__ = "DevCrew Team"

from .manager.container_manager import ContainerManager
from .registry.registry_client import RegistryClient
from .optimizer.image_optimizer import ImageOptimizer
from .scanner.security_scanner import SecurityScanner
from .linter.dockerfile_linter import DockerfileLinter
from .builder.build_engine import BuildEngine

__all__ = [
    "ContainerManager",
    "RegistryClient",
    "ImageOptimizer",
    "SecurityScanner",
    "DockerfileLinter",
    "BuildEngine",
]
