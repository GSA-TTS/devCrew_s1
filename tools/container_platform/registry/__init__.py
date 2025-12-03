"""
Registry Module

Multi-registry container image management.
"""

from .registry_client import (
    ImageInfo,
    ImageNotFoundError,
    ImagePromotionStage,
    PushPullProgress,
    RegistryAuthenticationError,
    RegistryClient,
    RegistryConfig,
    RegistryOperationError,
    RegistryType,
)

__all__ = [
    "RegistryClient",
    "RegistryConfig",
    "RegistryType",
    "ImageInfo",
    "ImagePromotionStage",
    "PushPullProgress",
    "RegistryAuthenticationError",
    "RegistryOperationError",
    "ImageNotFoundError",
]
