"""
Tests for Remediation Guide Generator module.
"""

import json
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from guide_generator import (CodeExample, RemediationGuide, RemediationStep,
                             Severity, Violation, WCAGLevel)


class TestDataClasses(unittest.TestCase):
    """Test data classes."""

    def test_violation_creation(self):
        """Test creating a Violation object."""
        violation = Violation(
            id="image-alt",
            description="Images must have alternate text",
            impact="critical",
            wcag_criteria="1.1.1",
            wcag_level=WCAGLevel.A,
            severity=Severity.CRITICAL,
            element='<img src="test.jpg">',
        )

        self.assertEqual(violation.id, "image-alt")
        self.assertEqual(violation.severity, Severity.CRITICAL)
        self.assertEqual(violation.wcag_level, WCAGLevel.A)

    def test_code_example_creation(self):
        """Test creating a CodeExample object."""
        example = CodeExample(
            before='<img src="test.jpg">',
            after='<img src="test.jpg" alt="Test image">',
            explanation="Added alt text",
            language="html",
        )

        self.assertEqual(example.language, "html")
        self.assertIn("alt=", example.after)

    def test_remediation_step_creation(self):
        """Test creating a RemediationStep object."""
        violation = Violation(
            id="test",
            description="Test",
            impact="moderate",
            wcag_criteria="1.1.1",
            wcag_level=WCAGLevel.A,
            severity=Severity.MODERATE,
            element="<div>",
        )

        step = RemediationStep(
            violation=violation,
            steps=["Step 1", "Step 2"],
            code_example=None,
            estimated_effort="1 hour",
            priority_score=75,
            alternatives=["Alt 1"],
            testing_guidance="Test with screen reader",
            resources=["https://example.com"],
        )

        self.assertEqual(len(step.steps), 2)
        self.assertEqual(step.priority_score, 75)


class TestRemediationGuide(unittest.TestCase):
    """Test RemediationGuide class."""

    def setUp(self):
        """Set up test fixtures."""
        self.guide = RemediationGuide()

    def test_initialization(self):
        """Test guide initialization."""
        self.assertIsNotNone(self.guide.remediation_db)
        self.assertGreater(len(self.guide.remediation_db), 0)
        self.assertIn("image-alt", self.guide.remediation_db)

    def test_remediation_database_structure(self):
        """Test remediation database has correct structure."""
        for violation_id, data in self.guide.remediation_db.items():
            self.assertIn("steps", data)
            self.assertIn("alternatives", data)
            self.assertIn("testing", data)
            self.assertIn("resources", data)
            self.assertIsInstance(data["steps"], list)
            self.assertIsInstance(data["alternatives"], list)

    def test_generate_remediation_known_violation(self):
        """Test generating remediation for known violation."""
        violation = Violation(
            id="image-alt",
            description="Images must have alternate text",
            impact="critical",
            wcag_criteria="1.1.1",
            wcag_level=WCAGLevel.A,
            severity=Severity.CRITICAL,
            element='<img src="test.jpg">',
        )

        remediation = self.guide.generate_remediation(violation)

        self.assertIsInstance(remediation, RemediationStep)
        self.assertGreater(len(remediation.steps), 0)
        self.assertIsNotNone(remediation.code_example)
        self.assertGreater(remediation.priority_score, 0)
        self.assertIsNotNone(remediation.estimated_effort)

    def test_generate_remediation_unknown_violation(self):
        """Test generating remediation for unknown violation."""
        violation = Violation(
            id="unknown-violation",
            description="Unknown issue",
            impact="moderate",
            wcag_criteria="2.4.1",
            wcag_level=WCAGLevel.AA,
            severity=Severity.MODERATE,
            element="<div>",
        )

        remediation = self.guide.generate_remediation(violation)

        self.assertIsInstance(remediation, RemediationStep)
        self.assertGreater(len(remediation.steps), 0)
        self.assertGreater(len(remediation.resources), 0)

    def test_calculate_priority(self):
        """Test priority calculation."""
        critical_violation = Violation(
            id="test",
            description="Test",
            impact="critical",
            wcag_criteria="1.1.1",
            wcag_level=WCAGLevel.A,
            severity=Severity.CRITICAL,
            element="<div>",
        )

        minor_violation = Violation(
            id="test",
            description="Test",
            impact="minor",
            wcag_criteria="1.1.1",
            wcag_level=WCAGLevel.AAA,
            severity=Severity.MINOR,
            element="<div>",
        )

        critical_priority = self.guide._calculate_priority(critical_violation)
        minor_priority = self.guide._calculate_priority(minor_violation)

        self.assertGreater(critical_priority, minor_priority)

    def test_prioritize_violations(self):
        """Test prioritizing violations."""
        violations = [
            Violation(
                id="minor",
                description="Minor issue",
                impact="minor",
                wcag_criteria="1.1.1",
                wcag_level=WCAGLevel.AAA,
                severity=Severity.MINOR,
                element="<div>",
            ),
            Violation(
                id="critical",
                description="Critical issue",
                impact="critical",
                wcag_criteria="1.1.1",
                wcag_level=WCAGLevel.A,
                severity=Severity.CRITICAL,
                element="<div>",
            ),
            Violation(
                id="moderate",
                description="Moderate issue",
                impact="moderate",
                wcag_criteria="1.1.1",
                wcag_level=WCAGLevel.AA,
                severity=Severity.MODERATE,
                element="<div>",
            ),
        ]

        prioritized = self.guide.prioritize_violations(violations)

        self.assertEqual(len(prioritized), 3)
        self.assertEqual(prioritized[0].severity, Severity.CRITICAL)
        self.assertEqual(prioritized[-1].severity, Severity.MINOR)

    def test_generate_code_example(self):
        """Test generating code example."""
        violation = Violation(
            id="color-contrast",
            description="Contrast issue",
            impact="serious",
            wcag_criteria="1.4.3",
            wcag_level=WCAGLevel.AA,
            severity=Severity.SERIOUS,
            element="<div>",
        )

        example = self.guide.generate_code_example(violation)

        self.assertIsNotNone(example)
        self.assertIsInstance(example, CodeExample)
        self.assertIsNotNone(example.before)
        self.assertIsNotNone(example.after)

    def test_generate_code_example_unknown(self):
        """Test generating code example for unknown violation."""
        violation = Violation(
            id="unknown",
            description="Unknown",
            impact="moderate",
            wcag_criteria="1.1.1",
            wcag_level=WCAGLevel.A,
            severity=Severity.MODERATE,
            element="<div>",
        )

        example = self.guide.generate_code_example(violation)
        self.assertIsNone(example)

    @patch("requests.post")
    def test_create_github_issue(self, mock_post):
        """Test creating GitHub issue."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "html_url": "https://github.com/owner/repo/issues/1"
        }
        mock_post.return_value = mock_response

        violation = Violation(
            id="image-alt",
            description="Images must have alternate text",
            impact="critical",
            wcag_criteria="1.1.1",
            wcag_level=WCAGLevel.A,
            severity=Severity.CRITICAL,
            element='<img src="test.jpg">',
        )

        issue_url = self.guide.create_github_issue(
            violation, "owner/repo", "fake_token"
        )

        self.assertEqual(issue_url, "https://github.com/owner/repo/issues/1")
        mock_post.assert_called_once()

        # Verify call parameters
        call_args = mock_post.call_args
        self.assertIn("repos/owner/repo/issues", call_args[0][0])
        self.assertIn("Authorization", call_args[1]["headers"])

    @patch("requests.post")
    def test_create_jira_issue(self, mock_post):
        """Test creating Jira issue."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"key": "PROJ-123"}
        mock_post.return_value = mock_response

        violation = Violation(
            id="button-name",
            description="Buttons must have accessible names",
            impact="serious",
            wcag_criteria="4.1.2",
            wcag_level=WCAGLevel.A,
            severity=Severity.SERIOUS,
            element="<button>",
        )

        issue_key = self.guide.create_jira_issue(
            violation,
            "https://jira.example.com",
            "PROJ",
            ("user", "token"),
        )

        self.assertEqual(issue_key, "PROJ-123")
        mock_post.assert_called_once()

    def test_generate_batch_report(self):
        """Test generating batch report."""
        violations = [
            Violation(
                id="image-alt",
                description="Images must have alternate text",
                impact="critical",
                wcag_criteria="1.1.1",
                wcag_level=WCAGLevel.A,
                severity=Severity.CRITICAL,
                element='<img src="test.jpg">',
            ),
            Violation(
                id="color-contrast",
                description="Contrast issue",
                impact="serious",
                wcag_criteria="1.4.3",
                wcag_level=WCAGLevel.AA,
                severity=Severity.SERIOUS,
                element="<div>",
            ),
        ]

        report = self.guide.generate_batch_report(violations)

        self.assertIn("generated_at", report)
        self.assertIn("summary", report)
        self.assertIn("remediations", report)
        self.assertEqual(report["summary"]["total_violations"], 2)
        self.assertEqual(len(report["remediations"]), 2)

    def test_export_report(self):
        """Test exporting report to file."""
        violations = [
            Violation(
                id="label",
                description="Form labels required",
                impact="serious",
                wcag_criteria="1.3.1",
                wcag_level=WCAGLevel.A,
                severity=Severity.SERIOUS,
                element="<input>",
            )
        ]

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f:
            temp_file = f.name

        try:
            self.guide.export_report(violations, temp_file)

            # Verify file was created and contains valid JSON
            with open(temp_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            self.assertIn("summary", data)
            self.assertIn("remediations", data)
            self.assertEqual(data["summary"]["total_violations"], 1)
        finally:
            import os

            os.unlink(temp_file)


class TestKnownViolations(unittest.TestCase):
    """Test remediation for all known violation types."""

    def setUp(self):
        """Set up test fixtures."""
        self.guide = RemediationGuide()

    def test_image_alt_remediation(self):
        """Test image alt remediation."""
        violation = Violation(
            id="image-alt",
            description="Images must have alternate text",
            impact="critical",
            wcag_criteria="1.1.1",
            wcag_level=WCAGLevel.A,
            severity=Severity.CRITICAL,
            element='<img src="test.jpg">',
        )

        remediation = self.guide.generate_remediation(violation)
        self.assertIn("alt", remediation.code_example.after)

    def test_color_contrast_remediation(self):
        """Test color contrast remediation."""
        violation = Violation(
            id="color-contrast",
            description="Contrast issue",
            impact="serious",
            wcag_criteria="1.4.3",
            wcag_level=WCAGLevel.AA,
            severity=Severity.SERIOUS,
            element="<div>",
        )

        remediation = self.guide.generate_remediation(violation)
        self.assertIn("contrast", remediation.code_example.explanation.lower())

    def test_button_name_remediation(self):
        """Test button name remediation."""
        violation = Violation(
            id="button-name",
            description="Buttons must have accessible names",
            impact="serious",
            wcag_criteria="4.1.2",
            wcag_level=WCAGLevel.A,
            severity=Severity.SERIOUS,
            element="<button>",
        )

        remediation = self.guide.generate_remediation(violation)
        self.assertIn("aria-label", remediation.code_example.after)

    def test_label_remediation(self):
        """Test form label remediation."""
        violation = Violation(
            id="label",
            description="Form labels required",
            impact="serious",
            wcag_criteria="1.3.1",
            wcag_level=WCAGLevel.A,
            severity=Severity.SERIOUS,
            element="<input>",
        )

        remediation = self.guide.generate_remediation(violation)
        self.assertIn("for=", remediation.code_example.after)

    def test_heading_order_remediation(self):
        """Test heading order remediation."""
        violation = Violation(
            id="heading-order",
            description="Headings must be in order",
            impact="moderate",
            wcag_criteria="1.3.1",
            wcag_level=WCAGLevel.A,
            severity=Severity.MODERATE,
            element="<h3>",
        )

        remediation = self.guide.generate_remediation(violation)
        self.assertIn("h2", remediation.code_example.after)


class TestIntegration(unittest.TestCase):
    """Integration tests for remediation guide."""

    def setUp(self):
        """Set up test fixtures."""
        self.guide = RemediationGuide()

    def test_full_remediation_workflow(self):
        """Test complete workflow of generating remediation."""
        violations = [
            Violation(
                id="image-alt",
                description="Images must have alternate text",
                impact="critical",
                wcag_criteria="1.1.1",
                wcag_level=WCAGLevel.A,
                severity=Severity.CRITICAL,
                element='<img src="logo.jpg">',
            ),
            Violation(
                id="color-contrast",
                description="Insufficient color contrast",
                impact="serious",
                wcag_criteria="1.4.3",
                wcag_level=WCAGLevel.AA,
                severity=Severity.SERIOUS,
                element='<p style="color: #999;">',
            ),
            Violation(
                id="label",
                description="Form inputs need labels",
                impact="serious",
                wcag_criteria="1.3.1",
                wcag_level=WCAGLevel.A,
                severity=Severity.SERIOUS,
                element='<input type="text">',
            ),
        ]

        # Prioritize
        prioritized = self.guide.prioritize_violations(violations)
        self.assertEqual(len(prioritized), 3)

        # Generate remediations
        remediations = []
        for violation in prioritized:
            remediation = self.guide.generate_remediation(violation)
            self.assertIsNotNone(remediation)
            remediations.append(remediation)

        # Generate batch report
        report = self.guide.generate_batch_report(violations)
        self.assertEqual(report["summary"]["total_violations"], 3)

    def test_severity_based_effort_estimation(self):
        """Test that effort estimation varies by severity."""
        violations = [
            Violation(
                id="test1",
                description="Test",
                impact="critical",
                wcag_criteria="1.1.1",
                wcag_level=WCAGLevel.A,
                severity=Severity.CRITICAL,
                element="<div>",
            ),
            Violation(
                id="test2",
                description="Test",
                impact="minor",
                wcag_criteria="1.1.1",
                wcag_level=WCAGLevel.AAA,
                severity=Severity.MINOR,
                element="<div>",
            ),
        ]

        critical_rem = self.guide.generate_remediation(violations[0])
        minor_rem = self.guide.generate_remediation(violations[1])

        # Critical should have more estimated effort
        self.assertNotEqual(critical_rem.estimated_effort, minor_rem.estimated_effort)


if __name__ == "__main__":
    unittest.main()
