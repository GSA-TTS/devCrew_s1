"""Tests for Usability Validator module."""

import json
import tempfile
from pathlib import Path
from typing import Any, Dict

import pytest
import yaml

from .usability_validator import (FormIssue, HeuristicEvaluation,
                                  HeuristicResult, MobileIssue,
                                  ReadabilityScore, UsabilityValidator)


class TestUsabilityValidator:
    """Test cases for UsabilityValidator class."""

    @pytest.fixture
    def validator(self) -> UsabilityValidator:
        """Create validator instance."""
        return UsabilityValidator()

    @pytest.fixture
    def sample_page_data(self) -> Dict[str, Any]:
        """Create sample page data for testing."""
        return {
            "loading_indicators": ["spinner"],
            "progress_bars": ["checkout-progress"],
            "status_messages": ["success-message"],
            "labels": ["Email Address", "Password", "Username"],
            "button_texts": ["Submit", "Cancel", "Save"],
            "button_classes": ["btn-primary", "btn-secondary"],
            "undo_buttons": ["undo"],
            "cancel_buttons": ["cancel"],
            "confirmation_dialogs": ["delete-confirm"],
            "form_validations": ["email-validation"],
            "destructive_actions": [{"name": "delete", "has_confirmation": True}],
            "navigation_visible": True,
            "help_texts": ["tooltip-help"],
            "autocomplete_fields": ["email"],
            "keyboard_shortcuts": ["ctrl+s"],
            "search_available": True,
            "bulk_actions": ["bulk-delete"],
            "word_count": 500,
            "whitespace_ratio": 0.4,
            "ui_elements_count": 30,
            "error_messages": ["Please enter a valid email address"],
            "error_suggestions": ["Try: name@example.com"],
            "help_links": ["/help"],
            "contextual_help": ["field-help"],
            "help_search": True,
        }

    @pytest.fixture
    def custom_checklist(self) -> Dict[str, Any]:
        """Create custom checklist for testing."""
        return {
            "items": [
                {
                    "name": "Custom Check 1",
                    "default_rating": 5.0,
                    "checks": [
                        {
                            "type": "exists",
                            "field": "loading_indicators",
                            "issue": "Missing loading indicators",
                            "recommendation": "Add loading spinners",
                            "penalty": 1.0,
                        }
                    ],
                },
                {
                    "name": "Custom Check 2",
                    "default_rating": 5.0,
                    "checks": [
                        {
                            "type": "count_greater",
                            "field": "help_texts",
                            "threshold": 0,
                            "issue": "Not enough help text",
                            "recommendation": "Add more tooltips",
                            "penalty": 0.5,
                        }
                    ],
                },
            ]
        }

    def test_initialization(self, validator: UsabilityValidator) -> None:
        """Test validator initialization."""
        assert validator.config["min_touch_target_size"] == 44
        assert validator.config["max_form_fields"] == 10
        assert validator.config["target_reading_level"] == 8
        assert validator.config["enable_playwright"] is False

    def test_custom_initialization(self) -> None:
        """Test validator with custom config."""
        config = {
            "min_touch_target_size": 48,
            "max_form_fields": 15,
        }
        validator = UsabilityValidator(config)
        assert validator.config["min_touch_target_size"] == 48
        assert validator.config["max_form_fields"] == 15

    def test_load_custom_checklist(
        self, validator: UsabilityValidator, custom_checklist: Dict[str, Any]
    ) -> None:
        """Test loading custom checklist from YAML."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(custom_checklist, f)
            temp_path = f.name

        try:
            validator.load_custom_checklist(temp_path, "test-checklist")
            assert "test-checklist" in validator.custom_checklists
            loaded = validator.custom_checklists["test-checklist"]
            assert loaded == custom_checklist
        finally:
            Path(temp_path).unlink()

    def test_load_custom_checklist_file_not_found(
        self, validator: UsabilityValidator
    ) -> None:
        """Test loading checklist with non-existent file."""
        with pytest.raises(FileNotFoundError):
            validator.load_custom_checklist("/nonexistent/file.yaml")

    def test_evaluate_nielsen_heuristics(
        self,
        validator: UsabilityValidator,
        sample_page_data: Dict[str, Any],
    ) -> None:
        """Test Nielsen's 10 heuristics evaluation."""
        evaluation = validator.evaluate_heuristics(
            url="https://example.com",
            heuristics="nielsen-10",
            page_data=sample_page_data,
        )

        assert isinstance(evaluation, HeuristicEvaluation)
        assert evaluation.url == "https://example.com"
        assert len(evaluation.heuristics) == 10
        assert evaluation.overall_score > 0
        assert evaluation.severity in ["low", "moderate", "high", "critical"]

    def test_evaluate_custom_checklist(
        self,
        validator: UsabilityValidator,
        sample_page_data: Dict[str, Any],
        custom_checklist: Dict[str, Any],
    ) -> None:
        """Test custom checklist evaluation."""
        evaluation = validator.evaluate_heuristics(
            url="https://example.com",
            heuristics="custom",
            custom_checklist=custom_checklist,
            page_data=sample_page_data,
        )

        assert isinstance(evaluation, HeuristicEvaluation)
        assert len(evaluation.heuristics) == 2
        assert evaluation.custom_checklist == "custom"

    def test_evaluate_unknown_heuristic_set(
        self, validator: UsabilityValidator
    ) -> None:
        """Test evaluation with unknown heuristic set."""
        with pytest.raises(ValueError, match="Unknown heuristic set"):
            validator.evaluate_heuristics(
                url="https://example.com",
                heuristics="unknown-set",
            )

    def test_check_visibility_status(self, validator: UsabilityValidator) -> None:
        """Test visibility of system status heuristic."""
        # Good visibility
        page_data = {
            "loading_indicators": ["spinner"],
            "progress_bars": ["progress"],
            "status_messages": ["success"],
        }
        result = validator._check_visibility_status(page_data)
        assert result.rating == 5.0
        assert result.severity == "low"

        # Missing indicators
        page_data = {
            "loading_indicators": [],
            "progress_bars": [],
            "status_messages": [],
        }
        result = validator._check_visibility_status(page_data)
        assert result.rating < 5.0
        assert len(result.issues) > 0
        assert len(result.recommendations) > 0

    def test_check_match_real_world(self, validator: UsabilityValidator) -> None:
        """Test match between system and real world."""
        # Good labels
        page_data = {
            "labels": ["Name", "Email", "Phone"],
            "button_texts": ["Create Account", "Sign In"],
        }
        result = validator._check_match_real_world(page_data)
        assert result.rating == 5.0

        # Too much jargon
        page_data = {
            "labels": ["API Key", "JSON Config", "HTTP URL", "XML Data"],
            "button_texts": ["Submit", "Ok"],
        }
        result = validator._check_match_real_world(page_data)
        assert result.rating < 5.0
        assert any("jargon" in issue.lower() for issue in result.issues)

    def test_check_user_control(self, validator: UsabilityValidator) -> None:
        """Test user control and freedom."""
        # Good control
        page_data = {
            "undo_buttons": ["undo"],
            "cancel_buttons": ["cancel"],
            "confirmation_dialogs": ["confirm"],
        }
        result = validator._check_user_control(page_data)
        assert result.rating == 5.0

        # Missing controls
        page_data = {
            "undo_buttons": [],
            "cancel_buttons": [],
            "confirmation_dialogs": [],
        }
        result = validator._check_user_control(page_data)
        assert result.rating < 5.0
        assert len(result.issues) == 3

    def test_check_consistency(self, validator: UsabilityValidator) -> None:
        """Test consistency and standards."""
        # Good consistency
        page_data = {
            "button_classes": ["btn-primary", "btn-secondary"],
            "labels": ["Save Changes"],
            "button_texts": ["Save Changes"],
        }
        result = validator._check_consistency(page_data)
        assert result.rating == 5.0

        # Too many styles
        page_data = {
            "button_classes": [
                "btn1",
                "btn2",
                "btn3",
                "btn4",
                "btn5",
                "btn6",
            ],
            "labels": ["Save"],
            "button_texts": ["Submit"],
        }
        result = validator._check_consistency(page_data)
        assert result.rating < 5.0

    def test_check_error_prevention(self, validator: UsabilityValidator) -> None:
        """Test error prevention."""
        # Good prevention
        page_data = {
            "form_validations": ["email-val"],
            "destructive_actions": [{"name": "delete", "has_confirmation": True}],
        }
        result = validator._check_error_prevention(page_data)
        assert result.rating == 5.0

        # Missing prevention
        page_data = {
            "form_validations": [],
            "destructive_actions": [{"name": "delete", "has_confirmation": False}],
        }
        result = validator._check_error_prevention(page_data)
        assert result.rating < 5.0

    def test_check_recognition(self, validator: UsabilityValidator) -> None:
        """Test recognition rather than recall."""
        # Good recognition
        page_data = {
            "navigation_visible": True,
            "help_texts": ["tooltip"],
            "autocomplete_fields": ["email"],
        }
        result = validator._check_recognition(page_data)
        assert result.rating == 5.0

        # Poor recognition
        page_data = {
            "navigation_visible": False,
            "help_texts": [],
            "autocomplete_fields": [],
        }
        result = validator._check_recognition(page_data)
        assert result.rating < 5.0

    def test_check_flexibility(self, validator: UsabilityValidator) -> None:
        """Test flexibility and efficiency."""
        # Good flexibility
        page_data = {
            "keyboard_shortcuts": ["ctrl+s"],
            "search_available": True,
            "bulk_actions": ["bulk-delete"],
        }
        result = validator._check_flexibility(page_data)
        assert result.rating == 5.0

        # Poor flexibility
        page_data = {
            "keyboard_shortcuts": [],
            "search_available": False,
            "bulk_actions": [],
        }
        result = validator._check_flexibility(page_data)
        assert result.rating < 5.0

    def test_check_aesthetic(self, validator: UsabilityValidator) -> None:
        """Test aesthetic and minimalist design."""
        # Good design
        page_data = {
            "word_count": 500,
            "whitespace_ratio": 0.4,
            "ui_elements_count": 30,
        }
        result = validator._check_aesthetic(page_data)
        assert result.rating == 5.0

        # Cluttered design
        page_data = {
            "word_count": 2000,
            "whitespace_ratio": 0.2,
            "ui_elements_count": 100,
        }
        result = validator._check_aesthetic(page_data)
        assert result.rating < 5.0

    def test_check_error_recovery(self, validator: UsabilityValidator) -> None:
        """Test error recovery."""
        # Good error messages
        page_data = {
            "error_messages": ["Please enter a valid email address"],
            "error_suggestions": ["Try: name@example.com"],
        }
        result = validator._check_error_recovery(page_data)
        assert result.rating == 5.0

        # Generic errors
        page_data = {
            "error_messages": ["Error", "Invalid", "Failed"],
            "error_suggestions": [],
        }
        result = validator._check_error_recovery(page_data)
        assert result.rating < 5.0

    def test_check_documentation(self, validator: UsabilityValidator) -> None:
        """Test help and documentation."""
        # Good documentation
        page_data = {
            "help_links": ["/help"],
            "contextual_help": ["tooltip"],
            "help_search": True,
        }
        result = validator._check_documentation(page_data)
        assert result.rating == 5.0

        # Missing documentation
        page_data = {
            "help_links": [],
            "contextual_help": [],
            "help_search": False,
        }
        result = validator._check_documentation(page_data)
        assert result.rating < 5.0

    def test_evaluate_check_exists(self, validator: UsabilityValidator) -> None:
        """Test evaluate_check with 'exists' type."""
        check = {"type": "exists", "field": "loading_indicators"}
        page_data = {"loading_indicators": ["spinner"]}
        assert validator._evaluate_check(check, page_data) is True

        page_data = {"loading_indicators": []}
        assert validator._evaluate_check(check, page_data) is False

    def test_evaluate_check_count_greater(self, validator: UsabilityValidator) -> None:
        """Test evaluate_check with 'count_greater' type."""
        check = {
            "type": "count_greater",
            "field": "buttons",
            "threshold": 2,
        }
        page_data = {"buttons": ["btn1", "btn2", "btn3"]}
        assert validator._evaluate_check(check, page_data) is True

        page_data = {"buttons": ["btn1"]}
        assert validator._evaluate_check(check, page_data) is False

    def test_evaluate_check_count_less(self, validator: UsabilityValidator) -> None:
        """Test evaluate_check with 'count_less' type."""
        check = {
            "type": "count_less",
            "field": "errors",
            "threshold": 5,
        }
        page_data = {"errors": ["err1", "err2"]}
        assert validator._evaluate_check(check, page_data) is True

        page_data = {"errors": ["e1", "e2", "e3", "e4", "e5", "e6"]}
        assert validator._evaluate_check(check, page_data) is False

    def test_evaluate_check_equals(self, validator: UsabilityValidator) -> None:
        """Test evaluate_check with 'equals' type."""
        check = {
            "type": "equals",
            "field": "theme",
            "expected": "dark",
        }
        page_data = {"theme": "dark"}
        assert validator._evaluate_check(check, page_data) is True

        page_data = {"theme": "light"}
        assert validator._evaluate_check(check, page_data) is False

    def test_analyze_forms(self, validator: UsabilityValidator) -> None:
        """Test form analysis."""
        page_data = {
            "forms": [
                {
                    "id": "login-form",
                    "fields": [
                        {
                            "name": "email",
                            "has_label": True,
                            "has_validation": True,
                            "required": True,
                            "has_error_message": True,
                            "has_placeholder": False,
                        },
                        {
                            "name": "password",
                            "has_label": False,
                            "has_validation": False,
                            "required": True,
                            "has_error_message": False,
                            "has_placeholder": True,
                        },
                    ],
                }
            ]
        }

        issues = validator.analyze_forms(page_data)
        assert len(issues) > 0
        assert any(issue.issue_type == "missing_label" for issue in issues)
        has_validation_issue = any(
            issue.issue_type == "missing_validation" for issue in issues
        )
        assert has_validation_issue
        assert any(issue.issue_type == "missing_error_message" for issue in issues)
        assert any(issue.issue_type == "placeholder_as_label" for issue in issues)

    def test_analyze_forms_too_many_fields(self, validator: UsabilityValidator) -> None:
        """Test form with too many fields."""
        fields = [
            {
                "name": f"field{i}",
                "has_label": True,
                "has_validation": True,
                "required": False,
                "has_error_message": True,
                "has_placeholder": False,
            }
            for i in range(15)
        ]

        page_data = {
            "forms": [
                {
                    "id": "long-form",
                    "fields": fields,
                }
            ]
        }

        issues = validator.analyze_forms(page_data)
        assert any(issue.issue_type == "too_many_fields" for issue in issues)

    def test_check_mobile_usability(self, validator: UsabilityValidator) -> None:
        """Test mobile usability checks."""
        page_data = {
            "has_viewport_meta": False,
            "interactive_elements": [
                {"selector": "button.small", "size": 30},
                {"selector": "a.link", "size": 48},
            ],
            "has_horizontal_scroll": True,
            "has_tap_delay": True,
        }

        issues = validator.check_mobile_usability(page_data)
        assert len(issues) > 0
        assert any(issue.issue_type == "missing_viewport_meta" for issue in issues)
        has_touch_issue = any(
            issue.issue_type == "small_touch_target" for issue in issues
        )
        assert has_touch_issue
        assert any(issue.issue_type == "horizontal_scroll" for issue in issues)
        assert any(issue.issue_type == "tap_delay" for issue in issues)

    def test_check_mobile_usability_good(self, validator: UsabilityValidator) -> None:
        """Test mobile usability with good practices."""
        page_data = {
            "has_viewport_meta": True,
            "interactive_elements": [
                {"selector": "button.large", "size": 48},
                {"selector": "a.link", "size": 50},
            ],
            "has_horizontal_scroll": False,
            "has_tap_delay": False,
        }

        issues = validator.check_mobile_usability(page_data)
        assert len(issues) == 0

    def test_calculate_readability(self, validator: UsabilityValidator) -> None:
        """Test readability calculation."""
        # Simple text (low reading level)
        simple_text = (
            "The cat sat on the mat. The dog ran in the park. "
            "The sun is bright today."
        )
        score = validator.calculate_readability(simple_text)
        assert isinstance(score, ReadabilityScore)
        assert score.flesch_reading_ease > 0
        assert score.flesch_kincaid_grade >= 0
        assert score.reading_level in [
            "Elementary",
            "Middle School",
            "High School",
            "College",
            "Graduate",
        ]

        # Complex text (high reading level)
        complex_text = (
            "The implementation of sophisticated algorithmic "
            "methodologies necessitates comprehensive evaluation of "
            "multifaceted architectural paradigms, incorporating "
            "synergistic optimization strategies to facilitate enhanced "
            "computational efficiency and scalability across distributed "
            "heterogeneous systems."
        )
        score = validator.calculate_readability(complex_text)
        assert score.flesch_kincaid_grade > 10

    def test_determine_reading_level(self, validator: UsabilityValidator) -> None:
        """Test reading level determination."""
        assert validator._determine_reading_level(4) == "Elementary"
        assert validator._determine_reading_level(7) == "Middle School"
        assert validator._determine_reading_level(10) == "High School"
        assert validator._determine_reading_level(14) == "College"
        assert validator._determine_reading_level(17) == "Graduate"

    def test_calculate_severity(self, validator: UsabilityValidator) -> None:
        """Test severity calculation."""
        assert validator._calculate_severity(5.0) == "low"
        assert validator._calculate_severity(4.5) == "low"
        assert validator._calculate_severity(4.0) == "moderate"
        assert validator._calculate_severity(3.0) == "high"
        assert validator._calculate_severity(2.0) == "critical"
        assert validator._calculate_severity(1.0) == "critical"

    def test_calculate_overall_severity(self, validator: UsabilityValidator) -> None:
        """Test overall severity calculation."""
        results = [
            HeuristicResult(heuristic="H1", rating=5.0, severity="low"),
            HeuristicResult(heuristic="H2", rating=4.0, severity="moderate"),
            HeuristicResult(heuristic="H3", rating=3.0, severity="high"),
        ]
        assert validator._calculate_overall_severity(results) == "high"

        results = [
            HeuristicResult(heuristic="H1", rating=5.0, severity="low"),
            HeuristicResult(heuristic="H2", rating=4.5, severity="low"),
        ]
        assert validator._calculate_overall_severity(results) == "low"

        results = [
            HeuristicResult(heuristic="H1", rating=2.0, severity="critical"),
        ]
        assert validator._calculate_overall_severity(results) == "critical"

    def test_generate_json_report(
        self,
        validator: UsabilityValidator,
        sample_page_data: Dict[str, Any],
    ) -> None:
        """Test JSON report generation."""
        evaluation = validator.evaluate_heuristics(
            url="https://example.com",
            heuristics="nielsen-10",
            page_data=sample_page_data,
        )

        report = validator.generate_evaluation_report(evaluation, format="json")
        assert isinstance(report, str)

        # Validate JSON structure
        data = json.loads(report)
        assert "evaluation_id" in data
        assert "url" in data
        assert "heuristics" in data
        assert "overall_score" in data
        assert len(data["heuristics"]) == 10

    def test_generate_text_report(
        self,
        validator: UsabilityValidator,
        sample_page_data: Dict[str, Any],
    ) -> None:
        """Test text report generation."""
        evaluation = validator.evaluate_heuristics(
            url="https://example.com",
            heuristics="nielsen-10",
            page_data=sample_page_data,
        )

        report = validator.generate_evaluation_report(evaluation, format="text")
        assert isinstance(report, str)
        assert "USABILITY EVALUATION REPORT" in report
        assert "https://example.com" in report
        assert "Overall Score" in report

    def test_generate_html_report(
        self,
        validator: UsabilityValidator,
        sample_page_data: Dict[str, Any],
    ) -> None:
        """Test HTML report generation."""
        evaluation = validator.evaluate_heuristics(
            url="https://example.com",
            heuristics="nielsen-10",
            page_data=sample_page_data,
        )

        report = validator.generate_evaluation_report(evaluation, format="html")
        assert isinstance(report, str)
        assert "<!DOCTYPE html>" in report
        assert "Usability Evaluation Report" in report
        assert "https://example.com" in report

    def test_generate_report_invalid_format(
        self,
        validator: UsabilityValidator,
        sample_page_data: Dict[str, Any],
    ) -> None:
        """Test report generation with invalid format."""
        evaluation = validator.evaluate_heuristics(
            url="https://example.com",
            heuristics="nielsen-10",
            page_data=sample_page_data,
        )

        with pytest.raises(ValueError, match="Unsupported format"):
            validator.generate_evaluation_report(evaluation, format="xml")

    def test_heuristic_result_to_dict(self) -> None:
        """Test HeuristicResult to_dict method."""
        result = HeuristicResult(
            heuristic="Test Heuristic",
            rating=4.5,
            issues=["Issue 1"],
            recommendations=["Fix 1"],
            severity="moderate",
        )

        data = result.to_dict()
        assert data["heuristic"] == "Test Heuristic"
        assert data["rating"] == 4.5
        assert data["issues"] == ["Issue 1"]
        assert data["recommendations"] == ["Fix 1"]
        assert data["severity"] == "moderate"

    def test_form_issue_to_dict(self) -> None:
        """Test FormIssue to_dict method."""
        issue = FormIssue(
            form_id="test-form",
            field_name="email",
            issue_type="missing_label",
            description="No label",
            severity="high",
            recommendation="Add label",
        )

        data = issue.to_dict()
        assert data["form_id"] == "test-form"
        assert data["field_name"] == "email"
        assert data["issue_type"] == "missing_label"

    def test_mobile_issue_to_dict(self) -> None:
        """Test MobileIssue to_dict method."""
        issue = MobileIssue(
            issue_type="small_touch_target",
            element="button.small",
            description="Target too small",
            severity="moderate",
            recommendation="Increase size",
        )

        data = issue.to_dict()
        assert data["issue_type"] == "small_touch_target"
        assert data["element"] == "button.small"
        assert data["severity"] == "moderate"

    def test_readability_score_to_dict(self) -> None:
        """Test ReadabilityScore to_dict method."""
        score = ReadabilityScore(
            flesch_reading_ease=65.0,
            flesch_kincaid_grade=8.0,
            gunning_fog=10.0,
            smog_index=9.0,
            automated_readability_index=8.5,
            coleman_liau_index=8.2,
            reading_level="Middle School",
            recommendation="Good readability",
        )

        data = score.to_dict()
        assert data["flesch_reading_ease"] == 65.0
        assert data["flesch_kincaid_grade"] == 8.0
        assert data["reading_level"] == "Middle School"

    def test_heuristic_evaluation_to_dict(self, validator: UsabilityValidator) -> None:
        """Test HeuristicEvaluation to_dict method."""
        evaluation = HeuristicEvaluation(
            evaluation_id="test-123",
            url="https://example.com",
            timestamp="2025-01-15T10:00:00",
            heuristics=[
                HeuristicResult(heuristic="Test", rating=5.0, severity="low"),
            ],
            overall_score=5.0,
            severity="low",
        )

        data = evaluation.to_dict()
        assert data["evaluation_id"] == "test-123"
        assert data["url"] == "https://example.com"
        assert len(data["heuristics"]) == 1
        assert data["overall_score"] == 5.0


class TestIntegration:
    """Integration tests for complete workflows."""

    def test_complete_evaluation_workflow(self) -> None:
        """Test complete evaluation workflow."""
        validator = UsabilityValidator()

        # Create comprehensive page data
        page_data = {
            "loading_indicators": ["spinner"],
            "progress_bars": ["checkout"],
            "status_messages": ["success"],
            "labels": ["Email", "Password"],
            "button_texts": ["Login", "Cancel"],
            "button_classes": ["btn-primary", "btn-secondary"],
            "undo_buttons": [],
            "cancel_buttons": ["cancel"],
            "confirmation_dialogs": [],
            "form_validations": ["email-val"],
            "destructive_actions": [],
            "navigation_visible": True,
            "help_texts": ["tooltip"],
            "autocomplete_fields": [],
            "keyboard_shortcuts": [],
            "search_available": False,
            "bulk_actions": [],
            "word_count": 500,
            "whitespace_ratio": 0.4,
            "ui_elements_count": 30,
            "error_messages": ["Invalid email"],
            "error_suggestions": [],
            "help_links": [],
            "contextual_help": [],
            "help_search": False,
        }

        # Evaluate heuristics
        evaluation = validator.evaluate_heuristics(
            url="https://example.com",
            heuristics="nielsen-10",
            page_data=page_data,
        )

        # Verify evaluation
        assert evaluation.url == "https://example.com"
        assert len(evaluation.heuristics) == 10
        assert 0 <= evaluation.overall_score <= 5.0

        # Generate reports in all formats
        json_report = validator.generate_evaluation_report(evaluation, format="json")
        assert json.loads(json_report)

        text_report = validator.generate_evaluation_report(evaluation, format="text")
        assert "USABILITY EVALUATION REPORT" in text_report

        html_report = validator.generate_evaluation_report(evaluation, format="html")
        assert "<!DOCTYPE html>" in html_report

    def test_form_and_mobile_analysis(self) -> None:
        """Test combined form and mobile analysis."""
        validator = UsabilityValidator()

        # Form data
        form_data = {
            "forms": [
                {
                    "id": "signup-form",
                    "fields": [
                        {
                            "name": "email",
                            "has_label": False,
                            "has_validation": False,
                            "required": True,
                            "has_error_message": False,
                            "has_placeholder": True,
                        }
                    ],
                }
            ]
        }

        # Mobile data
        mobile_data = {
            "has_viewport_meta": False,
            "interactive_elements": [{"selector": "button", "size": 32}],
            "has_horizontal_scroll": True,
            "has_tap_delay": False,
        }

        # Analyze forms
        form_issues = validator.analyze_forms(form_data)
        assert len(form_issues) > 0

        # Check mobile usability
        mobile_issues = validator.check_mobile_usability(mobile_data)
        assert len(mobile_issues) > 0

        # Verify all issues have proper structure
        for issue in form_issues:
            assert isinstance(issue, FormIssue)
            assert issue.form_id
            assert issue.issue_type
            assert issue.description

        for issue in mobile_issues:
            assert isinstance(issue, MobileIssue)
            assert issue.issue_type
            assert issue.description
