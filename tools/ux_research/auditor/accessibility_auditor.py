"""Accessibility auditor for WCAG 2.1 compliance checking.

This module implements comprehensive accessibility auditing using Playwright,
axe-core, and pa11y for the devCrew_s1 UX Research Platform.
"""

import json
import logging
import re
import subprocess
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from playwright.async_api import Page, async_playwright
from pydantic import BaseModel, Field, field_validator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Violation(BaseModel):
    """Represents a WCAG violation detected during audit."""

    id: str = Field(..., description="Unique identifier for violation type")
    impact: str = Field(
        ..., description="Impact level: critical, serious, moderate, minor"
    )
    wcag_criterion: str = Field(..., description="WCAG 2.1 success criterion")
    description: str = Field(..., description="Human-readable description")
    affected_nodes: List[Dict[str, Any]] = Field(
        default_factory=list, description="HTML elements affected"
    )
    remediation: str = Field(..., description="Guidance on how to fix")
    help_url: str = Field(default="", description="URL to detailed help")

    @field_validator("impact")
    @classmethod
    def validate_impact(cls, v: str) -> str:
        """Validate impact level."""
        valid_impacts = ["critical", "serious", "moderate", "minor"]
        if v.lower() not in valid_impacts:
            raise ValueError(f"Impact must be one of {valid_impacts}")
        return v.lower()


class KeyboardIssue(BaseModel):
    """Represents a keyboard navigation issue."""

    element: str = Field(..., description="CSS selector of affected element")
    issue_type: str = Field(
        ..., description="Type: focus_trap, skip_link, tab_order, focus_visible"
    )
    description: str = Field(..., description="Issue description")
    severity: str = Field(..., description="Severity: high, medium, low")
    remediation: str = Field(..., description="How to fix")


class ScreenReaderIssue(BaseModel):
    """Represents a screen reader compatibility issue."""

    element: str = Field(..., description="CSS selector of affected element")
    issue_type: str = Field(
        ..., description="Type: missing_label, invalid_role, missing_landmark"
    )
    description: str = Field(..., description="Issue description")
    aria_attribute: Optional[str] = Field(
        default=None, description="Related ARIA attribute"
    )
    remediation: str = Field(..., description="How to fix")


class AuditSummary(BaseModel):
    """Summary statistics for an audit."""

    total_violations: int = Field(default=0, description="Total violations found")
    critical: int = Field(default=0, description="Critical violations")
    serious: int = Field(default=0, description="Serious violations")
    moderate: int = Field(default=0, description="Moderate violations")
    minor: int = Field(default=0, description="Minor violations")
    keyboard_issues: int = Field(default=0, description="Keyboard navigation issues")
    screen_reader_issues: int = Field(default=0, description="Screen reader issues")


class AuditResult(BaseModel):
    """Complete accessibility audit result."""

    audit_id: str = Field(
        default_factory=lambda: f"audit-{datetime.now().strftime('%Y%m%d')}-"
        f"{uuid.uuid4().hex[:8]}"
    )
    url: str = Field(..., description="URL that was audited")
    wcag_level: str = Field(..., description="WCAG level tested: A, AA, AAA")
    timestamp: datetime = Field(
        default_factory=datetime.now, description="Audit timestamp"
    )
    summary: AuditSummary = Field(
        default_factory=AuditSummary, description="Audit summary"
    )
    violations: List[Violation] = Field(
        default_factory=list, description="All violations found"
    )
    keyboard_issues: List[KeyboardIssue] = Field(
        default_factory=list, description="Keyboard navigation issues"
    )
    screen_reader_issues: List[ScreenReaderIssue] = Field(
        default_factory=list, description="Screen reader issues"
    )
    compliance_score: float = Field(
        default=0.0,
        ge=0.0,
        le=100.0,
        description="Overall compliance score (0-100)",
    )
    lighthouse_score: Optional[float] = Field(
        default=None, description="Lighthouse accessibility score"
    )
    viewports_tested: List[Tuple[int, int]] = Field(
        default_factory=list, description="Viewports tested"
    )
    browsers_tested: List[str] = Field(
        default_factory=list, description="Browsers tested"
    )


class AccessibilityAuditor:
    """Comprehensive accessibility auditor using Playwright and axe-core.

    This class provides WCAG 2.1 compliance checking with multi-viewport
    testing, keyboard navigation validation, and screen reader simulation.

    Attributes:
        config: Configuration dictionary for auditor behavior
        wcag_criteria: Mapping of WCAG success criteria to requirements
    """

    # WCAG 2.1 Level A and AA criteria mapping
    WCAG_CRITERIA = {
        "1.1.1": "Non-text Content",
        "1.2.1": "Audio-only and Video-only (Prerecorded)",
        "1.2.2": "Captions (Prerecorded)",
        "1.2.3": "Audio Description or Media Alternative (Prerecorded)",
        "1.3.1": "Info and Relationships",
        "1.3.2": "Meaningful Sequence",
        "1.3.3": "Sensory Characteristics",
        "1.3.4": "Orientation",
        "1.3.5": "Identify Input Purpose",
        "1.4.1": "Use of Color",
        "1.4.2": "Audio Control",
        "1.4.3": "Contrast (Minimum)",
        "1.4.4": "Resize Text",
        "1.4.5": "Images of Text",
        "1.4.10": "Reflow",
        "1.4.11": "Non-text Contrast",
        "1.4.12": "Text Spacing",
        "1.4.13": "Content on Hover or Focus",
        "2.1.1": "Keyboard",
        "2.1.2": "No Keyboard Trap",
        "2.1.4": "Character Key Shortcuts",
        "2.2.1": "Timing Adjustable",
        "2.2.2": "Pause, Stop, Hide",
        "2.3.1": "Three Flashes or Below Threshold",
        "2.4.1": "Bypass Blocks",
        "2.4.2": "Page Titled",
        "2.4.3": "Focus Order",
        "2.4.4": "Link Purpose (In Context)",
        "2.4.5": "Multiple Ways",
        "2.4.6": "Headings and Labels",
        "2.4.7": "Focus Visible",
        "2.5.1": "Pointer Gestures",
        "2.5.2": "Pointer Cancellation",
        "2.5.3": "Label in Name",
        "2.5.4": "Motion Actuation",
        "3.1.1": "Language of Page",
        "3.1.2": "Language of Parts",
        "3.2.1": "On Focus",
        "3.2.2": "On Input",
        "3.2.3": "Consistent Navigation",
        "3.2.4": "Consistent Identification",
        "3.3.1": "Error Identification",
        "3.3.2": "Labels or Instructions",
        "3.3.3": "Error Suggestion",
        "3.3.4": "Error Prevention (Legal, Financial, Data)",
        "4.1.1": "Parsing",
        "4.1.2": "Name, Role, Value",
        "4.1.3": "Status Messages",
    }

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the accessibility auditor.

        Args:
            config: Optional configuration dictionary with settings like
                   timeout, headless mode, user agent, etc.
        """
        self.config = config or {}
        self.timeout = self.config.get("timeout", 30000)
        self.headless = self.config.get("headless", True)
        self.user_agent = self.config.get("user_agent", None)
        self.axe_script_path = self._get_axe_script_path()

    def _get_axe_script_path(self) -> Optional[Path]:
        """Get path to axe-core JavaScript file.

        Returns:
            Path to axe.min.js if found, None otherwise
        """
        try:
            # Try to find axe-core in common locations
            import axe_selenium_python

            axe_package_path = Path(axe_selenium_python.__file__).parent
            axe_script = axe_package_path / "node_modules" / "axe-core" / "axe.min.js"

            if axe_script.exists():
                return axe_script

            # Alternative: check if installed via npm globally
            result = subprocess.run(
                ["npm", "root", "-g"],
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode == 0:
                global_npm = Path(result.stdout.strip())
                axe_script = global_npm / "axe-core" / "axe.min.js"
                if axe_script.exists():
                    return axe_script
        except (ImportError, subprocess.SubprocessError) as e:
            logger.warning(f"Could not locate axe-core script: {e}")

        return None

    async def audit(
        self,
        url: str,
        wcag_level: str = "AA",
        browsers: Optional[List[str]] = None,
        viewports: Optional[List[Tuple[int, int]]] = None,
    ) -> AuditResult:
        """Run comprehensive accessibility audit on a URL.

        Args:
            url: URL to audit
            wcag_level: WCAG conformance level to test (A, AA, or AAA)
            browsers: List of browser types to test (chromium, firefox, webkit)
            viewports: List of viewport dimensions to test as (width, height)

        Returns:
            AuditResult containing all findings and scores

        Raises:
            ValueError: If URL is invalid or wcag_level is not A, AA, or AAA
            RuntimeError: If browser automation fails
        """
        if wcag_level.upper() not in ["A", "AA", "AAA"]:
            raise ValueError("wcag_level must be A, AA, or AAA")

        if not url.startswith(("http://", "https://")):
            raise ValueError("URL must start with http:// or https://")

        browsers = browsers or ["chromium"]
        viewports = viewports or [(1920, 1080), (768, 1024), (375, 667)]

        result = AuditResult(
            url=url,
            wcag_level=wcag_level.upper(),
            browsers_tested=browsers,
            viewports_tested=viewports,
        )

        async with async_playwright() as p:
            for browser_name in browsers:
                try:
                    browser = await self._launch_browser(p, browser_name)

                    for viewport in viewports:
                        context = await browser.new_context(
                            viewport={"width": viewport[0], "height": viewport[1]},
                            user_agent=self.user_agent,
                        )

                        page = await context.new_page()
                        logger.info(f"Testing {url} on {browser_name} at {viewport}")

                        try:
                            await page.goto(url, timeout=self.timeout)
                            await page.wait_for_load_state("networkidle")

                            # Run axe-core violations detection
                            violations = await self.detect_violations(page, wcag_level)
                            result.violations.extend(violations)

                            # Test keyboard navigation
                            keyboard_issues = await self.test_keyboard_navigation(page)
                            result.keyboard_issues.extend(keyboard_issues)

                            # Test screen reader compatibility
                            sr_issues = await self.test_screen_reader_compatibility(
                                page
                            )
                            result.screen_reader_issues.extend(sr_issues)

                        except Exception as e:
                            logger.error(
                                f"Error testing {viewport} on {browser_name}: {e}"
                            )
                            raise RuntimeError(f"Failed to audit page: {str(e)}") from e
                        finally:
                            await context.close()

                    await browser.close()

                except Exception as e:
                    logger.error(f"Error with browser {browser_name}: {e}")
                    raise RuntimeError(f"Browser automation failed: {str(e)}") from e

        # Calculate summary statistics
        result.summary = self._calculate_summary(result)

        # Calculate compliance score
        result.compliance_score = self.calculate_compliance_score(result.violations)

        # Try to get Lighthouse score
        result.lighthouse_score = await self._get_lighthouse_score(url)

        return result

    async def _launch_browser(self, playwright: Any, browser_name: str) -> Any:
        """Launch a browser instance.

        Args:
            playwright: Playwright instance
            browser_name: Browser type (chromium, firefox, webkit)

        Returns:
            Browser instance
        """
        browser_type = getattr(playwright, browser_name)
        return await browser_type.launch(headless=self.headless)

    async def detect_violations(
        self, page: Page, wcag_level: str = "AA"
    ) -> List[Violation]:
        """Detect WCAG violations using axe-core.

        Args:
            page: Playwright page object
            wcag_level: WCAG level to test against

        Returns:
            List of Violation objects
        """
        violations = []

        try:
            # Inject axe-core into page
            axe_script = self._get_axe_core_script()
            if not axe_script:
                logger.warning("axe-core script not available, using fallback")
                return await self._fallback_violation_detection(page)

            await page.evaluate(axe_script)

            # Run axe with WCAG level configuration
            wcag_tags = self._get_wcag_tags(wcag_level)
            axe_results = await page.evaluate(
                f"""
                async () => {{
                    const results = await axe.run({{
                        runOnly: {{
                            type: 'tag',
                            values: {json.dumps(wcag_tags)}
                        }}
                    }});
                    return results;
                }}
            """
            )

            # Parse axe results
            for violation in axe_results.get("violations", []):
                violations.append(
                    Violation(
                        id=violation["id"],
                        impact=violation.get("impact", "moderate"),
                        wcag_criterion=self._extract_wcag_criterion(
                            violation.get("tags", [])
                        ),
                        description=violation.get("description", ""),
                        affected_nodes=[
                            {
                                "html": node.get("html", ""),
                                "target": node.get("target", []),
                                "impact": node.get("impact", ""),
                            }
                            for node in violation.get("nodes", [])
                        ],
                        remediation=violation.get("help", ""),
                        help_url=violation.get("helpUrl", ""),
                    )
                )

        except Exception as e:
            logger.error(f"Error detecting violations: {e}")

        return violations

    def _get_axe_core_script(self) -> Optional[str]:
        """Get axe-core JavaScript source code.

        Returns:
            JavaScript source code as string, or None if not available
        """
        if self.axe_script_path and self.axe_script_path.exists():
            return self.axe_script_path.read_text()

        # Fallback: Try to load from CDN-like embedded version
        # In production, this should be bundled with the package
        return None

    def _get_wcag_tags(self, wcag_level: str) -> List[str]:
        """Get axe-core tags for WCAG level.

        Args:
            wcag_level: WCAG level (A, AA, AAA)

        Returns:
            List of axe-core tag strings
        """
        tags = ["wcag2a"]
        if wcag_level in ["AA", "AAA"]:
            tags.append("wcag2aa")
        if wcag_level == "AAA":
            tags.append("wcag2aaa")
        tags.append("wcag21a")
        if wcag_level in ["AA", "AAA"]:
            tags.append("wcag21aa")
        if wcag_level == "AAA":
            tags.append("wcag21aaa")
        return tags

    def _extract_wcag_criterion(self, tags: List[str]) -> str:
        """Extract WCAG success criterion from axe tags.

        Args:
            tags: List of axe-core tags

        Returns:
            WCAG criterion string (e.g., "1.4.3 Contrast (Minimum)")
        """
        for tag in tags:
            # Look for patterns like "wcag143" or "wcag111"
            match = re.match(r"wcag(\d)(\d)(\d)", tag)
            if match:
                criterion = f"{match.group(1)}.{match.group(2)}.{match.group(3)}"
                criterion_name = self.WCAG_CRITERIA.get(criterion, "Unknown")
                return f"{criterion} {criterion_name}"
        return "Unknown criterion"

    async def _fallback_violation_detection(self, page: Page) -> List[Violation]:
        """Fallback violation detection without axe-core.

        This implements basic checks when axe-core is not available.

        Args:
            page: Playwright page object

        Returns:
            List of Violation objects
        """
        violations = []

        # Check for images without alt text
        img_violations = await page.evaluate(
            """
            () => {
                const images = Array.from(document.querySelectorAll('img'));
                return images
                    .filter(img => !img.alt && !img.getAttribute('aria-label'))
                    .map(img => ({
                        html: img.outerHTML,
                        target: [img.id || img.className || 'img']
                    }));
            }
        """
        )

        if img_violations:
            violations.append(
                Violation(
                    id="image-alt",
                    impact="critical",
                    wcag_criterion="1.1.1 Non-text Content",
                    description="Images must have alternative text",
                    affected_nodes=img_violations,
                    remediation="Add alt attribute to all images",
                    help_url="https://dequeuniversity.com/rules/axe/4.8/image-alt",
                )
            )

        # Check for form inputs without labels
        form_violations = await page.evaluate(
            """
            () => {
                const inputs = Array.from(document.querySelectorAll(
                    'input:not([type="hidden"]), textarea, select'
                ));
                return inputs
                    .filter(input => {
                        const label = document.querySelector(
                            `label[for="${input.id}"]`
                        );
                        return !label && !input.getAttribute('aria-label');
                    })
                    .map(input => ({
                        html: input.outerHTML,
                        target: [input.id || input.name || 'input']
                    }));
            }
        """
        )

        if form_violations:
            violations.append(
                Violation(
                    id="label",
                    impact="critical",
                    wcag_criterion="1.3.1 Info and Relationships",
                    description="Form elements must have labels",
                    affected_nodes=form_violations,
                    remediation="Add label elements or aria-label attributes",
                    help_url="https://dequeuniversity.com/rules/axe/4.8/label",
                )
            )

        return violations

    async def test_keyboard_navigation(self, page: Page) -> List[KeyboardIssue]:
        """Test keyboard accessibility.

        Tests tab order, focus management, keyboard traps, and focus visibility.

        Args:
            page: Playwright page object

        Returns:
            List of KeyboardIssue objects
        """
        issues = []

        try:
            # Test for keyboard trap
            keyboard_trap = await self._test_keyboard_trap(page)
            if keyboard_trap:
                issues.append(keyboard_trap)

            # Test focus visibility
            focus_visible_issues = await self._test_focus_visible(page)
            issues.extend(focus_visible_issues)

            # Test skip links
            skip_link_issue = await self._test_skip_links(page)
            if skip_link_issue:
                issues.append(skip_link_issue)

            # Test tab order
            tab_order_issues = await self._test_tab_order(page)
            issues.extend(tab_order_issues)

        except Exception as e:
            logger.error(f"Error testing keyboard navigation: {e}")

        return issues

    async def _test_keyboard_trap(self, page: Page) -> Optional[KeyboardIssue]:
        """Test for keyboard traps.

        Args:
            page: Playwright page object

        Returns:
            KeyboardIssue if trap detected, None otherwise
        """
        try:
            # Get all focusable elements
            focusable = await page.evaluate(
                """
                () => {
                    const selector = 'a[href], button, input, textarea, ' +
                                   'select, [tabindex]:not([tabindex="-1"])';
                    return Array.from(document.querySelectorAll(selector)).length;
                }
            """
            )

            if focusable < 2:
                return None

            # Press Tab multiple times and check if focus cycles properly
            focused_elements: List[str] = []
            for _ in range(min(focusable + 5, 20)):
                await page.keyboard.press("Tab")
                focused = await page.evaluate("document.activeElement.outerHTML")
                if focused in focused_elements[:-1]:
                    # Focus returned to a previous element too early
                    return KeyboardIssue(
                        element=focused,
                        issue_type="focus_trap",
                        description="Keyboard focus appears to be trapped",
                        severity="high",
                        remediation=(
                            "Ensure focus can move freely through all "
                            "interactive elements"
                        ),
                    )
                focused_elements.append(focused)

        except Exception as e:
            logger.error(f"Error testing keyboard trap: {e}")

        return None

    async def _test_focus_visible(self, page: Page) -> List[KeyboardIssue]:
        """Test focus visibility.

        Args:
            page: Playwright page object

        Returns:
            List of KeyboardIssue objects
        """
        issues = []

        try:
            # Check if focused elements have visible focus indicators
            elements_without_focus = await page.evaluate(
                """
                () => {
                    const selector = 'a[href], button, input, textarea, ' +
                                   'select, [tabindex]:not([tabindex="-1"])';
                    const elements = Array.from(
                        document.querySelectorAll(selector)
                    );

                    return elements.slice(0, 10).filter(el => {
                        el.focus();
                        const styles = window.getComputedStyle(el);
                        const outlineWidth = styles.outlineWidth;
                        const outlineStyle = styles.outlineStyle;

                        return outlineStyle === 'none' ||
                               outlineWidth === '0px';
                    }).map(el => el.outerHTML);
                }
            """
            )

            if elements_without_focus:
                for element in elements_without_focus:
                    issues.append(
                        KeyboardIssue(
                            element=element,
                            issue_type="focus_visible",
                            description="Element lacks visible focus indicator",
                            severity="medium",
                            remediation=(
                                "Add visible focus styles using :focus or "
                                ":focus-visible"
                            ),
                        )
                    )

        except Exception as e:
            logger.error(f"Error testing focus visible: {e}")

        return issues

    async def _test_skip_links(self, page: Page) -> Optional[KeyboardIssue]:
        """Test for skip navigation links.

        Args:
            page: Playwright page object

        Returns:
            KeyboardIssue if skip links are missing, None otherwise
        """
        try:
            has_skip_link = await page.evaluate(
                """
                () => {
                    const links = Array.from(document.querySelectorAll('a'));
                    return links.some(link =>
                        link.textContent.toLowerCase().includes('skip') ||
                        link.textContent.toLowerCase().includes('jump')
                    );
                }
            """
            )

            if not has_skip_link:
                return KeyboardIssue(
                    element="body",
                    issue_type="skip_link",
                    description="Page lacks skip navigation link",
                    severity="medium",
                    remediation=(
                        "Add a skip link at the beginning of the page to "
                        "allow keyboard users to bypass navigation"
                    ),
                )

        except Exception as e:
            logger.error(f"Error testing skip links: {e}")

        return None

    async def _test_tab_order(self, page: Page) -> List[KeyboardIssue]:
        """Test tab order logic.

        Args:
            page: Playwright page object

        Returns:
            List of KeyboardIssue objects
        """
        issues = []

        try:
            # Check for positive tabindex values
            positive_tabindex = await page.evaluate(
                """
                () => {
                    const elements = Array.from(
                        document.querySelectorAll('[tabindex]')
                    );
                    return elements
                        .filter(el => parseInt(el.tabIndex) > 0)
                        .map(el => el.outerHTML);
                }
            """
            )

            if positive_tabindex:
                for element in positive_tabindex:
                    issues.append(
                        KeyboardIssue(
                            element=element,
                            issue_type="tab_order",
                            description="Positive tabindex disrupts natural tab order",
                            severity="medium",
                            remediation=(
                                "Remove positive tabindex values and use "
                                "DOM order instead"
                            ),
                        )
                    )

        except Exception as e:
            logger.error(f"Error testing tab order: {e}")

        return issues

    async def test_screen_reader_compatibility(
        self, page: Page
    ) -> List[ScreenReaderIssue]:
        """Test screen reader compatibility.

        Tests ARIA labels, roles, landmarks, and semantic HTML.

        Args:
            page: Playwright page object

        Returns:
            List of ScreenReaderIssue objects
        """
        issues = []

        try:
            # Check for missing ARIA labels on interactive elements
            missing_labels = await page.evaluate(
                """
                () => {
                    const selector = 'button, [role="button"], ' +
                                   '[role="link"], [role="tab"]';
                    const elements = Array.from(
                        document.querySelectorAll(selector)
                    );

                    return elements.filter(el => {
                        const hasText = el.textContent.trim().length > 0;
                        const hasLabel = el.getAttribute('aria-label');
                        const hasLabelledby = el.getAttribute('aria-labelledby');
                        return !hasText && !hasLabel && !hasLabelledby;
                    }).map(el => ({
                        html: el.outerHTML,
                        role: el.getAttribute('role') || el.tagName
                    }));
                }
            """
            )

            for element_info in missing_labels:
                issues.append(
                    ScreenReaderIssue(
                        element=element_info["html"],
                        issue_type="missing_label",
                        description="Interactive element lacks accessible name",
                        aria_attribute="aria-label",
                        remediation=(
                            "Add aria-label, aria-labelledby, or text content"
                        ),
                    )
                )

            # Check for invalid ARIA roles
            invalid_roles = await page.evaluate(
                """
                () => {
                    const validRoles = ['alert', 'alertdialog', 'application',
                        'article', 'banner', 'button', 'checkbox',
                        'complementary', 'contentinfo', 'dialog', 'document',
                        'feed', 'form', 'grid', 'heading', 'img', 'link',
                        'list', 'listbox', 'listitem', 'main', 'menu',
                        'menubar', 'menuitem', 'navigation', 'region',
                        'search', 'switch', 'tab', 'table', 'tabpanel',
                        'textbox', 'timer', 'toolbar', 'tree'];

                    const elements = Array.from(
                        document.querySelectorAll('[role]')
                    );
                    return elements.filter(el => {
                        const role = el.getAttribute('role');
                        return !validRoles.includes(role);
                    }).map(el => ({
                        html: el.outerHTML,
                        role: el.getAttribute('role')
                    }));
                }
            """
            )

            for element_info in invalid_roles:
                issues.append(
                    ScreenReaderIssue(
                        element=element_info["html"],
                        issue_type="invalid_role",
                        description=f"Invalid ARIA role: {element_info['role']}",
                        aria_attribute="role",
                        remediation="Use a valid ARIA role or remove the attribute",
                    )
                )

            # Check for missing landmarks
            has_landmarks = await page.evaluate(
                """
                () => {
                    const landmarkSelectors = [
                        'header', '[role="banner"]',
                        'main', '[role="main"]',
                        'footer', '[role="contentinfo"]',
                        'nav', '[role="navigation"]'
                    ];
                    return landmarkSelectors.some(selector =>
                        document.querySelector(selector) !== null
                    );
                }
            """
            )

            if not has_landmarks:
                issues.append(
                    ScreenReaderIssue(
                        element="body",
                        issue_type="missing_landmark",
                        description="Page lacks landmark regions",
                        aria_attribute="role",
                        remediation=(
                            "Add semantic HTML5 elements (header, main, "
                            "footer, nav) or ARIA landmark roles"
                        ),
                    )
                )

        except Exception as e:
            logger.error(f"Error testing screen reader compatibility: {e}")

        return issues

    def calculate_compliance_score(self, violations: List[Violation]) -> float:
        """Calculate overall compliance score.

        Score is based on the number and severity of violations.
        Formula: 100 - (critical*5 + serious*3 + moderate*2 + minor*1)
        Score is clamped to 0-100 range.

        Args:
            violations: List of violations found

        Returns:
            Compliance score between 0 and 100
        """
        if not violations:
            return 100.0

        penalty = 0
        impact_weights = {"critical": 5, "serious": 3, "moderate": 2, "minor": 1}

        for violation in violations:
            weight = impact_weights.get(violation.impact, 1)
            # Count affected nodes for more accurate scoring
            node_count = max(1, len(violation.affected_nodes))
            penalty += weight * node_count

        # Base score calculation
        score = max(0.0, 100.0 - penalty)

        return round(score, 2)

    def _calculate_summary(self, result: AuditResult) -> AuditSummary:
        """Calculate summary statistics from audit result.

        Args:
            result: AuditResult to summarize

        Returns:
            AuditSummary with counts
        """
        summary = AuditSummary()

        # Count violations by impact
        for violation in result.violations:
            summary.total_violations += 1
            if violation.impact == "critical":
                summary.critical += 1
            elif violation.impact == "serious":
                summary.serious += 1
            elif violation.impact == "moderate":
                summary.moderate += 1
            elif violation.impact == "minor":
                summary.minor += 1

        summary.keyboard_issues = len(result.keyboard_issues)
        summary.screen_reader_issues = len(result.screen_reader_issues)

        return summary

    async def _get_lighthouse_score(self, url: str) -> Optional[float]:
        """Get Lighthouse accessibility score.

        Args:
            url: URL to test

        Returns:
            Lighthouse accessibility score (0-100) or None if unavailable
        """
        try:
            # Try to run Lighthouse CLI if available
            result = subprocess.run(
                [
                    "lighthouse",
                    url,
                    "--only-categories=accessibility",
                    "--output=json",
                    "--quiet",
                    "--chrome-flags='--headless'",
                ],
                capture_output=True,
                text=True,
                timeout=60,
                check=False,
            )

            if result.returncode == 0:
                data = json.loads(result.stdout)
                accessibility_data = data.get("categories", {}).get("accessibility", {})
                score = accessibility_data.get("score")
                if score is not None:
                    return round(score * 100, 2)

        except (subprocess.SubprocessError, json.JSONDecodeError, FileNotFoundError):
            logger.debug("Lighthouse not available or failed to run")

        return None

    def generate_report(
        self, result: AuditResult, format: str = "json"
    ) -> str:  # noqa: A002
        """Generate audit report in specified format.

        Args:
            result: AuditResult to format
            format: Output format (json, html, or markdown)

        Returns:
            Formatted report as string

        Raises:
            ValueError: If format is not supported
        """
        if format == "json":
            return result.model_dump_json(indent=2)
        elif format == "html":
            return self._generate_html_report(result)
        elif format == "markdown":
            return self._generate_markdown_report(result)
        else:
            raise ValueError(f"Unsupported format: {format}")

    def _generate_html_report(self, result: AuditResult) -> str:
        """Generate HTML report.

        Args:
            result: AuditResult to format

        Returns:
            HTML report as string
        """
        html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Accessibility Audit Report - {result.audit_id}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; line-height: 1.6; }}
        h1, h2, h3 {{ color: #333; }}
        .summary {{ background: #f4f4f4; padding: 15px; border-radius: 5px; }}
        .violation {{ border-left: 4px solid #d32f2f; padding: 10px; margin: 10px 0; }}
        .critical {{ border-color: #d32f2f; }}
        .serious {{ border-color: #f57c00; }}
        .moderate {{ border-color: #fbc02d; }}
        .minor {{ border-color: #388e3c; }}
        .score {{ font-size: 2em; font-weight: bold; }}
        code {{ background: #f4f4f4; padding: 2px 5px; border-radius: 3px; }}
    </style>
</head>
<body>
    <h1>Accessibility Audit Report</h1>
    <p><strong>Audit ID:</strong> {result.audit_id}</p>
    <p><strong>URL:</strong> {result.url}</p>
    <p><strong>WCAG Level:</strong> {result.wcag_level}</p>
    <p><strong>Date:</strong> {result.timestamp.strftime('%Y-%m-%d %H:%M:%S')}</p>

    <div class="summary">
        <h2>Summary</h2>
        <p class="score">Compliance Score: {result.compliance_score}%</p>
        <p><strong>Total Violations:</strong> {result.summary.total_violations}</p>
        <ul>
            <li>Critical: {result.summary.critical}</li>
            <li>Serious: {result.summary.serious}</li>
            <li>Moderate: {result.summary.moderate}</li>
            <li>Minor: {result.summary.minor}</li>
        </ul>
        <p><strong>Keyboard Issues:</strong> {result.summary.keyboard_issues}</p>
        <p><strong>Screen Reader Issues:</strong> \
{result.summary.screen_reader_issues}</p>
    </div>

    <h2>Violations</h2>
"""

        for violation in result.violations:
            html += f"""
    <div class="violation {violation.impact}">
        <h3>{violation.id}</h3>
        <p><strong>Impact:</strong> {violation.impact}</p>
        <p><strong>WCAG:</strong> {violation.wcag_criterion}</p>
        <p>{violation.description}</p>
        <p><strong>Affected Elements:</strong> {len(violation.affected_nodes)}</p>
        <p><strong>Remediation:</strong> {violation.remediation}</p>
        <p><a href="{violation.help_url}" target="_blank">Learn more</a></p>
    </div>
"""

        html += """
</body>
</html>
"""
        return html

    def _generate_markdown_report(self, result: AuditResult) -> str:
        """Generate Markdown report.

        Args:
            result: AuditResult to format

        Returns:
            Markdown report as string
        """
        md = f"""# Accessibility Audit Report

**Audit ID:** {result.audit_id}
**URL:** {result.url}
**WCAG Level:** {result.wcag_level}
**Date:** {result.timestamp.strftime('%Y-%m-%d %H:%M:%S')}

## Summary

**Compliance Score:** {result.compliance_score}%

- **Total Violations:** {result.summary.total_violations}
  - Critical: {result.summary.critical}
  - Serious: {result.summary.serious}
  - Moderate: {result.summary.moderate}
  - Minor: {result.summary.minor}
- **Keyboard Issues:** {result.summary.keyboard_issues}
- **Screen Reader Issues:** {result.summary.screen_reader_issues}

## Violations

"""

        for i, violation in enumerate(result.violations, 1):
            md += f"""
### {i}. {violation.id} [{violation.impact.upper()}]

**WCAG Criterion:** {violation.wcag_criterion}

**Description:** {violation.description}

**Affected Elements:** {len(violation.affected_nodes)}

**Remediation:** {violation.remediation}

[Learn more]({violation.help_url})

---

"""

        return md
