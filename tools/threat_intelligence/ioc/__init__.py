"""
IOC (Indicators of Compromise) Management Module.

This module provides functionality for extracting, validating, enriching,
and managing IOCs from various threat intelligence sources.
"""

from ioc_manager import (
    IOC,
    EnrichedIOC,
    GeoLocation,
    IOCLifecycle,
    IOCManager,
)

__all__ = [
    "IOC",
    "EnrichedIOC",
    "GeoLocation",
    "IOCLifecycle",
    "IOCManager",
]

__version__ = "1.0.0"
