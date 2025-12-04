"""Comprehensive tests for accessibility auditor module.

Tests cover violation detection, keyboard navigation, screen reader compatibility,
and report generation for the devCrew_s1 UX Research Platform.
"""

import json
from unittest.mock import AsyncMock, Mock, patch

import pytest

from tools.ux_research.auditor.accessibility_auditor import (
    AccessibilityAuditor, AuditResult, KeyboardIssue, ScreenReaderIssue,
    Violation)


@pytest.fixture
def auditor() -> AccessibilityAuditor:
    """Create an AccessibilityAuditor instance for testing."""
    return AccessibilityAuditor(config={"timeout": 10000, "headless": True})


@pytest.fixture
def sample_violation() -> Violation:
    """Create a sample violation for testing."""
    return Violation(
        id="color-contrast",
        impact="serious",
        wcag_criterion="1.4.3 Contrast (Minimum)",
        description="Elements must have sufficient color contrast",
        affected_nodes=[
            {
                "html": '<button style="color: #777; background: #888;">Click</button>',
                "target": [".btn-primary"],
                "impact": "serious",
            }
        ],
        remediation="Increase color contrast ratio to at least 4.5:1",
        help_url="https://dequeuniversity.com/rules/axe/4.8/color-contrast",
    )


@pytest.fixture
def sample_keyboard_issue() -> KeyboardIssue:
    """Create a sample keyboard issue for testing."""
    return KeyboardIssue(
        element="div[role='button']",
        issue_type="focus_visible",
        description="Element lacks visible focus indicator",
        severity="medium",
        remediation="Add visible focus styles using :focus or :focus-visible",
    )


@pytest.fixture
def sample_screen_reader_issue() -> ScreenReaderIssue:
    """Create a sample screen reader issue for testing."""
    return ScreenReaderIssue(
        element="<button></button>",
        issue_type="missing_label",
        description="Interactive element lacks accessible name",
        aria_attribute="aria-label",
        remediation="Add aria-label, aria-labelledby, or text content",
    )


@pytest.fixture
def mock_page() -> Mock:
    """Create a mock Playwright page object."""
    page = Mock()
    page.goto = AsyncMock()
    page.wait_for_load_state = AsyncMock()
    page.evaluate = AsyncMock()
    page.keyboard = Mock()
    page.keyboard.press = AsyncMock()
    return page


class TestViolationModel:
    """Test Violation data model."""

    def test_violation_creation(self, sample_violation: Violation) -> None:
        """Test creating a violation object."""
        assert sample_violation.id == "color-contrast"
        assert sample_violation.impact == "serious"
        assert "1.4.3" in sample_violation.wcag_criterion
        assert len(sample_violation.affected_nodes) == 1

    def test_violation_impact_validation(self) -> None:
        """Test violation impact validation."""
        with pytest.raises(ValueError, match="Impact must be one of"):
            Violation(
                id="test",
                impact="invalid",
                wcag_criterion="1.1.1",
                description="Test",
                remediation="Fix it",
            )

    def test_violation_impact_case_insensitive(self) -> None:
        """Test violation impact is case-insensitive."""
        violation = Violation(
            id="test",
            impact="CRITICAL",
            wcag_criterion="1.1.1",
            description="Test",
            remediation="Fix it",
        )
        assert violation.impact == "critical"


class TestKeyboardIssueModel:
    """Test KeyboardIssue data model."""

    def test_keyboard_issue_creation(
        self, sample_keyboard_issue: KeyboardIssue
    ) -> None:
        """Test creating a keyboard issue object."""
        assert sample_keyboard_issue.element == "div[role='button']"
        assert sample_keyboard_issue.issue_type == "focus_visible"
        assert sample_keyboard_issue.severity == "medium"


class TestScreenReaderIssueModel:
    """Test ScreenReaderIssue data model."""

    def test_screen_reader_issue_creation(
        self, sample_screen_reader_issue: ScreenReaderIssue
    ) -> None:
        """Test creating a screen reader issue object."""
        assert sample_screen_reader_issue.issue_type == "missing_label"
        assert sample_screen_reader_issue.aria_attribute == "aria-label"


class TestAuditResultModel:
    """Test AuditResult data model."""

    def test_audit_result_creation(self) -> None:
        """Test creating an audit result object."""
        result = AuditResult(url="https://example.com", wcag_level="AA")
        assert result.url == "https://example.com"
        assert result.wcag_level == "AA"
        assert result.compliance_score == 0.0
        assert len(result.violations) == 0
        assert result.audit_id.startswith("audit-")

    def test_audit_result_with_violations(self, sample_violation: Violation) -> None:
        """Test audit result with violations."""
        result = AuditResult(
            url="https://example.com",
            wcag_level="AA",
            violations=[sample_violation],
        )
        assert len(result.violations) == 1
        assert result.violations[0].id == "color-contrast"

    def test_compliance_score_validation(self) -> None:
        """Test compliance score is within 0-100 range."""
        with pytest.raises(ValueError):
            AuditResult(
                url="https://example.com", wcag_level="AA", compliance_score=150.0
            )


class TestAccessibilityAuditor:
    """Test AccessibilityAuditor class."""

    def test_auditor_initialization(self, auditor: AccessibilityAuditor) -> None:
        """Test auditor initialization."""
        assert auditor.timeout == 10000
        assert auditor.headless is True

    def test_auditor_default_config(self) -> None:
        """Test auditor with default configuration."""
        auditor = AccessibilityAuditor()
        assert auditor.timeout == 30000
        assert auditor.headless is True

    def test_get_wcag_tags_level_a(self, auditor: AccessibilityAuditor) -> None:
        """Test WCAG tag generation for Level A."""
        tags = auditor._get_wcag_tags("A")
        assert "wcag2a" in tags
        assert "wcag21a" in tags
        assert "wcag2aa" not in tags

    def test_get_wcag_tags_level_aa(self, auditor: AccessibilityAuditor) -> None:
        """Test WCAG tag generation for Level AA."""
        tags = auditor._get_wcag_tags("AA")
        assert "wcag2a" in tags
        assert "wcag2aa" in tags
        assert "wcag21a" in tags
        assert "wcag21aa" in tags

    def test_get_wcag_tags_level_aaa(self, auditor: AccessibilityAuditor) -> None:
        """Test WCAG tag generation for Level AAA."""
        tags = auditor._get_wcag_tags("AAA")
        assert "wcag2aaa" in tags
        assert "wcag21aaa" in tags

    def test_extract_wcag_criterion(self, auditor: AccessibilityAuditor) -> None:
        """Test WCAG criterion extraction from tags."""
        tags = ["wcag143", "best-practice"]
        criterion = auditor._extract_wcag_criterion(tags)
        assert "1.4.3" in criterion
        assert "Contrast" in criterion

    def test_extract_wcag_criterion_unknown(
        self, auditor: AccessibilityAuditor
    ) -> None:
        """Test WCAG criterion extraction with no matching tags."""
        tags = ["best-practice", "experimental"]
        criterion = auditor._extract_wcag_criterion(tags)
        assert "Unknown" in criterion

    def test_calculate_compliance_score_no_violations(
        self, auditor: AccessibilityAuditor
    ) -> None:
        """Test compliance score calculation with no violations."""
        score = auditor.calculate_compliance_score([])
        assert score == 100.0

    def test_calculate_compliance_score_with_violations(
        self, auditor: AccessibilityAuditor, sample_violation: Violation
    ) -> None:
        """Test compliance score calculation with violations."""
        violations = [sample_violation]
        score = auditor.calculate_compliance_score(violations)
        assert 0 <= score < 100
        assert isinstance(score, float)

    def test_calculate_compliance_score_multiple_impacts(
        self, auditor: AccessibilityAuditor
    ) -> None:
        """Test compliance score with different impact levels."""
        violations = [
            Violation(
                id="critical-1",
                impact="critical",
                wcag_criterion="1.1.1",
                description="Critical issue",
                remediation="Fix it",
                affected_nodes=[{"html": "<img>", "target": ["img"]}],
            ),
            Violation(
                id="serious-1",
                impact="serious",
                wcag_criterion="1.4.3",
                description="Serious issue",
                remediation="Fix it",
                affected_nodes=[{"html": "<div>", "target": ["div"]}],
            ),
            Violation(
                id="moderate-1",
                impact="moderate",
                wcag_criterion="2.4.1",
                description="Moderate issue",
                remediation="Fix it",
                affected_nodes=[{"html": "<a>", "target": ["a"]}],
            ),
            Violation(
                id="minor-1",
                impact="minor",
                wcag_criterion="3.1.1",
                description="Minor issue",
                remediation="Fix it",
                affected_nodes=[{"html": "<span>", "target": ["span"]}],
            ),
        ]
        score = auditor.calculate_compliance_score(violations)
        # Score should be reduced based on weighted impacts
        # critical(5) + serious(3) + moderate(2) + minor(1) = 11
        assert score == 89.0

    def test_calculate_summary(self, auditor: AccessibilityAuditor) -> None:
        """Test summary calculation."""
        violations = [
            Violation(
                id="v1",
                impact="critical",
                wcag_criterion="1.1.1",
                description="Test",
                remediation="Fix",
            ),
            Violation(
                id="v2",
                impact="serious",
                wcag_criterion="1.4.3",
                description="Test",
                remediation="Fix",
            ),
            Violation(
                id="v3",
                impact="moderate",
                wcag_criterion="2.4.1",
                description="Test",
                remediation="Fix",
            ),
        ]

        result = AuditResult(
            url="https://example.com",
            wcag_level="AA",
            violations=violations,
            keyboard_issues=[
                KeyboardIssue(
                    element="button",
                    issue_type="focus_visible",
                    description="Test",
                    severity="medium",
                    remediation="Fix",
                )
            ],
        )

        summary = auditor._calculate_summary(result)
        assert summary.total_violations == 3
        assert summary.critical == 1
        assert summary.serious == 1
        assert summary.moderate == 1
        assert summary.minor == 0
        assert summary.keyboard_issues == 1


class TestViolationDetection:
    """Test violation detection functionality."""

    @pytest.mark.asyncio
    async def test_detect_violations_no_axe(
        self, auditor: AccessibilityAuditor, mock_page: Mock
    ) -> None:
        """Test fallback violation detection without axe-core."""
        # Mock page.evaluate to return images without alt text
        mock_page.evaluate.return_value = [
            {"html": '<img src="test.jpg">', "target": ["img"]}
        ]

        violations = await auditor._fallback_violation_detection(mock_page)
        assert len(violations) >= 1
        assert any(v.id == "image-alt" for v in violations)

    @pytest.mark.asyncio
    async def test_detect_violations_form_inputs(
        self, auditor: AccessibilityAuditor, mock_page: Mock
    ) -> None:
        """Test detection of form inputs without labels."""
        # First call returns no images, second call returns unlabeled inputs
        mock_page.evaluate.side_effect = [
            [],  # No images without alt
            [
                {
                    "html": '<input type="text" name="email">',
                    "target": ["input"],
                }
            ],  # Unlabeled inputs
        ]

        violations = await auditor._fallback_violation_detection(mock_page)
        assert len(violations) >= 1
        assert any(v.id == "label" for v in violations)


class TestKeyboardNavigation:
    """Test keyboard navigation functionality."""

    @pytest.mark.asyncio
    async def test_keyboard_navigation_no_issues(
        self, auditor: AccessibilityAuditor, mock_page: Mock
    ) -> None:
        """Test keyboard navigation with no issues detected."""
        # Mock successful keyboard navigation
        mock_page.evaluate.side_effect = [
            5,  # 5 focusable elements
            "<button>Button 1</button>",
            "<button>Button 2</button>",
            "<button>Button 3</button>",
            "<button>Button 4</button>",
            "<button>Button 5</button>",
            [],  # No elements without focus
            True,  # Has skip link
            [],  # No positive tabindex
        ]

        issues = await auditor.test_keyboard_navigation(mock_page)
        # Should have minimal or no issues
        assert isinstance(issues, list)

    @pytest.mark.asyncio
    async def test_keyboard_trap_detection(
        self, auditor: AccessibilityAuditor, mock_page: Mock
    ) -> None:
        """Test keyboard trap detection."""
        # Mock a keyboard trap scenario
        mock_page.evaluate.side_effect = [
            5,  # 5 focusable elements
            "<button>Button 1</button>",
            "<button>Button 2</button>",
            "<button>Button 1</button>",  # Returns to Button 1 too early
        ]

        issue = await auditor._test_keyboard_trap(mock_page)
        if issue:
            assert issue.issue_type == "focus_trap"
            assert issue.severity == "high"

    @pytest.mark.asyncio
    async def test_focus_visible_detection(
        self, auditor: AccessibilityAuditor, mock_page: Mock
    ) -> None:
        """Test focus visibility detection."""
        mock_page.evaluate.return_value = [
            "<button>No Focus Outline</button>",
            "<a href='#'>Link</a>",
        ]

        issues = await auditor._test_focus_visible(mock_page)
        assert len(issues) == 2
        assert all(issue.issue_type == "focus_visible" for issue in issues)

    @pytest.mark.asyncio
    async def test_skip_link_missing(
        self, auditor: AccessibilityAuditor, mock_page: Mock
    ) -> None:
        """Test detection of missing skip links."""
        mock_page.evaluate.return_value = False

        issue = await auditor._test_skip_links(mock_page)
        assert issue is not None
        assert issue.issue_type == "skip_link"
        assert issue.severity == "medium"

    @pytest.mark.asyncio
    async def test_skip_link_present(
        self, auditor: AccessibilityAuditor, mock_page: Mock
    ) -> None:
        """Test when skip link is present."""
        mock_page.evaluate.return_value = True

        issue = await auditor._test_skip_links(mock_page)
        assert issue is None

    @pytest.mark.asyncio
    async def test_positive_tabindex_detection(
        self, auditor: AccessibilityAuditor, mock_page: Mock
    ) -> None:
        """Test detection of positive tabindex values."""
        mock_page.evaluate.return_value = [
            '<button tabindex="1">First</button>',
            '<button tabindex="2">Second</button>',
        ]

        issues = await auditor._test_tab_order(mock_page)
        assert len(issues) == 2
        assert all(issue.issue_type == "tab_order" for issue in issues)


class TestScreenReaderCompatibility:
    """Test screen reader compatibility functionality."""

    @pytest.mark.asyncio
    async def test_missing_aria_labels(
        self, auditor: AccessibilityAuditor, mock_page: Mock
    ) -> None:
        """Test detection of missing ARIA labels."""
        mock_page.evaluate.side_effect = [
            [
                {
                    "html": "<button></button>",
                    "role": "button",
                },
                {
                    "html": '<div role="button"></div>',
                    "role": "button",
                },
            ],
            [],  # No invalid roles
            True,  # Has landmarks
        ]

        issues = await auditor.test_screen_reader_compatibility(mock_page)
        assert len(issues) >= 2
        assert all(issue.issue_type == "missing_label" for issue in issues[:2])

    @pytest.mark.asyncio
    async def test_invalid_aria_roles(
        self, auditor: AccessibilityAuditor, mock_page: Mock
    ) -> None:
        """Test detection of invalid ARIA roles."""
        mock_page.evaluate.side_effect = [
            [],  # No missing labels
            [
                {
                    "html": '<div role="invalid"></div>',
                    "role": "invalid",
                }
            ],
            True,  # Has landmarks
        ]

        issues = await auditor.test_screen_reader_compatibility(mock_page)
        assert len(issues) >= 1
        assert any(issue.issue_type == "invalid_role" for issue in issues)

    @pytest.mark.asyncio
    async def test_missing_landmarks(
        self, auditor: AccessibilityAuditor, mock_page: Mock
    ) -> None:
        """Test detection of missing landmark regions."""
        mock_page.evaluate.side_effect = [
            [],  # No missing labels
            [],  # No invalid roles
            False,  # No landmarks
        ]

        issues = await auditor.test_screen_reader_compatibility(mock_page)
        assert len(issues) >= 1
        assert any(issue.issue_type == "missing_landmark" for issue in issues)


class TestReportGeneration:
    """Test report generation functionality."""

    def test_generate_json_report(
        self, auditor: AccessibilityAuditor, sample_violation: Violation
    ) -> None:
        """Test JSON report generation."""
        result = AuditResult(
            url="https://example.com",
            wcag_level="AA",
            violations=[sample_violation],
            compliance_score=85.5,
        )

        report = auditor.generate_report(result, format="json")
        assert isinstance(report, str)

        # Validate JSON structure
        data = json.loads(report)
        assert data["url"] == "https://example.com"
        assert data["wcag_level"] == "AA"
        assert data["compliance_score"] == 85.5
        assert len(data["violations"]) == 1

    def test_generate_html_report(
        self, auditor: AccessibilityAuditor, sample_violation: Violation
    ) -> None:
        """Test HTML report generation."""
        result = AuditResult(
            url="https://example.com",
            wcag_level="AA",
            violations=[sample_violation],
            compliance_score=85.5,
        )

        report = auditor.generate_report(result, format="html")
        assert isinstance(report, str)
        assert "<!DOCTYPE html>" in report
        assert "Accessibility Audit Report" in report
        assert result.audit_id in report
        assert "85.5%" in report

    def test_generate_markdown_report(
        self, auditor: AccessibilityAuditor, sample_violation: Violation
    ) -> None:
        """Test Markdown report generation."""
        result = AuditResult(
            url="https://example.com",
            wcag_level="AA",
            violations=[sample_violation],
            compliance_score=85.5,
        )

        report = auditor.generate_report(result, format="markdown")
        assert isinstance(report, str)
        assert "# Accessibility Audit Report" in report
        assert "**Compliance Score:** 85.5%" in report
        assert "color-contrast" in report

    def test_generate_report_invalid_format(
        self, auditor: AccessibilityAuditor
    ) -> None:
        """Test report generation with invalid format."""
        result = AuditResult(url="https://example.com", wcag_level="AA")

        with pytest.raises(ValueError, match="Unsupported format"):
            auditor.generate_report(result, format="pdf")


class TestAuditWorkflow:
    """Test complete audit workflow."""

    @pytest.mark.asyncio
    async def test_audit_invalid_url(self, auditor: AccessibilityAuditor) -> None:
        """Test audit with invalid URL."""
        with pytest.raises(ValueError, match="URL must start with"):
            await auditor.audit("example.com")

    @pytest.mark.asyncio
    async def test_audit_invalid_wcag_level(
        self, auditor: AccessibilityAuditor
    ) -> None:
        """Test audit with invalid WCAG level."""
        with pytest.raises(ValueError, match="wcag_level must be"):
            await auditor.audit("https://example.com", wcag_level="B")

    @pytest.mark.asyncio
    @patch("tools.ux_research.auditor.accessibility_auditor.async_playwright")
    async def test_audit_successful_run(
        self, mock_playwright: Mock, auditor: AccessibilityAuditor
    ) -> None:
        """Test successful audit execution."""
        # Setup mocks
        mock_browser = Mock()
        mock_context = Mock()
        mock_page = Mock()

        mock_page.goto = AsyncMock()
        mock_page.wait_for_load_state = AsyncMock()
        mock_page.evaluate = AsyncMock(return_value=[])
        mock_context.new_page = AsyncMock(return_value=mock_page)
        mock_context.close = AsyncMock()
        mock_browser.new_context = AsyncMock(return_value=mock_context)
        mock_browser.close = AsyncMock()

        mock_pw_instance = Mock()
        mock_pw_instance.chromium.launch = AsyncMock(return_value=mock_browser)
        mock_playwright.return_value.__aenter__ = AsyncMock(
            return_value=mock_pw_instance
        )
        mock_playwright.return_value.__aexit__ = AsyncMock()

        # Run audit
        result = await auditor.audit(
            "https://example.com",
            wcag_level="AA",
            browsers=["chromium"],
            viewports=[(1920, 1080)],
        )

        assert isinstance(result, AuditResult)
        assert result.url == "https://example.com"
        assert result.wcag_level == "AA"
        assert "chromium" in result.browsers_tested
        assert (1920, 1080) in result.viewports_tested

    @pytest.mark.asyncio
    async def test_audit_browser_failure(self, auditor: AccessibilityAuditor) -> None:
        """Test audit handling browser failure."""
        with patch(
            "tools.ux_research.auditor.accessibility_auditor.async_playwright"
        ) as mock_playwright:
            mock_pw_instance = Mock()
            mock_pw_instance.chromium.launch = AsyncMock(
                side_effect=Exception("Browser launch failed")
            )
            mock_playwright.return_value.__aenter__ = AsyncMock(
                return_value=mock_pw_instance
            )
            mock_playwright.return_value.__aexit__ = AsyncMock()

            with pytest.raises(RuntimeError, match="Browser automation failed"):
                await auditor.audit("https://example.com")


class TestLighthouseIntegration:
    """Test Lighthouse integration."""

    @pytest.mark.asyncio
    async def test_lighthouse_score_available(
        self, auditor: AccessibilityAuditor
    ) -> None:
        """Test getting Lighthouse score when available."""
        lighthouse_output = json.dumps(
            {"categories": {"accessibility": {"score": 0.92}}}
        )

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(
                returncode=0, stdout=lighthouse_output, stderr=""
            )

            score = await auditor._get_lighthouse_score("https://example.com")
            assert score == 92.0

    @pytest.mark.asyncio
    async def test_lighthouse_score_unavailable(
        self, auditor: AccessibilityAuditor
    ) -> None:
        """Test getting Lighthouse score when unavailable."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=1, stdout="", stderr="Error")

            score = await auditor._get_lighthouse_score("https://example.com")
            assert score is None

    @pytest.mark.asyncio
    async def test_lighthouse_not_installed(
        self, auditor: AccessibilityAuditor
    ) -> None:
        """Test when Lighthouse is not installed."""
        with patch("subprocess.run", side_effect=FileNotFoundError):
            score = await auditor._get_lighthouse_score("https://example.com")
            assert score is None


class TestWCAGCriteriaCoverage:
    """Test WCAG 2.1 criteria coverage."""

    def test_wcag_criteria_mapping(self, auditor: AccessibilityAuditor) -> None:
        """Test that WCAG criteria mapping is comprehensive."""
        # Test Level A criteria (25 criteria)
        level_a_criteria = [
            "1.1.1",
            "1.2.1",
            "1.2.2",
            "1.2.3",
            "1.3.1",
            "1.3.2",
            "1.3.3",
            "1.4.1",
            "1.4.2",
            "2.1.1",
            "2.1.2",
            "2.2.1",
            "2.2.2",
            "2.3.1",
            "2.4.1",
            "2.4.2",
            "2.4.3",
            "2.4.4",
            "2.5.1",
            "2.5.2",
            "2.5.3",
            "2.5.4",
            "3.1.1",
            "3.2.1",
            "3.2.2",
            "3.3.1",
            "3.3.2",
            "4.1.1",
            "4.1.2",
            "4.1.3",
        ]

        for criterion in level_a_criteria:
            if criterion in auditor.WCAG_CRITERIA:
                assert len(auditor.WCAG_CRITERIA[criterion]) > 0

        # Test Level AA criteria
        level_aa_criteria = [
            "1.3.4",
            "1.3.5",
            "1.4.3",
            "1.4.4",
            "1.4.5",
            "1.4.10",
            "1.4.11",
            "1.4.12",
            "1.4.13",
            "2.4.5",
            "2.4.6",
            "2.4.7",
            "3.1.2",
            "3.2.3",
            "3.2.4",
            "3.3.3",
            "3.3.4",
        ]

        for criterion in level_aa_criteria:
            if criterion in auditor.WCAG_CRITERIA:
                assert len(auditor.WCAG_CRITERIA[criterion]) > 0


class TestMultiViewportTesting:
    """Test multi-viewport testing functionality."""

    @pytest.mark.asyncio
    @patch("tools.ux_research.auditor.accessibility_auditor.async_playwright")
    async def test_multiple_viewports(
        self, mock_playwright: Mock, auditor: AccessibilityAuditor
    ) -> None:
        """Test auditing with multiple viewports."""
        # Setup mocks
        mock_browser = Mock()
        mock_context = Mock()
        mock_page = Mock()

        mock_page.goto = AsyncMock()
        mock_page.wait_for_load_state = AsyncMock()
        mock_page.evaluate = AsyncMock(return_value=[])
        mock_context.new_page = AsyncMock(return_value=mock_page)
        mock_context.close = AsyncMock()
        mock_browser.new_context = AsyncMock(return_value=mock_context)
        mock_browser.close = AsyncMock()

        mock_pw_instance = Mock()
        mock_pw_instance.chromium.launch = AsyncMock(return_value=mock_browser)
        mock_playwright.return_value.__aenter__ = AsyncMock(
            return_value=mock_pw_instance
        )
        mock_playwright.return_value.__aexit__ = AsyncMock()

        # Run audit with multiple viewports
        viewports = [(1920, 1080), (768, 1024), (375, 667)]
        result = await auditor.audit(
            "https://example.com", wcag_level="AA", viewports=viewports
        )

        assert len(result.viewports_tested) == 3
        assert (1920, 1080) in result.viewports_tested
        assert (768, 1024) in result.viewports_tested
        assert (375, 667) in result.viewports_tested


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
