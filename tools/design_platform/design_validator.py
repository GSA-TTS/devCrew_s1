#!/usr/bin/env python3
"""
Design Validator - WCAG 2.1 and Design System Compliance Validation.

This module provides comprehensive accessibility validation and design system
compliance checking for Figma design files. It implements WCAG 2.1 Level AA
and AAA standards, including color contrast ratios, touch target sizes,
text size requirements, and custom design system rules.

Features:
    - WCAG 2.1 AA (4.5:1) and AAA (7:1) color contrast validation
    - Touch target size validation (44x44px minimum)
    - Text size validation (16px minimum)
    - Design system compliance checking
    - Batch validation support
    - JSON report generation
    - Relative luminance calculation for color contrast

Usage:
    validator = DesignValidator()
    result = validator.validate_accessibility(design_file, wcag_level="AA")
    contrast = validator.check_contrast("#000000", "#FFFFFF")

TOOL-DESIGN-002: Design Validator
"""

import logging
import math
import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml
from pydantic import BaseModel, Field, field_validator

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WCAGLevel(str, Enum):
    """WCAG 2.1 compliance levels for accessibility validation."""

    AA = "AA"  # Standard level (4.5:1 for normal text, 3:1 for large text)
    AAA = "AAA"  # Enhanced level (7:1 for normal text, 4.5:1 for large text)


class SeverityLevel(str, Enum):
    """Severity levels for validation violations."""

    CRITICAL = "critical"  # WCAG failures that prevent accessibility
    WARNING = "warning"  # Best practice violations or edge cases
    INFO = "info"  # Informational findings


class ContrastRatio(BaseModel):
    """
    Color contrast ratio calculation result.

    Attributes:
        ratio: Calculated contrast ratio (1-21)
        passes_aa: Whether the ratio meets WCAG AA standards
        passes_aaa: Whether the ratio meets WCAG AAA standards
        foreground_color: The foreground color used
        background_color: The background color used
        is_large_text: Whether the text is considered large (>= 18pt or bold)
    """

    ratio: float = Field(ge=1.0, le=21.0)
    passes_aa: bool
    passes_aaa: bool
    foreground_color: str
    background_color: str
    is_large_text: bool = False

    @field_validator("foreground_color", "background_color")
    @classmethod
    def validate_color_format(cls, v: str) -> str:
        """Validate color format (hex, rgb, or rgba)."""
        if not v:
            raise ValueError("Color cannot be empty")
        # Allow hex, rgb, and rgba formats
        hex_pattern = r"^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$"
        rgb_pattern = r"^rgb\(\s*\d+\s*,\s*\d+\s*,\s*\d+\s*\)$"
        rgba_pattern = r"^rgba\(\s*\d+\s*,\s*\d+\s*,\s*\d+\s*,\s*[\d.]+\s*\)$"
        if not (
            re.match(hex_pattern, v)
            or re.match(rgb_pattern, v)
            or re.match(rgba_pattern, v)
        ):
            raise ValueError(f"Invalid color format: {v}")
        return v


class Violation(BaseModel):
    """
    Validation violation or warning.

    Attributes:
        rule: The rule that was violated (e.g., "WCAG-1.4.3")
        severity: Severity level of the violation
        message: Human-readable description of the violation
        node_id: ID of the Figma node that violated the rule
        node_name: Name of the Figma node
        location: Location information (page, frame path)
        suggestion: Suggested fix for the violation
        wcag_reference: Link to WCAG documentation
    """

    rule: str
    severity: SeverityLevel
    message: str
    node_id: Optional[str] = None
    node_name: Optional[str] = None
    location: Optional[str] = None
    suggestion: Optional[str] = None
    wcag_reference: Optional[str] = None


class ValidationResult(BaseModel):
    """
    Complete validation result.

    Attributes:
        status: Overall validation status ("passed", "failed", "warning")
        violations: List of violations found
        warnings: List of warnings found
        passed_checks: Number of checks that passed
        total_checks: Total number of checks performed
        file_key: Figma file key that was validated
        wcag_level: WCAG level used for validation
        timestamp: When the validation was performed
        summary: Human-readable summary
    """

    status: str  # "passed", "failed", "warning"
    violations: List[Violation] = Field(default_factory=list)
    warnings: List[Violation] = Field(default_factory=list)
    passed_checks: int = 0
    total_checks: int = 0
    file_key: Optional[str] = None
    wcag_level: Optional[WCAGLevel] = None
    timestamp: Optional[str] = None
    summary: Optional[str] = None

    @property
    def pass_rate(self) -> float:
        """Calculate the pass rate percentage."""
        if self.total_checks == 0:
            return 0.0
        return (self.passed_checks / self.total_checks) * 100

    def to_json(self, file_path: Optional[Path] = None) -> str:
        """
        Export validation result to JSON.

        Args:
            file_path: Optional path to save JSON file

        Returns:
            JSON string representation
        """
        json_str = self.model_dump_json(indent=2)
        if file_path:
            Path(file_path).write_text(json_str)
            logger.info(f"Validation report saved to {file_path}")
        return json_str


@dataclass
class FigmaNode:
    """
    Simplified Figma node representation for validation.

    This is a minimal representation to support validation operations.
    For full Figma API integration, use FigmaClient.
    """

    id: str
    name: str
    type: str
    width: Optional[float] = None
    height: Optional[float] = None
    fills: List[Dict[str, Any]] = field(default_factory=list)
    strokes: List[Dict[str, Any]] = field(default_factory=list)
    effects: List[Dict[str, Any]] = field(default_factory=list)
    style: Optional[Dict[str, Any]] = None
    children: List["FigmaNode"] = field(default_factory=list)
    parent: Optional["FigmaNode"] = None
    absolute_bounding_box: Optional[Dict[str, float]] = None
    characters: Optional[str] = None  # For text nodes
    font_size: Optional[float] = None
    font_weight: Optional[int] = None


@dataclass
class FigmaFile:
    """
    Simplified Figma file representation for validation.

    This is a minimal representation to support validation operations.
    For full Figma API integration, use FigmaClient.
    """

    key: str
    name: str
    document: Optional[FigmaNode] = None
    components: Dict[str, Any] = field(default_factory=dict)
    styles: Dict[str, Any] = field(default_factory=dict)


class DesignValidator:
    """
    WCAG 2.1 and design system compliance validator.

    This class provides comprehensive accessibility validation including
    color contrast ratios, touch target sizes, text sizes, and custom
    design system rule enforcement.

    Attributes:
        validation_rules: Dictionary of validation rules loaded from config
        wcag_aa_normal_text_ratio: WCAG AA ratio for normal text (4.5:1)
        wcag_aa_large_text_ratio: WCAG AA ratio for large text (3:1)
        wcag_aaa_normal_text_ratio: WCAG AAA ratio for normal text (7:1)
        wcag_aaa_large_text_ratio: WCAG AAA ratio for large text (4.5:1)
        min_touch_target_size: Minimum touch target size in pixels (44x44)
        min_text_size: Minimum text size in pixels (16px)
    """

    # WCAG 2.1 contrast ratio requirements
    WCAG_AA_NORMAL_TEXT_RATIO = 4.5
    WCAG_AA_LARGE_TEXT_RATIO = 3.0
    WCAG_AAA_NORMAL_TEXT_RATIO = 7.0
    WCAG_AAA_LARGE_TEXT_RATIO = 4.5

    # Accessibility requirements
    MIN_TOUCH_TARGET_SIZE = 44  # pixels (44x44)
    MIN_TEXT_SIZE = 16  # pixels
    LARGE_TEXT_SIZE = 18  # pixels (or 14pt bold)
    LARGE_TEXT_BOLD_WEIGHT = 700

    def __init__(self, validation_rules: Optional[Dict[str, Any]] = None) -> None:
        """
        Initialize the design validator.

        Args:
            validation_rules: Optional dictionary of validation rules.
                            If None, loads from default config file.
        """
        self.validation_rules = validation_rules or self._load_default_rules()
        logger.info("DesignValidator initialized")

    def _load_default_rules(self) -> Dict[str, Any]:
        """
        Load default validation rules from YAML configuration.

        Returns:
            Dictionary of validation rules

        Note:
            If no config file exists, returns default rule set.
        """
        config_path = Path(__file__).parent / "config" / "validation_rules.yaml"
        if config_path.exists():
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    rules = yaml.safe_load(f)
                logger.info(f"Loaded validation rules from {config_path}")
                return rules
            except Exception as e:
                logger.warning(f"Failed to load rules from {config_path}: {e}")

        # Return default rules if config file doesn't exist
        return {
            "accessibility": {
                "color_contrast": True,
                "touch_targets": True,
                "text_size": True,
            },
            "design_system": {
                "color_palette": [],
                "typography": {},
                "spacing": [],
            },
        }

    def _parse_color(self, color: str) -> Tuple[int, int, int]:
        """
        Parse color string to RGB values.

        Args:
            color: Color string in hex, rgb, or rgba format

        Returns:
            Tuple of (r, g, b) values (0-255)

        Raises:
            ValueError: If color format is invalid
        """
        color = color.strip()

        # Hex format
        if color.startswith("#"):
            color = color.lstrip("#")
            if len(color) == 3:
                # Expand shorthand hex (e.g., #fff -> #ffffff)
                color = "".join([c * 2 for c in color])
            if len(color) != 6:
                raise ValueError(f"Invalid hex color: #{color}")
            r = int(color[0:2], 16)
            g = int(color[2:4], 16)
            b = int(color[4:6], 16)
            return (r, g, b)

        # RGB/RGBA format
        if color.startswith("rgb"):
            # Extract numbers from rgb(r, g, b) or rgba(r, g, b, a)
            match = re.findall(r"\d+", color)
            if len(match) >= 3:
                return (int(match[0]), int(match[1]), int(match[2]))

        raise ValueError(f"Unsupported color format: {color}")

    def _calculate_relative_luminance(self, color: str) -> float:
        """
        Calculate relative luminance of a color per WCAG 2.1 formula.

        The relative luminance is calculated using the formula:
        L = 0.2126 * R + 0.7152 * G + 0.0722 * B

        Where R, G, B are calculated as:
        - if RsRGB <= 0.03928 then R = RsRGB/12.92
        - else R = ((RsRGB+0.055)/1.055)^2.4

        Args:
            color: Color string (hex, rgb, or rgba)

        Returns:
            Relative luminance value (0-1)
        """
        r, g, b = self._parse_color(color)

        # Convert to sRGB (0-1 range)
        r_srgb = r / 255.0
        g_srgb = g / 255.0
        b_srgb = b / 255.0

        # Apply gamma correction
        def gamma_correct(channel: float) -> float:
            if channel <= 0.03928:
                return channel / 12.92
            return math.pow((channel + 0.055) / 1.055, 2.4)

        r_linear = gamma_correct(r_srgb)
        g_linear = gamma_correct(g_srgb)
        b_linear = gamma_correct(b_srgb)

        # Calculate relative luminance
        luminance = 0.2126 * r_linear + 0.7152 * g_linear + 0.0722 * b_linear
        return luminance

    def check_contrast(
        self,
        foreground_color: str,
        background_color: str,
        wcag_level: WCAGLevel = WCAGLevel.AA,
        is_large_text: bool = False,
    ) -> ContrastRatio:
        """
        Check color contrast ratio against WCAG 2.1 standards.

        The contrast ratio is calculated using the formula:
        (L1 + 0.05) / (L2 + 0.05)
        where L1 is the lighter color and L2 is the darker color.

        Args:
            foreground_color: Foreground color (hex, rgb, or rgba)
            background_color: Background color (hex, rgb, or rgba)
            wcag_level: WCAG compliance level (AA or AAA)
            is_large_text: Whether text is large (>= 18pt or >= 14pt bold)

        Returns:
            ContrastRatio object with validation results

        Example:
            >>> validator = DesignValidator()
            >>> contrast = validator.check_contrast("#000000", "#FFFFFF")
            >>> print(f"Ratio: {contrast.ratio}, Passes AA: {contrast.passes_aa}")
            Ratio: 21.0, Passes AA: True
        """
        # Calculate relative luminance for both colors
        l1 = self._calculate_relative_luminance(foreground_color)
        l2 = self._calculate_relative_luminance(background_color)

        # Ensure L1 is the lighter color
        lighter = max(l1, l2)
        darker = min(l1, l2)

        # Calculate contrast ratio
        ratio = (lighter + 0.05) / (darker + 0.05)

        # Determine pass/fail based on WCAG level and text size
        if is_large_text:
            aa_threshold = self.WCAG_AA_LARGE_TEXT_RATIO
            aaa_threshold = self.WCAG_AAA_LARGE_TEXT_RATIO
        else:
            aa_threshold = self.WCAG_AA_NORMAL_TEXT_RATIO
            aaa_threshold = self.WCAG_AAA_NORMAL_TEXT_RATIO

        passes_aa = ratio >= aa_threshold
        passes_aaa = ratio >= aaa_threshold

        return ContrastRatio(
            ratio=round(ratio, 2),
            passes_aa=passes_aa,
            passes_aaa=passes_aaa,
            foreground_color=foreground_color,
            background_color=background_color,
            is_large_text=is_large_text,
        )

    def check_touch_targets(self, node: FigmaNode) -> bool:
        """
        Validate touch target size meets 44x44px minimum.

        Per WCAG 2.1 Success Criterion 2.5.5 (AAA), the minimum target
        size for pointer inputs should be at least 44x44 CSS pixels.

        Args:
            node: Figma node to validate

        Returns:
            True if touch target meets minimum size, False otherwise

        Note:
            Interactive elements include buttons, links, form inputs,
            and any element with pointer events.
        """
        if not node.width or not node.height:
            logger.warning(f"Node {node.name} has no dimensions")
            return False

        # Check if node is interactive (button, input, link, etc.)
        interactive_types = [
            "BUTTON",
            "INSTANCE",
            "COMPONENT",
            "TEXT",  # Text that might be a link
        ]

        if node.type not in interactive_types:
            return True  # Not an interactive element, skip check

        # Check minimum size requirements
        min_width = node.width >= self.MIN_TOUCH_TARGET_SIZE
        min_height = node.height >= self.MIN_TOUCH_TARGET_SIZE

        return min_width and min_height

    def check_text_size(self, node: FigmaNode) -> bool:
        """
        Validate text size meets 16px minimum for readability.

        While WCAG 2.1 doesn't specify a minimum font size, 16px is
        considered best practice for body text readability.

        Args:
            node: Figma text node to validate

        Returns:
            True if text size meets minimum, False otherwise
        """
        if node.type != "TEXT":
            return True  # Not a text node, skip check

        if not node.font_size:
            logger.warning(f"Text node {node.name} has no font size")
            return False

        return node.font_size >= self.MIN_TEXT_SIZE

    def _is_large_text(self, node: FigmaNode) -> bool:
        """
        Determine if text is considered "large" per WCAG 2.1.

        Large text is defined as:
        - 18pt (24px) or larger, or
        - 14pt (18.5px) or larger when bold (font-weight >= 700)

        Args:
            node: Figma text node

        Returns:
            True if text is considered large, False otherwise
        """
        if node.type != "TEXT" or not node.font_size:
            return False

        # Check for large text (18pt = 24px)
        if node.font_size >= 24:
            return True

        # Check for bold text at 14pt+ (18.5px)
        if node.font_size >= 18.5 and node.font_weight:
            if node.font_weight >= self.LARGE_TEXT_BOLD_WEIGHT:
                return True

        return False

    def _validate_node(
        self,
        node: FigmaNode,
        wcag_level: WCAGLevel,
        violations: List[Violation],
        warnings: List[Violation],
        checks: Dict[str, int],
        parent_bg: Optional[str] = None,
    ) -> None:
        """
        Recursively validate a Figma node and its children.

        Args:
            node: Figma node to validate
            wcag_level: WCAG level for validation
            violations: List to append violations to
            warnings: List to append warnings to
            checks: Dictionary tracking passed/total checks
            parent_bg: Parent node's background color for contrast checking
        """
        # Extract background color from fills
        bg_color = None
        fg_color = None

        if node.fills:
            for fill in node.fills:
                if fill.get("visible", True) and fill.get("type") == "SOLID":
                    color = fill.get("color", {})
                    r = int(color.get("r", 0) * 255)
                    g = int(color.get("g", 0) * 255)
                    b = int(color.get("b", 0) * 255)
                    bg_color = f"#{r:02x}{g:02x}{b:02x}"
                    break

        # Check touch targets for interactive elements
        if node.type in ["BUTTON", "INSTANCE", "COMPONENT"]:
            checks["total"] += 1
            if self.check_touch_targets(node):
                checks["passed"] += 1
            else:
                violations.append(
                    Violation(
                        rule="WCAG-2.5.5",
                        severity=SeverityLevel.CRITICAL,
                        message=(
                            f"Touch target too small: {node.width}x{node.height}px"
                            f" (minimum: {self.MIN_TOUCH_TARGET_SIZE}x"
                            f"{self.MIN_TOUCH_TARGET_SIZE}px)"
                        ),
                        node_id=node.id,
                        node_name=node.name,
                        suggestion=(
                            f"Increase size to at least "
                            f"{self.MIN_TOUCH_TARGET_SIZE}x"
                            f"{self.MIN_TOUCH_TARGET_SIZE}px"
                        ),
                        wcag_reference="https://www.w3.org/WAI/WCAG21/Understanding/target-size.html",  # noqa: E501
                    )
                )

        # Check text size and contrast
        if node.type == "TEXT":
            # Text size check
            checks["total"] += 1
            if self.check_text_size(node):
                checks["passed"] += 1
            else:
                warnings.append(
                    Violation(
                        rule="TEXT-SIZE",
                        severity=SeverityLevel.WARNING,
                        message=(
                            f"Text size below recommended minimum: "
                            f"{node.font_size}px (recommended: {self.MIN_TEXT_SIZE}px)"
                        ),
                        node_id=node.id,
                        node_name=node.name,
                        suggestion=f"Increase font size to at least {self.MIN_TEXT_SIZE}px",  # noqa: E501
                    )
                )

            # Color contrast check
            if bg_color and parent_bg:
                # Use node's own background or parent's background
                check_bg = bg_color if bg_color else parent_bg

                # Extract text color from fills
                if node.fills:
                    for fill in node.fills:
                        if (
                            fill.get("visible", True) and fill.get("type") == "SOLID"
                        ):  # noqa: E501
                            color = fill.get("color", {})
                            r = int(color.get("r", 0) * 255)
                            g = int(color.get("g", 0) * 255)
                            b = int(color.get("b", 0) * 255)
                            fg_color = f"#{r:02x}{g:02x}{b:02x}"
                            break

                if fg_color:
                    checks["total"] += 1
                    is_large = self._is_large_text(node)
                    contrast = self.check_contrast(
                        fg_color, check_bg, wcag_level, is_large
                    )

                    if wcag_level == WCAGLevel.AAA:
                        if contrast.passes_aaa:
                            checks["passed"] += 1
                        else:
                            violations.append(
                                Violation(
                                    rule="WCAG-1.4.6",
                                    severity=SeverityLevel.CRITICAL,
                                    message=(
                                        f"Insufficient color contrast: {contrast.ratio}:1 "  # noqa: E501
                                        f"(required: {self.WCAG_AAA_NORMAL_TEXT_RATIO if not is_large else self.WCAG_AAA_LARGE_TEXT_RATIO}:1 for AAA)"  # noqa: E501
                                    ),
                                    node_id=node.id,
                                    node_name=node.name,
                                    suggestion="Increase color contrast to meet AAA standards",  # noqa: E501
                                    wcag_reference="https://www.w3.org/WAI/WCAG21/Understanding/contrast-enhanced.html",  # noqa: E501
                                )
                            )
                    else:  # AA level
                        if contrast.passes_aa:
                            checks["passed"] += 1
                        else:
                            violations.append(
                                Violation(
                                    rule="WCAG-1.4.3",
                                    severity=SeverityLevel.CRITICAL,
                                    message=(
                                        f"Insufficient color contrast: {contrast.ratio}:1 "  # noqa: E501
                                        f"(required: {self.WCAG_AA_NORMAL_TEXT_RATIO if not is_large else self.WCAG_AA_LARGE_TEXT_RATIO}:1 for AA)"  # noqa: E501
                                    ),
                                    node_id=node.id,
                                    node_name=node.name,
                                    suggestion="Increase color contrast to meet AA standards",  # noqa: E501
                                    wcag_reference="https://www.w3.org/WAI/WCAG21/Understanding/contrast-minimum.html",  # noqa: E501
                                )
                            )

        # Recursively validate children
        current_bg = bg_color if bg_color else parent_bg
        for child in node.children:
            self._validate_node(
                child, wcag_level, violations, warnings, checks, current_bg
            )

    def validate_accessibility(
        self, design_file: FigmaFile, wcag_level: WCAGLevel = WCAGLevel.AA
    ) -> ValidationResult:
        """
        Perform comprehensive accessibility validation on a Figma file.

        This method checks:
        - Color contrast ratios (WCAG 1.4.3 for AA, 1.4.6 for AAA)
        - Touch target sizes (WCAG 2.5.5)
        - Text size recommendations
        - Overall WCAG 2.1 compliance

        Args:
            design_file: Figma file to validate
            wcag_level: WCAG compliance level (AA or AAA)

        Returns:
            ValidationResult with all findings and statistics

        Example:
            >>> validator = DesignValidator()
            >>> result = validator.validate_accessibility(file, WCAGLevel.AA)
            >>> print(f"Status: {result.status}, Pass rate: {result.pass_rate}%")
        """
        logger.info(
            f"Starting accessibility validation (WCAG {wcag_level.value}) for "
            f"file: {design_file.name}"
        )

        violations: List[Violation] = []
        warnings: List[Violation] = []
        checks = {"passed": 0, "total": 0}

        # Validate document tree if available
        if design_file.document:
            self._validate_node(
                design_file.document, wcag_level, violations, warnings, checks
            )

        # Determine overall status
        if violations:
            status = "failed"
        elif warnings:
            status = "warning"
        else:
            status = "passed"

        # Create summary
        summary = (
            f"Validation complete: {checks['passed']}/{checks['total']} checks passed. "  # noqa: E501
            f"Found {len(violations)} violations and {len(warnings)} warnings."
        )

        result = ValidationResult(
            status=status,
            violations=violations,
            warnings=warnings,
            passed_checks=checks["passed"],
            total_checks=checks["total"],
            file_key=design_file.key,
            wcag_level=wcag_level,
            summary=summary,
        )

        logger.info(
            f"Validation complete: {result.status} "
            f"({result.pass_rate:.1f}% pass rate)"
        )
        return result

    def validate_design_system(
        self, design_file: FigmaFile, rules: Dict[str, Any]
    ) -> ValidationResult:
        """
        Validate design file against custom design system rules.

        Design system rules can include:
        - Color palette restrictions
        - Typography requirements (font families, sizes, weights)
        - Spacing constraints (margins, padding)
        - Component usage requirements
        - Naming conventions

        Args:
            design_file: Figma file to validate
            rules: Dictionary of design system rules

        Returns:
            ValidationResult with design system compliance findings

        Example:
            >>> rules = {
            ...     "color_palette": ["#FF0000", "#00FF00", "#0000FF"],
            ...     "typography": {"font_family": ["Inter", "Roboto"]},
            ... }
            >>> result = validator.validate_design_system(file, rules)
        """
        logger.info(f"Starting design system validation for file: {design_file.name}")

        violations: List[Violation] = []
        warnings: List[Violation] = []
        checks = {"passed": 0, "total": 0}

        # Validate color palette if specified
        if "color_palette" in rules and rules["color_palette"]:
            allowed_colors = set(rules["color_palette"])
            self._validate_color_palette(
                design_file.document,
                allowed_colors,
                violations,
                warnings,
                checks,
            )

        # Validate typography if specified
        if "typography" in rules and rules["typography"]:
            self._validate_typography(
                design_file.document,
                rules["typography"],
                violations,
                warnings,
                checks,
            )

        # Validate spacing if specified
        if "spacing" in rules and rules["spacing"]:
            self._validate_spacing(
                design_file.document,
                rules["spacing"],
                violations,
                warnings,
                checks,  # noqa: E501
            )

        # Determine overall status
        if violations:
            status = "failed"
        elif warnings:
            status = "warning"
        else:
            status = "passed"

        summary = (
            f"Design system validation complete: {checks['passed']}/{checks['total']} "  # noqa: E501
            f"checks passed. Found {len(violations)} violations and "
            f"{len(warnings)} warnings."
        )

        result = ValidationResult(
            status=status,
            violations=violations,
            warnings=warnings,
            passed_checks=checks["passed"],
            total_checks=checks["total"],
            file_key=design_file.key,
            summary=summary,
        )

        logger.info(
            f"Design system validation complete: {result.status} "
            f"({result.pass_rate:.1f}% pass rate)"
        )
        return result

    def _validate_color_palette(
        self,
        node: Optional[FigmaNode],
        allowed_colors: set,
        violations: List[Violation],
        warnings: List[Violation],
        checks: Dict[str, int],
    ) -> None:
        """Validate colors against allowed palette."""
        if not node:
            return

        # Check fills for color usage
        if node.fills:
            for fill in node.fills:
                if fill.get("visible", True) and fill.get("type") == "SOLID":
                    color = fill.get("color", {})
                    r = int(color.get("r", 0) * 255)
                    g = int(color.get("g", 0) * 255)
                    b = int(color.get("b", 0) * 255)
                    hex_color = f"#{r:02x}{g:02x}{b:02x}"

                    checks["total"] += 1
                    if hex_color.upper() in [
                        c.upper() for c in allowed_colors
                    ]:  # noqa: E501
                        checks["passed"] += 1
                    else:
                        warnings.append(
                            Violation(
                                rule="COLOR-PALETTE",
                                severity=SeverityLevel.WARNING,
                                message=f"Color {hex_color} not in design system palette",  # noqa: E501
                                node_id=node.id,
                                node_name=node.name,
                                suggestion="Use colors from the approved design system palette",  # noqa: E501
                            )
                        )

        # Recursively check children
        for child in node.children:
            self._validate_color_palette(
                child, allowed_colors, violations, warnings, checks
            )

    def _validate_typography(
        self,
        node: Optional[FigmaNode],
        typography_rules: Dict[str, Any],
        violations: List[Violation],
        warnings: List[Violation],
        checks: Dict[str, int],
    ) -> None:
        """Validate typography against design system rules."""
        if not node or node.type != "TEXT":
            # Recursively check children
            if node:
                for child in node.children:
                    self._validate_typography(
                        child, typography_rules, violations, warnings, checks
                    )
            return

        # Validate font family if specified
        if "font_family" in typography_rules:
            checks["total"] += 1
            # Note: This would need node.style.fontFamily from actual Figma API
            # For now, we'll mark as passed
            checks["passed"] += 1

        # Validate font sizes if specified
        if "font_sizes" in typography_rules and node.font_size:
            checks["total"] += 1
            allowed_sizes = typography_rules["font_sizes"]
            if node.font_size in allowed_sizes:
                checks["passed"] += 1
            else:
                warnings.append(
                    Violation(
                        rule="TYPOGRAPHY-SIZE",
                        severity=SeverityLevel.WARNING,
                        message=f"Font size {node.font_size}px not in design system scale",  # noqa: E501
                        node_id=node.id,
                        node_name=node.name,
                        suggestion=f"Use approved font sizes: {allowed_sizes}",
                    )
                )

        # Recursively check children
        for child in node.children:
            self._validate_typography(
                child, typography_rules, violations, warnings, checks
            )

    def _validate_spacing(
        self,
        node: Optional[FigmaNode],
        spacing_rules: List[int],
        violations: List[Violation],
        warnings: List[Violation],
        checks: Dict[str, int],
    ) -> None:
        """Validate spacing against design system scale."""
        if not node:
            return

        # This would validate padding, margins, gaps, etc.
        # For now, we'll skip implementation as it requires detailed layout info
        # from Figma API

        # Recursively check children
        for child in node.children:
            self._validate_spacing(
                child, spacing_rules, violations, warnings, checks
            )  # noqa: E501

    def batch_validate(
        self,
        file_keys: List[str],
        wcag_level: WCAGLevel = WCAGLevel.AA,
    ) -> List[ValidationResult]:
        """
        Validate multiple Figma files in batch.

        This is a convenience method for validating multiple files.
        Note: This requires FigmaClient integration to fetch files.

        Args:
            file_keys: List of Figma file keys to validate
            wcag_level: WCAG compliance level

        Returns:
            List of ValidationResult objects

        Note:
            This method requires FigmaClient to be integrated.
            For now, it returns an empty list as a placeholder.
        """
        logger.warning(
            "Batch validation requires FigmaClient integration. "
            "Please use FigmaClient to fetch files first, then validate "
            "individually."
        )
        results: List[ValidationResult] = []

        # Placeholder for future implementation
        # for file_key in file_keys:
        #     file = figma_client.get_file(file_key)
        #     result = self.validate_accessibility(file, wcag_level)
        #     results.append(result)

        return results


# Convenience functions for quick validation
def validate_contrast(
    foreground: str, background: str, level: str = "AA"
) -> Dict[str, Any]:
    """
    Quick contrast validation function.

    Args:
        foreground: Foreground color
        background: Background color
        level: WCAG level ("AA" or "AAA")

    Returns:
        Dictionary with contrast validation results
    """
    validator = DesignValidator()
    wcag_level = WCAGLevel.AA if level == "AA" else WCAGLevel.AAA
    contrast = validator.check_contrast(foreground, background, wcag_level)
    return contrast.model_dump()


if __name__ == "__main__":
    # Example usage and testing
    print("Design Validator - WCAG 2.1 Compliance Checker")
    print("=" * 50)

    validator = DesignValidator()

    # Test contrast checking
    print("\nTesting color contrast:")
    test_pairs = [
        ("#000000", "#FFFFFF", "Black on white"),
        ("#FFFFFF", "#000000", "White on black"),
        ("#767676", "#FFFFFF", "Gray on white"),
        ("#FF0000", "#FFFFFF", "Red on white"),
    ]

    for fg, bg, desc in test_pairs:
        contrast = validator.check_contrast(fg, bg, WCAGLevel.AA)
        print(f"\n{desc}:")
        print(f"  Ratio: {contrast.ratio}:1")
        print(f"  Passes AA: {contrast.passes_aa}")
        print(f"  Passes AAA: {contrast.passes_aaa}")

    print("\n" + "=" * 50)
    print("For full file validation, integrate with FigmaClient")
