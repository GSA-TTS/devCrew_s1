"""
Design Tools & UI/UX Integration Platform.

Multi-functional design platform enabling programmatic access to Figma API,
automated design validation against WCAG 2.1 accessibility standards, design
system management, design-to-code export, and C4 architecture visualization.

Core Components:
    - Figma Client: HTTP wrapper for Figma REST API
    - Design Validator: WCAG 2.1 and design system validation
    - Code Exporter: Design-to-code export (CSS, React, design tokens)
    - C4 Generator: Architecture diagram generation from DSL
    - CLI Interface: Command-line design operations tool

Protocols Supported:
    - P-C4-VISUALIZATION: C4 architecture diagram generation
    - P-FRONTEND-DEV: Design-to-code export for frontend development
    - P-DESIGN-REVIEW: Automated design validation
    - QG-FRONTEND: Frontend quality gates for accessibility and design system

Features:
    - Programmatic Figma API access (files, components, exports)
    - WCAG 2.1 AA/AAA accessibility validation
    - Color contrast checking (4.5:1, 7:1 ratios)
    - Touch target size validation (44x44px minimum)
    - Design system compliance enforcement
    - CSS/React component generation
    - Design token extraction
    - C4 diagram generation (System Context, Container, Component)
    - CLI for all design operations
"""

__version__ = "1.0.0"
__author__ = "devCrew_s1"

from .figma_client import FigmaClient, FigmaFile, FigmaNode, FigmaExport
from .design_validator import (
    DesignValidator,
    ValidationResult,
    WCAGLevel,
    ContrastRatio,
)
from .code_exporter import (
    CodeExporter,
    CSSGenerator,
    ReactGenerator,
    DesignTokens,
)
from .c4_generator import C4Generator, C4Workspace, C4Diagram, DiagramType

__all__ = [
    # Figma Client
    "FigmaClient",
    "FigmaFile",
    "FigmaNode",
    "FigmaExport",
    # Design Validator
    "DesignValidator",
    "ValidationResult",
    "WCAGLevel",
    "ContrastRatio",
    # Code Exporter
    "CodeExporter",
    "CSSGenerator",
    "ReactGenerator",
    "DesignTokens",
    # C4 Generator
    "C4Generator",
    "C4Workspace",
    "C4Diagram",
    "DiagramType",
]
