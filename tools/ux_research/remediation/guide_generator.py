"""
Remediation Guide Generator for UX Research & Design Feedback Platform.

This module generates WCAG violation fix recommendations with code examples,
prioritization, and automated issue creation.
"""

import json
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

import requests


class Severity(Enum):
    """Violation severity levels."""

    CRITICAL = "critical"
    SERIOUS = "serious"
    MODERATE = "moderate"
    MINOR = "minor"


class WCAGLevel(Enum):
    """WCAG conformance levels."""

    A = "A"
    AA = "AA"
    AAA = "AAA"


@dataclass
class Violation:
    """Accessibility violation details."""

    id: str
    description: str
    impact: str
    wcag_criteria: str
    wcag_level: WCAGLevel
    severity: Severity
    element: str
    help_url: Optional[str] = None
    context: Optional[str] = None


@dataclass
class CodeExample:
    """Before and after code example."""

    before: str
    after: str
    explanation: str
    language: str = "html"


@dataclass
class RemediationStep:
    """Step-by-step remediation instructions."""

    violation: Violation
    steps: List[str]
    code_example: Optional[CodeExample]
    estimated_effort: str
    priority_score: int
    alternatives: List[str]
    testing_guidance: str
    resources: List[str]


class RemediationGuide:
    """Generate remediation guidance for WCAG violations."""

    def __init__(self):
        """Initialize with remediation knowledge base."""
        self.remediation_db = self._build_remediation_db()
        self.effort_estimates = {
            Severity.CRITICAL: "2-4 hours",
            Severity.SERIOUS: "1-2 hours",
            Severity.MODERATE: "30-60 minutes",
            Severity.MINOR: "15-30 minutes",
        }

    def _build_remediation_db(self) -> Dict[str, Dict[str, Any]]:
        """
        Build comprehensive remediation knowledge base.

        Returns:
            Dictionary mapping violation IDs to remediation data
        """
        return {
            "image-alt": {
                "steps": [
                    "Identify all images missing alt text",
                    "Add descriptive alt attributes to <img> tags",
                    "Use empty alt='' for decorative images",
                    "Verify alt text provides equivalent information",
                ],
                "code_example": CodeExample(
                    before='<img src="logo.png">',
                    after='<img src="logo.png" alt="Company Logo">',
                    explanation=(
                        "Alt text provides text alternative for screen readers"
                    ),
                    language="html",
                ),
                "alternatives": [
                    "Use aria-label for complex images",
                    "Use aria-describedby for detailed descriptions",
                    "Use figure/figcaption for images with captions",
                ],
                "testing": ("Test with screen reader (NVDA/JAWS), validate with axe"),
                "resources": [
                    "https://www.w3.org/WAI/tutorials/images/",
                    "https://webaim.org/techniques/alttext/",
                ],
            },
            "color-contrast": {
                "steps": [
                    "Use contrast checker tool to identify violations",
                    "Adjust text color or background color",
                    "Ensure 4.5:1 ratio for normal text (AA)",
                    "Ensure 3:1 ratio for large text (AA)",
                    "Test in different lighting conditions",
                ],
                "code_example": CodeExample(
                    before=("color: #999; background: #fff; /* 2.8:1 contrast */"),
                    after=("color: #595959; background: #fff; /* 4.5:1 contrast */"),
                    explanation="Increased contrast ratio to meet WCAG AA",
                    language="css",
                ),
                "alternatives": [
                    "Use darker shades of existing colors",
                    "Add text shadow for additional contrast",
                    "Use border to distinguish elements",
                ],
                "testing": (
                    "Use WebAIM Contrast Checker, test with color blindness "
                    "simulators"
                ),
                "resources": [
                    "https://webaim.org/resources/contrastchecker/",
                    "https://www.w3.org/WAI/WCAG21/Understanding/contrast-minimum",
                ],
            },
            "button-name": {
                "steps": [
                    "Ensure all buttons have accessible names",
                    "Add aria-label or aria-labelledby",
                    "Use visible text content when possible",
                    "Avoid generic labels like 'Click here'",
                ],
                "code_example": CodeExample(
                    before='<button><i class="icon-save"></i></button>',
                    after=(
                        '<button aria-label="Save document">'
                        '<i class="icon-save"></i></button>'
                    ),
                    explanation="Aria-label provides accessible name",
                    language="html",
                ),
                "alternatives": [
                    "Use visually hidden text span",
                    "Use title attribute (not recommended)",
                    "Add visible text alongside icon",
                ],
                "testing": ("Navigate with keyboard, test with screen reader"),
                "resources": [
                    "https://www.w3.org/WAI/WCAG21/Understanding/name-role-value",
                    "https://webaim.org/techniques/forms/controls",
                ],
            },
            "label": {
                "steps": [
                    "Associate labels with form inputs using 'for' attribute",
                    "Ensure label text is descriptive",
                    "Place labels before inputs (except checkboxes/radios)",
                    "Use aria-label if visible label not possible",
                ],
                "code_example": CodeExample(
                    before='<label>Email</label><input type="email" id="email">',
                    after=(
                        '<label for="email">Email Address</label>'
                        '<input type="email" id="email" name="email">'
                    ),
                    explanation="for attribute associates label with input",
                    language="html",
                ),
                "alternatives": [
                    "Use aria-labelledby to reference label",
                    "Use aria-label for programmatic labels",
                    "Wrap input inside label element",
                ],
                "testing": "Click label to focus input, test with screen reader",
                "resources": [
                    "https://www.w3.org/WAI/tutorials/forms/labels/",
                    "https://webaim.org/techniques/forms/",
                ],
            },
            "link-name": {
                "steps": [
                    "Ensure all links have descriptive text",
                    "Avoid generic text like 'Click here' or 'Read more'",
                    "Add aria-label for icon-only links",
                    "Make link purpose clear from text alone",
                ],
                "code_example": CodeExample(
                    before='<a href="/article">Read more</a>',
                    after='<a href="/article">Read more about Web Accessibility</a>',
                    explanation="Descriptive link text provides context",
                    language="html",
                ),
                "alternatives": [
                    "Use aria-label for additional context",
                    "Use aria-describedby for detailed descriptions",
                    "Include article title in link text",
                ],
                "testing": (
                    "Use screen reader link list, test with keyboard navigation"
                ),
                "resources": [
                    (
                        "https://www.w3.org/WAI/WCAG21/Understanding/"
                        "link-purpose-in-context"
                    ),
                    "https://webaim.org/techniques/hypertext/",
                ],
            },
            "heading-order": {
                "steps": [
                    "Ensure proper heading hierarchy (h1->h2->h3)",
                    "Do not skip heading levels",
                    "Use only one h1 per page",
                    "Use headings for structure, not styling",
                ],
                "code_example": CodeExample(
                    before="<h1>Page Title</h1><h3>Section</h3>",
                    after="<h1>Page Title</h1><h2>Section</h2>",
                    explanation="Proper heading hierarchy improves navigation",
                    language="html",
                ),
                "alternatives": [
                    "Use aria-level for custom heading levels",
                    "Use CSS for styling without affecting semantics",
                    "Use role='heading' with aria-level",
                ],
                "testing": (
                    "Use heading navigation in screen reader, " "check document outline"
                ),
                "resources": [
                    "https://www.w3.org/WAI/tutorials/page-structure/headings/",
                    "https://webaim.org/techniques/semanticstructure/",
                ],
            },
            "landmark-one-main": {
                "steps": [
                    "Add <main> landmark to page",
                    "Ensure only one main landmark per page",
                    "Place primary content inside main",
                    "Use role='main' for older browsers",
                ],
                "code_example": CodeExample(
                    before='<div id="content">Main content</div>',
                    after="<main>Main content</main>",
                    explanation="Main landmark helps users skip to content",
                    language="html",
                ),
                "alternatives": [
                    "Use role='main' on existing element",
                    "Add aria-label to distinguish multiple mains",
                    "Ensure single main per page",
                ],
                "testing": (
                    "Use landmark navigation in screen reader, " "validate with axe"
                ),
                "resources": [
                    "https://www.w3.org/WAI/ARIA/apg/patterns/landmarks/",
                    "https://webaim.org/techniques/aria/",
                ],
            },
            "html-has-lang": {
                "steps": [
                    "Add lang attribute to <html> tag",
                    "Use appropriate language code (en, es, fr, etc.)",
                    "Use lang attribute for content in different languages",
                ],
                "code_example": CodeExample(
                    before="<html>",
                    after='<html lang="en">',
                    explanation="Lang attribute helps screen readers pronounce text",
                    language="html",
                ),
                "alternatives": [
                    "Use xml:lang for XHTML",
                    "Add lang to specific elements for mixed content",
                ],
                "testing": ("Test with screen reader, validate with HTML validator"),
                "resources": [
                    (
                        "https://www.w3.org/International/questions/"
                        "qa-html-language-declarations"
                    ),
                    "https://webaim.org/techniques/language/",
                ],
            },
            "meta-viewport": {
                "steps": [
                    "Add viewport meta tag to <head>",
                    "Allow user scaling (avoid maximum-scale=1)",
                    "Set initial scale to 1",
                    "Test on mobile devices",
                ],
                "code_example": CodeExample(
                    before=(
                        '<meta name="viewport" '
                        'content="width=device-width, maximum-scale=1">'
                    ),
                    after=(
                        '<meta name="viewport" '
                        'content="width=device-width, initial-scale=1">'
                    ),
                    explanation="Removed maximum-scale to allow user zoom",
                    language="html",
                ),
                "alternatives": [
                    "Use responsive CSS instead of disabling zoom",
                    "Allow minimum-scale for better accessibility",
                ],
                "testing": "Test zoom on mobile devices, validate with WAVE",
                "resources": [
                    "https://www.w3.org/WAI/WCAG21/Understanding/reflow",
                    "https://webaim.org/articles/zoom/",
                ],
            },
            "aria-required-attr": {
                "steps": [
                    "Identify ARIA roles missing required attributes",
                    "Add required attributes per ARIA specification",
                    "Validate ARIA usage with automated tools",
                    "Test with assistive technology",
                ],
                "code_example": CodeExample(
                    before='<div role="checkbox">Option</div>',
                    after='<div role="checkbox" aria-checked="false">Option</div>',
                    explanation="aria-checked required for checkbox role",
                    language="html",
                ),
                "alternatives": [
                    "Use native HTML elements when possible",
                    "Follow ARIA authoring practices",
                ],
                "testing": "Validate with axe, test with screen reader",
                "resources": [
                    "https://www.w3.org/TR/wai-aria-1.2/",
                    "https://www.w3.org/WAI/ARIA/apg/",
                ],
            },
        }

    def generate_remediation(self, violation: Violation) -> RemediationStep:
        """
        Generate remediation steps for violation.

        Args:
            violation: Violation object

        Returns:
            RemediationStep with detailed guidance
        """
        # Get remediation data from knowledge base
        remediation_data = self.remediation_db.get(
            violation.id, self._get_generic_remediation(violation)
        )

        # Calculate priority score
        priority_score = self._calculate_priority(violation)

        # Get estimated effort
        estimated_effort = self.effort_estimates.get(violation.severity, "1 hour")

        return RemediationStep(
            violation=violation,
            steps=remediation_data["steps"],
            code_example=remediation_data.get("code_example"),
            estimated_effort=estimated_effort,
            priority_score=priority_score,
            alternatives=remediation_data.get("alternatives", []),
            testing_guidance=remediation_data.get("testing", ""),
            resources=remediation_data.get("resources", []),
        )

    def _get_generic_remediation(self, violation: Violation) -> Dict[str, Any]:
        """
        Generate generic remediation for unknown violations.

        Args:
            violation: Violation object

        Returns:
            Generic remediation data
        """
        return {
            "steps": [
                f"Review {violation.wcag_criteria} guidelines",
                f"Identify affected element: {violation.element}",
                "Implement fix according to WCAG specification",
                "Test with assistive technology",
                "Validate with automated testing tools",
            ],
            "alternatives": [
                "Consult WCAG documentation",
                "Seek expert accessibility review",
            ],
            "testing": ("Test with screen reader and keyboard navigation"),
            "resources": [
                (
                    "https://www.w3.org/WAI/WCAG21/Understanding/"
                    f"{violation.wcag_criteria.lower()}"
                )
            ],
        }

    def _calculate_priority(self, violation: Violation) -> int:
        """
        Calculate priority score for violation.

        Args:
            violation: Violation object

        Returns:
            Priority score (higher = more urgent)
        """
        severity_scores = {
            Severity.CRITICAL: 100,
            Severity.SERIOUS: 75,
            Severity.MODERATE: 50,
            Severity.MINOR: 25,
        }

        level_scores = {WCAGLevel.A: 30, WCAGLevel.AA: 20, WCAGLevel.AAA: 10}

        return severity_scores.get(violation.severity, 50) + level_scores.get(
            violation.wcag_level, 0
        )

    def prioritize_violations(self, violations: List[Violation]) -> List[Violation]:
        """
        Prioritize violations by severity and effort.

        Args:
            violations: List of violations

        Returns:
            Sorted list of violations (highest priority first)
        """
        # Calculate priority for each violation
        prioritized = []
        for violation in violations:
            priority_score = self._calculate_priority(violation)
            prioritized.append((priority_score, violation))

        # Sort by priority (descending)
        prioritized.sort(key=lambda x: x[0], reverse=True)

        return [v for _, v in prioritized]

    def create_github_issue(self, violation: Violation, repo: str, token: str) -> str:
        """
        Create GitHub issue for violation.

        Args:
            violation: Violation object
            repo: Repository name (owner/repo)
            token: GitHub personal access token

        Returns:
            Issue URL

        Raises:
            requests.RequestException: If issue creation fails
        """
        # Generate remediation steps
        remediation = self.generate_remediation(violation)

        # Create issue title
        title = f"[A11Y] {violation.description}"

        # Create issue body
        body_parts = [
            "## Accessibility Violation",
            (
                f"**WCAG Criteria:** {violation.wcag_criteria} "
                f"(Level {violation.wcag_level.value})"
            ),
            f"**Severity:** {violation.severity.value.upper()}",
            f"**Impact:** {violation.impact}",
            "",
            "## Description",
            violation.description,
            "",
        ]

        if violation.element:
            body_parts.extend(
                [
                    "## Affected Element",
                    f"```html\n{violation.element}\n```",
                    "",
                ]
            )

        body_parts.extend(
            [
                "## Remediation Steps",
                *[f"{i+1}. {step}" for i, step in enumerate(remediation.steps)],
                "",
                f"**Estimated Effort:** {remediation.estimated_effort}",
                "",
            ]
        )

        if remediation.code_example:
            body_parts.extend(
                [
                    "## Code Example",
                    "### Before",
                    (
                        f"```{remediation.code_example.language}\n"
                        f"{remediation.code_example.before}\n```"
                    ),
                    "",
                    "### After",
                    (
                        f"```{remediation.code_example.language}\n"
                        f"{remediation.code_example.after}\n```"
                    ),
                    "",
                    f"**Explanation:** {remediation.code_example.explanation}",
                    "",
                ]
            )

        if remediation.alternatives:
            body_parts.extend(
                [
                    "## Alternative Approaches",
                    *[f"- {alt}" for alt in remediation.alternatives],
                    "",
                ]
            )

        body_parts.extend(
            [
                "## Testing Guidance",
                remediation.testing_guidance,
                "",
                "## Resources",
                *[f"- {resource}" for resource in remediation.resources],
                "",
                "---",
                (
                    "*Generated by UX Research Platform on "
                    f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*"
                ),
            ]
        )

        body = "\n".join(body_parts)

        # Create GitHub issue via API
        api_url = f"https://api.github.com/repos/{repo}/issues"
        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json",
        }
        data = {
            "title": title,
            "body": body,
            "labels": [
                "accessibility",
                violation.severity.value,
                f"wcag-{violation.wcag_level.value.lower()}",
            ],
        }

        response = requests.post(api_url, headers=headers, json=data, timeout=30)
        response.raise_for_status()

        issue_data = response.json()
        return issue_data["html_url"]

    def create_jira_issue(
        self,
        violation: Violation,
        jira_url: str,
        project_key: str,
        auth: tuple,
    ) -> str:
        """
        Create Jira issue for violation.

        Args:
            violation: Violation object
            jira_url: Jira instance URL
            project_key: Jira project key
            auth: Tuple of (username, api_token)

        Returns:
            Issue key

        Raises:
            requests.RequestException: If issue creation fails
        """
        # Generate remediation steps
        remediation = self.generate_remediation(violation)

        # Create issue summary
        summary = f"[A11Y] {violation.description}"

        # Create issue description
        description_parts = [
            f"h2. Accessibility Violation",
            (
                f"*WCAG Criteria:* {violation.wcag_criteria} "
                f"(Level {violation.wcag_level.value})"
            ),
            f"*Severity:* {violation.severity.value.upper()}",
            f"*Impact:* {violation.impact}",
            "",
            f"h2. Description",
            violation.description,
            "",
        ]

        if violation.element:
            description_parts.extend(
                [
                    "h2. Affected Element",
                    f"{{code:html}}\n{violation.element}\n{{code}}",
                    "",
                ]
            )

        description_parts.extend(
            [
                "h2. Remediation Steps",
                *[f"# {step}" for step in remediation.steps],
                "",
                f"*Estimated Effort:* {remediation.estimated_effort}",
                "",
            ]
        )

        if remediation.code_example:
            description_parts.extend(
                [
                    "h2. Code Example",
                    "h3. Before",
                    (
                        f"{{code:{remediation.code_example.language}}}\n"
                        f"{remediation.code_example.before}\n{{code}}"
                    ),
                    "",
                    "h3. After",
                    (
                        f"{{code:{remediation.code_example.language}}}\n"
                        f"{remediation.code_example.after}\n{{code}}"
                    ),
                    "",
                    f"*Explanation:* {remediation.code_example.explanation}",
                    "",
                ]
            )

        description = "\n".join(description_parts)

        # Determine priority
        priority_map = {
            Severity.CRITICAL: "Highest",
            Severity.SERIOUS: "High",
            Severity.MODERATE: "Medium",
            Severity.MINOR: "Low",
        }

        # Create Jira issue via API
        api_url = f"{jira_url}/rest/api/2/issue"
        headers = {"Content-Type": "application/json"}
        data = {
            "fields": {
                "project": {"key": project_key},
                "summary": summary,
                "description": description,
                "issuetype": {"name": "Bug"},
                "priority": {"name": priority_map.get(violation.severity, "Medium")},
                "labels": [
                    "accessibility",
                    violation.severity.value,
                    f"wcag-{violation.wcag_level.value.lower()}",
                ],
            }
        }

        response = requests.post(
            api_url, auth=auth, headers=headers, json=data, timeout=30
        )
        response.raise_for_status()

        issue_data = response.json()
        return issue_data["key"]

    def generate_code_example(self, violation: Violation) -> Optional[CodeExample]:
        """
        Generate before/after code example for violation.

        Args:
            violation: Violation object

        Returns:
            CodeExample or None if not available
        """
        remediation_data = self.remediation_db.get(violation.id)
        if remediation_data:
            return remediation_data.get("code_example")
        return None

    def generate_batch_report(self, violations: List[Violation]) -> Dict[str, Any]:
        """
        Generate comprehensive remediation report for multiple violations.

        Args:
            violations: List of violations

        Returns:
            Dictionary with report data
        """
        # Prioritize violations
        prioritized = self.prioritize_violations(violations)

        # Generate remediation for each
        remediations = []
        for violation in prioritized:
            remediation = self.generate_remediation(violation)
            remediations.append(
                {
                    "violation": {
                        "id": violation.id,
                        "description": violation.description,
                        "severity": violation.severity.value,
                        "wcag_criteria": violation.wcag_criteria,
                        "wcag_level": violation.wcag_level.value,
                    },
                    "priority_score": remediation.priority_score,
                    "estimated_effort": remediation.estimated_effort,
                    "steps": remediation.steps,
                    "has_code_example": remediation.code_example is not None,
                }
            )

        # Calculate statistics
        total_violations = len(violations)
        by_severity: Dict[str, int] = {}
        for violation in violations:
            severity = violation.severity.value
            by_severity[severity] = by_severity.get(severity, 0) + 1

        # Estimate total effort
        total_hours: float = 0.0
        for remediation_dict in remediations:
            effort = str(remediation_dict["estimated_effort"])
            # Parse effort string (e.g., "2-4 hours")
            if "hours" in effort:
                hours = effort.split("-")[0].strip()
                total_hours += float(hours.split()[0])
            elif "minutes" in effort:
                minutes = effort.split("-")[0].strip()
                total_hours += float(minutes.split()[0]) / 60

        return {
            "generated_at": datetime.now().isoformat(),
            "summary": {
                "total_violations": total_violations,
                "by_severity": by_severity,
                "estimated_total_effort_hours": round(total_hours, 1),
            },
            "remediations": remediations,
        }

    def export_report(self, violations: List[Violation], output_file: str) -> None:
        """
        Export remediation report to JSON file.

        Args:
            violations: List of violations
            output_file: Path to output file
        """
        report = self.generate_batch_report(violations)
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
