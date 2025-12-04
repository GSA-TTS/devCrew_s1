"""Usability Validator for UX Research Platform.

This module provides automated usability validation based on Nielsen's
10 heuristics, custom checklists, form analysis, mobile usability checks,
and content readability.
"""

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import textstat
import yaml


@dataclass
class HeuristicResult:
    """Result for a single heuristic evaluation."""

    heuristic: str
    rating: float
    issues: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    severity: str = "low"  # low, moderate, high, critical

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class HeuristicEvaluation:
    """Complete heuristic evaluation result."""

    evaluation_id: str
    url: str
    timestamp: str
    heuristics: List[HeuristicResult] = field(default_factory=list)
    overall_score: float = 0.0
    severity: str = "low"
    custom_checklist: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data["heuristics"] = [h.to_dict() for h in self.heuristics]
        return data


@dataclass
class FormIssue:
    """Form usability issue."""

    form_id: str
    field_name: str
    issue_type: str
    description: str
    severity: str = "moderate"
    recommendation: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class MobileIssue:
    """Mobile usability issue."""

    issue_type: str
    element: str
    description: str
    severity: str = "moderate"
    recommendation: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class ReadabilityScore:
    """Content readability scores."""

    flesch_reading_ease: float
    flesch_kincaid_grade: float
    gunning_fog: float
    smog_index: float
    automated_readability_index: float
    coleman_liau_index: float
    reading_level: str
    recommendation: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


class UsabilityValidator:
    """Usability validator for automated heuristic evaluation."""

    # Nielsen's 10 Heuristics
    NIELSEN_10_HEURISTICS = {
        "visibility": "Visibility of system status",
        "match_real_world": "Match between system and real world",
        "user_control": "User control and freedom",
        "consistency": "Consistency and standards",
        "error_prevention": "Error prevention",
        "recognition": "Recognition rather than recall",
        "flexibility": "Flexibility and efficiency of use",
        "aesthetic": "Aesthetic and minimalist design",
        "error_recovery": ("Help users recognize, diagnose, and recover from errors"),
        "documentation": "Help and documentation",
    }

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the usability validator.

        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self.custom_checklists: Dict[str, Dict] = {}
        self._load_default_config()

    def _load_default_config(self) -> None:
        """Load default configuration."""
        self.config.setdefault("min_touch_target_size", 44)  # pixels
        self.config.setdefault("max_form_fields", 10)
        self.config.setdefault("target_reading_level", 8)
        self.config.setdefault("enable_playwright", False)

    def load_custom_checklist(
        self, checklist_path: str, checklist_name: str = "custom"
    ) -> None:
        """Load custom heuristic checklist from YAML file.

        Args:
            checklist_path: Path to YAML checklist file
            checklist_name: Name to identify this checklist
        """
        checklist_file = Path(checklist_path)
        if not checklist_file.exists():
            raise FileNotFoundError(f"Checklist not found: {checklist_path}")

        with open(checklist_file, "r", encoding="utf-8") as f:
            self.custom_checklists[checklist_name] = yaml.safe_load(f)

    def evaluate_heuristics(
        self,
        url: str,
        heuristics: str = "nielsen-10",
        custom_checklist: Optional[Dict[str, Any]] = None,
        page_data: Optional[Dict[str, Any]] = None,
    ) -> HeuristicEvaluation:
        """Evaluate usability based on heuristics.

        Args:
            url: URL being evaluated
            heuristics: Heuristic set to use ("nielsen-10" or custom name)
            custom_checklist: Optional custom checklist dictionary
            page_data: Optional page data from browser automation

        Returns:
            HeuristicEvaluation object with results
        """
        evaluation_id = f"eval-{datetime.now().strftime('%Y-%m-%d-%H%M%S')}"
        custom_name = heuristics if heuristics != "nielsen-10" else None
        evaluation = HeuristicEvaluation(
            evaluation_id=evaluation_id,
            url=url,
            timestamp=datetime.now().isoformat(),
            custom_checklist=custom_name,
        )

        if heuristics == "nielsen-10":
            evaluation.heuristics = self._evaluate_nielsen_heuristics(url, page_data)
        elif custom_checklist:
            evaluation.heuristics = self._evaluate_custom_checklist(
                url, custom_checklist, page_data
            )
        elif heuristics in self.custom_checklists:
            evaluation.heuristics = self._evaluate_custom_checklist(
                url, self.custom_checklists[heuristics], page_data
            )
        else:
            raise ValueError(f"Unknown heuristic set: {heuristics}")

        # Calculate overall score
        if evaluation.heuristics:
            evaluation.overall_score = sum(
                h.rating for h in evaluation.heuristics
            ) / len(evaluation.heuristics)

        # Determine overall severity
        evaluation.severity = self._calculate_overall_severity(evaluation.heuristics)

        return evaluation

    def _evaluate_nielsen_heuristics(
        self, url: str, page_data: Optional[Dict[str, Any]] = None
    ) -> List[HeuristicResult]:
        """Evaluate Nielsen's 10 heuristics.

        Args:
            url: URL being evaluated
            page_data: Optional page data from browser

        Returns:
            List of HeuristicResult objects
        """
        results = []

        # 1. Visibility of system status
        results.append(self._check_visibility_status(page_data or {}))

        # 2. Match between system and real world
        results.append(self._check_match_real_world(page_data or {}))

        # 3. User control and freedom
        results.append(self._check_user_control(page_data or {}))

        # 4. Consistency and standards
        results.append(self._check_consistency(page_data or {}))

        # 5. Error prevention
        results.append(self._check_error_prevention(page_data or {}))

        # 6. Recognition rather than recall
        results.append(self._check_recognition(page_data or {}))

        # 7. Flexibility and efficiency of use
        results.append(self._check_flexibility(page_data or {}))

        # 8. Aesthetic and minimalist design
        results.append(self._check_aesthetic(page_data or {}))

        # 9. Help users recognize, diagnose, and recover from errors
        results.append(self._check_error_recovery(page_data or {}))

        # 10. Help and documentation
        results.append(self._check_documentation(page_data or {}))

        return results

    def _check_visibility_status(self, page_data: Dict[str, Any]) -> HeuristicResult:
        """Check visibility of system status heuristic."""
        result = HeuristicResult(
            heuristic=self.NIELSEN_10_HEURISTICS["visibility"],
            rating=5.0,
        )

        # Check for loading indicators
        if "loading_indicators" in page_data:
            if not page_data["loading_indicators"]:
                result.issues.append("No loading indicators found for async operations")
                result.recommendations.append(
                    "Add spinner or progress bar for loading states"
                )
                result.rating -= 1.0

        # Check for progress indicators
        if "progress_bars" in page_data:
            if not page_data["progress_bars"]:
                result.issues.append("No progress indicators for multi-step processes")
                result.recommendations.append(
                    "Add step indicators for multi-step forms/processes"
                )
                result.rating -= 0.5

        # Check for status messages
        if "status_messages" in page_data:
            if not page_data["status_messages"]:
                result.issues.append("No status messages for user actions")
                result.recommendations.append(
                    "Add success/error messages for user actions"
                )
                result.rating -= 1.0

        result.severity = self._calculate_severity(result.rating)
        return result

    def _check_match_real_world(self, page_data: Dict[str, Any]) -> HeuristicResult:
        """Check match between system and real world."""
        result = HeuristicResult(
            heuristic=self.NIELSEN_10_HEURISTICS["match_real_world"],
            rating=5.0,
        )

        # Check for jargon in labels
        if "labels" in page_data:
            jargon_count = 0
            jargon_terms = [
                "API",
                "URL",
                "JSON",
                "XML",
                "HTTP",
                "AJAX",
                "DOM",
                "UUID",
                "SQL",
            ]
            for label in page_data["labels"]:
                if any(term in label.upper() for term in jargon_terms):
                    jargon_count += 1

            if jargon_count > 3:
                result.issues.append(
                    f"Found {jargon_count} technical jargon terms in labels"
                )
                result.recommendations.append(
                    "Use plain language instead of technical jargon"
                )
                result.rating -= 1.0

        # Check for natural language
        if "button_texts" in page_data:
            unclear_buttons = []
            for btn in page_data["button_texts"]:
                if btn.lower() in ["ok", "submit", "send", "go"]:
                    unclear_buttons.append(btn)

            if unclear_buttons:
                result.issues.append(
                    f"Vague button labels: {', '.join(unclear_buttons)}"
                )
                result.recommendations.append(
                    "Use specific action-oriented button labels"
                )
                result.rating -= 0.5

        result.severity = self._calculate_severity(result.rating)
        return result

    def _check_user_control(self, page_data: Dict[str, Any]) -> HeuristicResult:
        """Check user control and freedom."""
        result = HeuristicResult(
            heuristic=self.NIELSEN_10_HEURISTICS["user_control"],
            rating=5.0,
        )

        # Check for undo/redo functionality
        if "undo_buttons" in page_data:
            if not page_data["undo_buttons"]:
                result.issues.append("No undo/redo functionality found")
                result.recommendations.append(
                    "Add undo/cancel options for destructive actions"
                )
                result.rating -= 1.0

        # Check for cancel buttons
        if "cancel_buttons" in page_data:
            if not page_data["cancel_buttons"]:
                result.issues.append("No cancel buttons in forms/dialogs")
                result.recommendations.append(
                    "Add cancel/close options to all dialogs and forms"
                )
                result.rating -= 1.0

        # Check for confirmation dialogs
        if "confirmation_dialogs" in page_data:
            if not page_data["confirmation_dialogs"]:
                result.issues.append("No confirmation for destructive actions")
                result.recommendations.append(
                    "Add confirmation dialogs for delete/destructive actions"
                )
                result.rating -= 1.5

        result.severity = self._calculate_severity(result.rating)
        return result

    def _check_consistency(self, page_data: Dict[str, Any]) -> HeuristicResult:
        """Check consistency and standards."""
        result = HeuristicResult(
            heuristic=self.NIELSEN_10_HEURISTICS["consistency"],
            rating=5.0,
        )

        # Check for consistent button styles
        if "button_classes" in page_data:
            unique_classes = len(set(page_data["button_classes"]))
            if unique_classes > 5:
                result.issues.append(
                    f"Too many button styles ({unique_classes} unique classes)"
                )
                result.recommendations.append(
                    "Standardize button styles across the interface"
                )
                result.rating -= 1.0

        # Check for consistent terminology
        if "labels" in page_data and "button_texts" in page_data:
            all_text = page_data["labels"] + page_data["button_texts"]
            if "save" in [t.lower() for t in all_text] and "submit" in [
                t.lower() for t in all_text
            ]:
                result.issues.append(
                    "Inconsistent terminology: both 'Save' and 'Submit' used"
                )
                result.recommendations.append(
                    "Use consistent terminology throughout the interface"
                )
                result.rating -= 0.5

        result.severity = self._calculate_severity(result.rating)
        return result

    def _check_error_prevention(self, page_data: Dict[str, Any]) -> HeuristicResult:
        """Check error prevention."""
        result = HeuristicResult(
            heuristic=self.NIELSEN_10_HEURISTICS["error_prevention"],
            rating=5.0,
        )

        # Check for input validation
        if "form_validations" in page_data:
            if not page_data["form_validations"]:
                result.issues.append("No client-side form validation found")
                result.recommendations.append(
                    "Add input validation with helpful error messages"
                )
                result.rating -= 1.5

        # Check for confirmation dialogs
        if "destructive_actions" in page_data:
            unconfirmed = [
                action
                for action in page_data["destructive_actions"]
                if not action.get("has_confirmation")
            ]
            if unconfirmed:
                result.issues.append(
                    f"{len(unconfirmed)} destructive actions without " "confirmation"
                )
                result.recommendations.append(
                    "Add confirmation dialogs for all destructive actions"
                )
                result.rating -= 1.0

        result.severity = self._calculate_severity(result.rating)
        return result

    def _check_recognition(self, page_data: Dict[str, Any]) -> HeuristicResult:
        """Check recognition rather than recall."""
        result = HeuristicResult(
            heuristic=self.NIELSEN_10_HEURISTICS["recognition"],
            rating=5.0,
        )

        # Check for visible navigation
        if "navigation_visible" in page_data:
            if not page_data["navigation_visible"]:
                result.issues.append("Navigation not consistently visible")
                result.recommendations.append(
                    "Keep navigation visible or easily accessible"
                )
                result.rating -= 1.0

        # Check for tooltips/help text
        if "help_texts" in page_data:
            if not page_data["help_texts"]:
                result.issues.append("No contextual help text found")
                result.recommendations.append(
                    "Add tooltips and help text for complex fields"
                )
                result.rating -= 0.5

        # Check for autocomplete
        if "autocomplete_fields" in page_data:
            if not page_data["autocomplete_fields"]:
                result.issues.append("No autocomplete for common fields")
                result.recommendations.append(
                    "Add autocomplete for common inputs (email, address, etc.)"
                )
                result.rating -= 0.5

        result.severity = self._calculate_severity(result.rating)
        return result

    def _check_flexibility(self, page_data: Dict[str, Any]) -> HeuristicResult:
        """Check flexibility and efficiency of use."""
        result = HeuristicResult(
            heuristic=self.NIELSEN_10_HEURISTICS["flexibility"],
            rating=5.0,
        )

        # Check for keyboard shortcuts
        if "keyboard_shortcuts" in page_data:
            if not page_data["keyboard_shortcuts"]:
                result.issues.append("No keyboard shortcuts found")
                result.recommendations.append(
                    "Add keyboard shortcuts for common actions"
                )
                result.rating -= 0.5

        # Check for search functionality
        if "search_available" in page_data:
            if not page_data["search_available"]:
                result.issues.append("No search functionality found")
                result.recommendations.append(
                    "Add search to help users find content quickly"
                )
                result.rating -= 1.0

        # Check for bulk actions
        if "bulk_actions" in page_data:
            if not page_data["bulk_actions"]:
                result.issues.append("No bulk actions for list operations")
                result.recommendations.append("Add bulk actions for power users")
                result.rating -= 0.5

        result.severity = self._calculate_severity(result.rating)
        return result

    def _check_aesthetic(self, page_data: Dict[str, Any]) -> HeuristicResult:
        """Check aesthetic and minimalist design."""
        result = HeuristicResult(
            heuristic=self.NIELSEN_10_HEURISTICS["aesthetic"],
            rating=5.0,
        )

        # Check for excessive content
        if "word_count" in page_data:
            if page_data["word_count"] > 1000:
                result.issues.append(
                    f"Page has {page_data['word_count']} words - may be " "overwhelming"
                )
                result.recommendations.append(
                    "Reduce content or split into multiple pages"
                )
                result.rating -= 1.0

        # Check for whitespace
        if "whitespace_ratio" in page_data:
            if page_data["whitespace_ratio"] < 0.3:
                result.issues.append("Insufficient whitespace in design")
                result.recommendations.append(
                    "Add more whitespace to improve readability"
                )
                result.rating -= 0.5

        # Check for number of UI elements
        if "ui_elements_count" in page_data:
            if page_data["ui_elements_count"] > 50:
                result.issues.append(
                    f"{page_data['ui_elements_count']} UI elements - " "too cluttered"
                )
                result.recommendations.append(
                    "Simplify the interface by removing unnecessary elements"
                )
                result.rating -= 1.0

        result.severity = self._calculate_severity(result.rating)
        return result

    def _check_error_recovery(self, page_data: Dict[str, Any]) -> HeuristicResult:
        """Check error recognition, diagnosis, and recovery."""
        result = HeuristicResult(
            heuristic=self.NIELSEN_10_HEURISTICS["error_recovery"],
            rating=5.0,
        )

        # Check for descriptive error messages
        if "error_messages" in page_data:
            generic_errors = []
            for error in page_data["error_messages"]:
                if error.lower() in [
                    "error",
                    "invalid",
                    "failed",
                    "something went wrong",
                ]:
                    generic_errors.append(error)

            if generic_errors:
                result.issues.append(
                    f"Generic error messages: {', '.join(generic_errors)}"
                )
                result.recommendations.append("Use specific, actionable error messages")
                result.rating -= 1.5

        # Check for error suggestions
        if "error_suggestions" in page_data:
            if not page_data["error_suggestions"]:
                result.issues.append("Error messages lack recovery suggestions")
                result.recommendations.append("Add suggestions on how to fix errors")
                result.rating -= 1.0

        result.severity = self._calculate_severity(result.rating)
        return result

    def _check_documentation(self, page_data: Dict[str, Any]) -> HeuristicResult:
        """Check help and documentation."""
        result = HeuristicResult(
            heuristic=self.NIELSEN_10_HEURISTICS["documentation"],
            rating=5.0,
        )

        # Check for help links
        if "help_links" in page_data:
            if not page_data["help_links"]:
                result.issues.append("No help or documentation links found")
                result.recommendations.append("Add help documentation or FAQ links")
                result.rating -= 1.0

        # Check for contextual help
        if "contextual_help" in page_data:
            if not page_data["contextual_help"]:
                result.issues.append("No contextual help available")
                result.recommendations.append(
                    "Add contextual help or tooltips for complex features"
                )
                result.rating -= 0.5

        # Check for search in documentation
        if "help_search" in page_data:
            if not page_data["help_search"]:
                result.issues.append("Help documentation lacks search")
                result.recommendations.append(
                    "Add search functionality to help documentation"
                )
                result.rating -= 0.5

        result.severity = self._calculate_severity(result.rating)
        return result

    def _evaluate_custom_checklist(
        self,
        url: str,
        checklist: Dict[str, Any],
        page_data: Optional[Dict[str, Any]] = None,
    ) -> List[HeuristicResult]:
        """Evaluate using custom checklist.

        Args:
            url: URL being evaluated
            checklist: Custom checklist dictionary
            page_data: Optional page data

        Returns:
            List of HeuristicResult objects
        """
        results = []

        for item in checklist.get("items", []):
            result = HeuristicResult(
                heuristic=item["name"],
                rating=item.get("default_rating", 5.0),
            )

            # Check conditions if provided
            if "checks" in item and page_data:
                for check in item["checks"]:
                    if not self._evaluate_check(check, page_data):
                        result.issues.append(check.get("issue", "Check failed"))
                        result.recommendations.append(
                            check.get("recommendation", "Fix the issue")
                        )
                        result.rating -= check.get("penalty", 1.0)

            result.severity = self._calculate_severity(result.rating)
            results.append(result)

        return results

    def _evaluate_check(self, check: Dict[str, Any], page_data: Dict[str, Any]) -> bool:
        """Evaluate a single check condition.

        Args:
            check: Check definition
            page_data: Page data to check against

        Returns:
            True if check passes, False otherwise
        """
        check_type = check.get("type", "exists")
        field = check.get("field")

        if not field or field not in page_data:
            return False

        value = page_data[field]

        if check_type == "exists":
            return bool(value)
        elif check_type == "count_greater":
            threshold = check.get("threshold", 0)
            return len(value) > threshold if isinstance(value, list) else False
        elif check_type == "count_less":
            threshold = check.get("threshold", 10)
            return len(value) < threshold if isinstance(value, list) else False
        elif check_type == "equals":
            expected = check.get("expected")
            return value == expected

        return True

    def analyze_forms(self, page: Any) -> List[FormIssue]:
        """Analyze form usability.

        Args:
            page: Playwright page object or page data dict

        Returns:
            List of FormIssue objects
        """
        issues = []

        # If page is a dict (test data), use it directly
        if isinstance(page, dict):
            page_data = page
        else:
            # Extract form data from Playwright page
            page_data = self._extract_form_data(page)

        for form in page_data.get("forms", []):
            form_id = form.get("id", "unknown")

            # Check field count
            fields = form.get("fields", [])
            if len(fields) > self.config["max_form_fields"]:
                max_fields = self.config["max_form_fields"]
                issues.append(
                    FormIssue(
                        form_id=form_id,
                        field_name="general",
                        issue_type="too_many_fields",
                        description=(
                            f"Form has {len(fields)} fields "
                            f"(max recommended: {max_fields})"
                        ),
                        severity="moderate",
                        recommendation="Split into multiple steps or pages",
                    )
                )

            # Check each field
            for form_field in fields:
                field_name = form_field.get("name", "unknown")

                # Check for labels
                if not form_field.get("has_label"):
                    issues.append(
                        FormIssue(
                            form_id=form_id,
                            field_name=field_name,
                            issue_type="missing_label",
                            description=f"Field '{field_name}' missing label",
                            severity="high",
                            recommendation="Add descriptive label to field",
                        )
                    )

                # Check for validation
                if not form_field.get("has_validation"):
                    issues.append(
                        FormIssue(
                            form_id=form_id,
                            field_name=field_name,
                            issue_type="missing_validation",
                            description=(f"Field '{field_name}' missing validation"),
                            severity="moderate",
                            recommendation=(
                                "Add client-side validation with " "error messages"
                            ),
                        )
                    )

                # Check for error messages
                required = form_field.get("required")
                has_error = form_field.get("has_error_message")
                if required and not has_error:
                    issues.append(
                        FormIssue(
                            form_id=form_id,
                            field_name=field_name,
                            issue_type="missing_error_message",
                            description=(
                                f"Required field '{field_name}' missing "
                                "error message"
                            ),
                            severity="moderate",
                            recommendation=(
                                "Add clear error message for " "validation failures"
                            ),
                        )
                    )

                # Check for placeholder vs label
                has_placeholder = form_field.get("has_placeholder")
                has_label = form_field.get("has_label")
                if has_placeholder and not has_label:
                    issues.append(
                        FormIssue(
                            form_id=form_id,
                            field_name=field_name,
                            issue_type="placeholder_as_label",
                            description=(
                                f"Field '{field_name}' uses placeholder "
                                "instead of label"
                            ),
                            severity="moderate",
                            recommendation=("Use proper labels, not just placeholders"),
                        )
                    )

        return issues

    def _extract_form_data(self, page: Any) -> Dict[str, Any]:
        """Extract form data from Playwright page.

        Args:
            page: Playwright page object

        Returns:
            Dictionary with form data
        """
        # This would use Playwright to extract actual form data
        # For now, return empty structure
        return {"forms": []}

    def check_mobile_usability(self, page: Any) -> List[MobileIssue]:
        """Check mobile usability.

        Args:
            page: Playwright page object or page data dict

        Returns:
            List of MobileIssue objects
        """
        issues = []

        # If page is a dict (test data), use it directly
        if isinstance(page, dict):
            page_data = page
        else:
            # Extract mobile data from Playwright page
            page_data = self._extract_mobile_data(page)

        # Check viewport meta tag
        if not page_data.get("has_viewport_meta"):
            issues.append(
                MobileIssue(
                    issue_type="missing_viewport_meta",
                    element="<head>",
                    description="Missing viewport meta tag",
                    severity="high",
                    recommendation=(
                        'Add: <meta name="viewport" '
                        'content="width=device-width, initial-scale=1">'
                    ),
                )
            )

        # Check touch target sizes
        for element in page_data.get("interactive_elements", []):
            size = element.get("size", 0)
            if size < self.config["min_touch_target_size"]:
                issues.append(
                    MobileIssue(
                        issue_type="small_touch_target",
                        element=element.get("selector", "unknown"),
                        description=(
                            f"Touch target too small: {size}px "
                            f"(min: {self.config['min_touch_target_size']}px)"
                        ),
                        severity="moderate",
                        recommendation=(
                            f"Increase target size to at least "
                            f"{self.config['min_touch_target_size']}px"
                        ),
                    )
                )

        # Check for horizontal scrolling
        if page_data.get("has_horizontal_scroll"):
            issues.append(
                MobileIssue(
                    issue_type="horizontal_scroll",
                    element="page",
                    description="Page has horizontal scrolling",
                    severity="high",
                    recommendation=("Fix layout to prevent horizontal scrolling"),
                )
            )

        # Check for tap delay
        if page_data.get("has_tap_delay"):
            issues.append(
                MobileIssue(
                    issue_type="tap_delay",
                    element="page",
                    description="300ms tap delay detected",
                    severity="moderate",
                    recommendation=(
                        "Add touch-action CSS or viewport meta to remove delay"
                    ),
                )
            )

        return issues

    def _extract_mobile_data(self, page: Any) -> Dict[str, Any]:
        """Extract mobile data from Playwright page.

        Args:
            page: Playwright page object

        Returns:
            Dictionary with mobile data
        """
        # This would use Playwright to extract actual mobile data
        # For now, return empty structure
        return {"interactive_elements": []}

    def calculate_readability(self, text: str) -> ReadabilityScore:
        """Calculate content readability scores.

        Args:
            text: Text content to analyze

        Returns:
            ReadabilityScore object
        """
        # Calculate various readability metrics
        flesch_ease = textstat.flesch_reading_ease(text)
        flesch_grade = textstat.flesch_kincaid_grade(text)
        gunning_fog = textstat.gunning_fog(text)
        smog = textstat.smog_index(text)
        ari = textstat.automated_readability_index(text)
        coleman_liau = textstat.coleman_liau_index(text)

        # Determine reading level
        grades = [flesch_grade, gunning_fog, smog, ari, coleman_liau]
        avg_grade = sum(grades) / 5
        reading_level = self._determine_reading_level(avg_grade)

        # Generate recommendation
        target_level = self.config["target_reading_level"]
        recommendation = ""
        if avg_grade > target_level:
            recommendation = (
                f"Content is at grade {avg_grade:.1f} level. "
                f"Simplify to grade {target_level} for better accessibility."
            )
        else:
            recommendation = (
                f"Content is at grade {avg_grade:.1f} level - " "good readability!"
            )

        return ReadabilityScore(
            flesch_reading_ease=flesch_ease,
            flesch_kincaid_grade=flesch_grade,
            gunning_fog=gunning_fog,
            smog_index=smog,
            automated_readability_index=ari,
            coleman_liau_index=coleman_liau,
            reading_level=reading_level,
            recommendation=recommendation,
        )

    def _determine_reading_level(self, grade: float) -> str:
        """Determine reading level from grade.

        Args:
            grade: Grade level score

        Returns:
            Reading level description
        """
        if grade < 6:
            return "Elementary"
        elif grade < 9:
            return "Middle School"
        elif grade < 13:
            return "High School"
        elif grade < 16:
            return "College"
        else:
            return "Graduate"

    def _calculate_severity(self, rating: float) -> str:
        """Calculate severity based on rating.

        Args:
            rating: Rating score (1-5)

        Returns:
            Severity level string
        """
        if rating >= 4.5:
            return "low"
        elif rating >= 3.5:
            return "moderate"
        elif rating >= 2.5:
            return "high"
        else:
            return "critical"

    def _calculate_overall_severity(self, results: List[HeuristicResult]) -> str:
        """Calculate overall severity from heuristic results.

        Args:
            results: List of heuristic results

        Returns:
            Overall severity level
        """
        if not results:
            return "low"

        severity_scores = {
            "critical": 4,
            "high": 3,
            "moderate": 2,
            "low": 1,
        }

        max_severity = max(severity_scores.get(r.severity, 1) for r in results)

        for severity, score in severity_scores.items():
            if score == max_severity:
                return severity

        return "low"

    def generate_evaluation_report(
        self, evaluation: HeuristicEvaluation, format: str = "json"
    ) -> str:
        """Generate evaluation report.

        Args:
            evaluation: HeuristicEvaluation object
            format: Output format ("json", "text", "html")

        Returns:
            Report string in specified format
        """
        if format == "json":
            return json.dumps(evaluation.to_dict(), indent=2)
        elif format == "text":
            return self._generate_text_report(evaluation)
        elif format == "html":
            return self._generate_html_report(evaluation)
        else:
            raise ValueError(f"Unsupported format: {format}")

    def _generate_text_report(self, evaluation: HeuristicEvaluation) -> str:
        """Generate text report.

        Args:
            evaluation: HeuristicEvaluation object

        Returns:
            Text report string
        """
        lines = [
            "=" * 80,
            "USABILITY EVALUATION REPORT",
            "=" * 80,
            f"Evaluation ID: {evaluation.evaluation_id}",
            f"URL: {evaluation.url}",
            f"Timestamp: {evaluation.timestamp}",
            f"Overall Score: {evaluation.overall_score:.2f}/5.0",
            f"Severity: {evaluation.severity.upper()}",
            "",
            "HEURISTIC RESULTS",
            "-" * 80,
        ]

        for result in evaluation.heuristics:
            lines.extend(
                [
                    "",
                    f"Heuristic: {result.heuristic}",
                    f"Rating: {result.rating:.1f}/5.0 ({result.severity})",
                ]
            )

            if result.issues:
                lines.append("Issues:")
                for issue in result.issues:
                    lines.append(f"  - {issue}")

            if result.recommendations:
                lines.append("Recommendations:")
                for rec in result.recommendations:
                    lines.append(f"  - {rec}")

        lines.append("=" * 80)
        return "\n".join(lines)

    def _generate_html_report(self, evaluation: HeuristicEvaluation) -> str:
        """Generate HTML report.

        Args:
            evaluation: HeuristicEvaluation object

        Returns:
            HTML report string
        """
        severity_colors = {
            "low": "#28a745",
            "moderate": "#ffc107",
            "high": "#fd7e14",
            "critical": "#dc3545",
        }

        html_parts = [
            "<!DOCTYPE html>",
            "<html>",
            "<head>",
            "<meta charset='utf-8'>",
            "<title>Usability Evaluation Report</title>",
            "<style>",
            "body { font-family: Arial, sans-serif; margin: 20px; }",
            "h1, h2 { color: #333; }",
            ".header { background: #f8f9fa; padding: 20px; " "border-radius: 5px; }",
            ".heuristic { margin: 20px 0; padding: 15px; "
            "border-left: 4px solid #007bff; background: #f8f9fa; }",
            ".severity { padding: 5px 10px; border-radius: 3px; "
            "color: white; font-weight: bold; }",
            ".issues, .recommendations { margin: 10px 0; }",
            "ul { margin: 5px 0; }",
            "</style>",
            "</head>",
            "<body>",
            "<div class='header'>",
            "<h1>Usability Evaluation Report</h1>",
            f"<p><strong>Evaluation ID:</strong> " f"{evaluation.evaluation_id}</p>",
            f"<p><strong>URL:</strong> {evaluation.url}</p>",
            f"<p><strong>Timestamp:</strong> {evaluation.timestamp}</p>",
            f"<p><strong>Overall Score:</strong> "
            f"{evaluation.overall_score:.2f}/5.0</p>",
            f"<p><strong>Severity:</strong> <span class='severity' "
            f"style='background-color: "
            f"{severity_colors.get(evaluation.severity, '#6c757d')};'>"
            f"{evaluation.severity.upper()}</span></p>",
            "</div>",
            "<h2>Heuristic Results</h2>",
        ]

        for result in evaluation.heuristics:
            html_parts.extend(
                [
                    "<div class='heuristic'>",
                    f"<h3>{result.heuristic}</h3>",
                    f"<p><strong>Rating:</strong> {result.rating:.1f}/5.0 "
                    f"<span class='severity' style='background-color: "
                    f"{severity_colors.get(result.severity, '#6c757d')};'>"
                    f"{result.severity.upper()}</span></p>",
                ]
            )

            if result.issues:
                html_parts.append("<div class='issues'>")
                html_parts.append("<strong>Issues:</strong>")
                html_parts.append("<ul>")
                for issue in result.issues:
                    html_parts.append(f"<li>{issue}</li>")
                html_parts.append("</ul>")
                html_parts.append("</div>")

            if result.recommendations:
                html_parts.append("<div class='recommendations'>")
                html_parts.append("<strong>Recommendations:</strong>")
                html_parts.append("<ul>")
                for rec in result.recommendations:
                    html_parts.append(f"<li>{rec}</li>")
                html_parts.append("</ul>")
                html_parts.append("</div>")

            html_parts.append("</div>")

        html_parts.extend(["</body>", "</html>"])

        return "\n".join(html_parts)
