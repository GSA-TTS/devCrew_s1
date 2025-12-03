"""
Automated GitHub Issue Classification and Triage.

ML-powered classifier for automatic issue labeling, priority assignment,
and team routing based on issue content analysis.

Protocol Coverage: P-ISSUE-TRIAGE
"""

import json
import logging
import re
from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)


class IssueClassifier:
    """
    Automated classifier for GitHub issues.

    Uses rule-based and pattern matching to classify issues by type,
    priority, and appropriate team assignment.
    """

    # Issue type patterns
    TYPE_PATTERNS = {
        "bug": [
            r"\bbug\b",
            r"\berror\b",
            r"\bfail(s|ed|ing)?\b",
            r"\bcrash\b",
            r"\bbroken\b",
            r"\bnot working\b",
            r"\bissue\b",
            r"\bproblem\b",
            r"\bexception\b",
        ],
        "feature": [
            r"\bfeature\b",
            r"\benhancement\b",
            r"\bimplement\b",
            r"\badd\b",
            r"\bsupport\b",
            r"\bwould be nice\b",
            r"\bwould be great\b",
        ],
        "documentation": [
            r"\bdoc(s|umentation)?\b",
            r"\breadme\b",
            r"\bguide\b",
            r"\btutorial\b",
            r"\bexample\b",
        ],
        "question": [
            r"\bquestion\b",
            r"\bhow to\b",
            r"\bwhy\b",
            r"\bwhat\b",
            r"\bhelp\b",
            r"\?\s*$",
        ],
        "performance": [
            r"\bperformance\b",
            r"\bslow\b",
            r"\boptimize\b",
            r"\bspeed\b",
            r"\blatency\b",
        ],
        "security": [
            r"\bsecurity\b",
            r"\bvulner(ability|able)\b",
            r"\bCVE\b",
            r"\bexploit\b",
            r"\bxss\b",
            r"\bsql injection\b",
        ],
    }

    # Priority indicators
    PRIORITY_HIGH = [
        r"\bcritical\b",
        r"\burgent\b",
        r"\bblocking\b",
        r"\bproduction\b",
        r"\bdata loss\b",
        r"\bsecurity\b",
    ]

    PRIORITY_LOW = [
        r"\bnice to have\b",
        r"\bminor\b",
        r"\bcosmetic\b",
        r"\btrivial\b",
    ]

    # Component patterns
    COMPONENT_PATTERNS = {
        "frontend": [
            r"\bui\b",
            r"\bfrontend\b",
            r"\breact\b",
            r"\bvue\b",
            r"\bangular\b",
            r"\bcss\b",
            r"\bhtml\b",
        ],
        "backend": [
            r"\bbackend\b",
            r"\bapi\b",
            r"\bserver\b",
            r"\bdatabase\b",
            r"\bpostgres\b",
            r"\bmysql\b",
        ],
        "devops": [
            r"\bdevops\b",
            r"\bci/cd\b",
            r"\bdocker\b",
            r"\bkubernetes\b",
            r"\bdeployment\b",
        ],
        "infrastructure": [
            r"\binfrastructure\b",
            r"\bcloud\b",
            r"\baws\b",
            r"\bazure\b",
            r"\bgcp\b",
        ],
    }

    def __init__(
        self,
        custom_patterns: Optional[Dict[str, List[str]]] = None,
        custom_labels: Optional[Dict[str, List[str]]] = None,
    ) -> None:
        """
        Initialize issue classifier.

        Args:
            custom_patterns: Additional type patterns
            custom_labels: Custom label mappings
        """
        self.type_patterns = self.TYPE_PATTERNS.copy()
        self.component_patterns = self.COMPONENT_PATTERNS.copy()

        if custom_patterns:
            for issue_type, patterns in custom_patterns.items():
                if issue_type in self.type_patterns:
                    self.type_patterns[issue_type].extend(patterns)
                else:
                    self.type_patterns[issue_type] = patterns

        self.custom_labels = custom_labels or {}

        # Compile regex patterns for efficiency
        self._compiled_patterns: Dict[str, Any] = {}
        self._compile_patterns()

        logger.info("Issue classifier initialized")

    def _compile_patterns(self) -> None:
        """Compile regex patterns for better performance."""
        self._compiled_patterns["types"] = {
            issue_type: [re.compile(pattern, re.IGNORECASE) for pattern in patterns]
            for issue_type, patterns in self.type_patterns.items()
        }

        self._compiled_patterns["components"] = {
            component: [re.compile(pattern, re.IGNORECASE) for pattern in patterns]
            for component, patterns in self.component_patterns.items()
        }

        self._compiled_patterns["priority_high"] = [
            re.compile(pattern, re.IGNORECASE) for pattern in self.PRIORITY_HIGH
        ]

        self._compiled_patterns["priority_low"] = [
            re.compile(pattern, re.IGNORECASE) for pattern in self.PRIORITY_LOW
        ]

    def classify_issue(
        self,
        title: str,
        body: str = "",
        labels: Optional[List[str]] = None,
        author: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Classify an issue based on its content.

        Args:
            title: Issue title
            body: Issue body/description
            labels: Existing labels
            author: Issue author username

        Returns:
            Classification result with suggested labels and metadata
        """
        content = f"{title} {body}".lower()
        labels = labels or []

        result: Dict[str, Any] = {
            "types": [],
            "components": [],
            "priority": "medium",
            "suggested_labels": set(),
            "confidence": {},
            "metadata": {},
        }

        # Detect issue types
        type_scores: Dict[str, int] = defaultdict(int)
        for issue_type, patterns in self._compiled_patterns["types"].items():
            for pattern in patterns:
                matches = len(pattern.findall(content))
                if matches > 0:
                    type_scores[issue_type] += matches

        # Sort by score and take top types
        if type_scores:
            sorted_types = sorted(type_scores.items(), key=lambda x: x[1], reverse=True)
            result["types"] = [t[0] for t in sorted_types[:2]]
            result["confidence"]["types"] = {t: score for t, score in sorted_types[:2]}

        # Detect components
        component_scores: Dict[str, int] = defaultdict(int)
        for component, patterns in self._compiled_patterns["components"].items():
            for pattern in patterns:
                matches = len(pattern.findall(content))
                if matches > 0:
                    component_scores[component] += matches

        if component_scores:
            sorted_components = sorted(
                component_scores.items(), key=lambda x: x[1], reverse=True
            )
            result["components"] = [c[0] for c in sorted_components[:2]]
            result["confidence"]["components"] = {
                c: score for c, score in sorted_components[:2]
            }

        # Determine priority
        result["priority"] = self._determine_priority(content, labels)

        # Generate suggested labels
        suggested = set()

        # Add type labels
        for issue_type in result["types"]:
            suggested.add(f"type:{issue_type}")

        # Add component labels
        for component in result["components"]:
            suggested.add(f"component:{component}")

        # Add priority label
        if result["priority"] in ["critical", "high"]:
            suggested.add(f"priority:{result['priority']}")

        # Add custom labels based on patterns
        for label_name, keywords in self.custom_labels.items():
            if any(keyword.lower() in content for keyword in keywords):
                suggested.add(label_name)

        result["suggested_labels"] = sorted(suggested)

        # Add metadata
        result["metadata"] = {
            "analyzed_at": datetime.utcnow().isoformat(),
            "content_length": len(content),
            "has_code_block": "```" in body,
            "has_error_trace": (
                "error" in content.lower() and "at " in content.lower()
            ),
        }

        logger.info(
            f"Classified issue: types={result['types']}, "
            f"priority={result['priority']}"
        )

        return result

    def _determine_priority(self, content: str, existing_labels: List[str]) -> str:
        """
        Determine issue priority.

        Args:
            content: Issue content
            existing_labels: Existing labels

        Returns:
            Priority level (critical, high, medium, low)
        """
        # Check existing priority labels
        for label in existing_labels:
            if label.startswith("priority:"):
                return label.split(":")[1]

        # Check for high priority indicators
        high_matches = sum(
            1
            for pattern in self._compiled_patterns["priority_high"]
            if pattern.search(content)
        )

        if high_matches >= 2:
            return "critical"
        elif high_matches == 1:
            return "high"

        # Check for low priority indicators
        low_matches = sum(
            1
            for pattern in self._compiled_patterns["priority_low"]
            if pattern.search(content)
        )

        if low_matches > 0:
            return "low"

        return "medium"

    def batch_classify(self, issues: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Classify multiple issues at once.

        Args:
            issues: List of issue dictionaries with title/body

        Returns:
            List of classification results
        """
        results = []
        for issue in issues:
            classification = self.classify_issue(
                title=issue.get("title", ""),
                body=issue.get("body", ""),
                labels=issue.get("labels", []),
                author=issue.get("author"),
            )
            classification["issue_number"] = issue.get("number")
            results.append(classification)

        logger.info(f"Batch classified {len(results)} issues")
        return results

    def suggest_assignee(
        self,
        issue_type: str,
        component: Optional[str] = None,
        team_mapping: Optional[Dict[str, List[str]]] = None,
    ) -> Optional[str]:
        """
        Suggest assignee based on issue classification.

        Args:
            issue_type: Issue type
            component: Component name
            team_mapping: Mapping of components to team members

        Returns:
            Suggested assignee username or None
        """
        if not team_mapping:
            return None

        # Try component-based assignment first
        if component and component in team_mapping:
            members = team_mapping[component]
            if members:
                # Simple round-robin (would need state for real impl)
                return members[0]

        # Fall back to type-based assignment
        if issue_type in team_mapping:
            members = team_mapping[issue_type]
            if members:
                return members[0]

        return None

    def generate_triage_report(self, issues: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate triage report for multiple issues.

        Args:
            issues: List of issue dictionaries

        Returns:
            Triage report with statistics and recommendations
        """
        classifications = self.batch_classify(issues)

        # Aggregate statistics
        type_counts: Dict[str, int] = defaultdict(int)
        component_counts: Dict[str, int] = defaultdict(int)
        priority_counts: Dict[str, int] = defaultdict(int)

        for classification in classifications:
            for issue_type in classification["types"]:
                type_counts[issue_type] += 1

            for component in classification["components"]:
                component_counts[component] += 1

            priority_counts[classification["priority"]] += 1

        report = {
            "summary": {
                "total_issues": len(issues),
                "types": dict(type_counts),
                "components": dict(component_counts),
                "priorities": dict(priority_counts),
            },
            "recommendations": [],
            "high_priority": [],
            "unclassified": [],
            "generated_at": datetime.utcnow().isoformat(),
        }

        # Identify high priority issues
        for classification in classifications:
            if classification["priority"] in ["critical", "high"]:
                report["high_priority"].append(
                    {
                        "issue_number": classification.get("issue_number"),
                        "types": classification["types"],
                        "priority": classification["priority"],
                    }
                )

        # Identify unclassified issues (low confidence)
        for classification in classifications:
            if not classification["types"]:
                report["unclassified"].append(classification.get("issue_number"))

        # Generate recommendations
        if report["high_priority"]:
            report["recommendations"].append(
                f"Address {len(report['high_priority'])} high-priority "
                f"issues immediately"
            )

        if report["unclassified"]:
            report["recommendations"].append(
                f"Manually review {len(report['unclassified'])} " f"unclassified issues"
            )

        # Component-based recommendations
        if component_counts:
            top_component = max(component_counts.items(), key=lambda x: x[1])
            report["recommendations"].append(
                f"Most issues in '{top_component[0]}' component "
                f"({top_component[1]} issues) - consider team allocation"
            )

        logger.info(f"Generated triage report for {len(issues)} issues")

        return report

    def export_classification_rules(self) -> str:
        """
        Export classification rules as JSON.

        Returns:
            JSON string of classification rules
        """
        rules = {
            "type_patterns": self.type_patterns,
            "component_patterns": self.component_patterns,
            "priority_high": self.PRIORITY_HIGH,
            "priority_low": self.PRIORITY_LOW,
            "custom_labels": self.custom_labels,
        }
        return json.dumps(rules, indent=2)

    def import_classification_rules(self, rules_json: str) -> None:
        """
        Import classification rules from JSON.

        Args:
            rules_json: JSON string of rules
        """
        rules = json.loads(rules_json)

        if "type_patterns" in rules:
            self.type_patterns.update(rules["type_patterns"])

        if "component_patterns" in rules:
            self.component_patterns.update(rules["component_patterns"])

        if "custom_labels" in rules:
            self.custom_labels.update(rules["custom_labels"])

        # Recompile patterns
        self._compile_patterns()

        logger.info("Imported classification rules")

    def train_from_labeled_issues(
        self, labeled_issues: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Learn patterns from manually labeled issues.

        Args:
            labeled_issues: List of issues with verified labels

        Returns:
            Training statistics
        """
        # Extract common terms from labeled issues
        term_frequencies: Dict[str, Dict[str, int]] = defaultdict(
            lambda: defaultdict(int)
        )

        for issue in labeled_issues:
            content = (f"{issue.get('title', '')} {issue.get('body', '')}").lower()
            labels = issue.get("labels", [])

            # Extract words
            words = re.findall(r"\b\w{4,}\b", content)

            for label in labels:
                for word in words:
                    term_frequencies[label][word] += 1

        # Identify significant terms (appear frequently for specific labels)
        learned_patterns: Dict[str, List[str]] = {}
        threshold = 3  # Minimum frequency

        for label, terms in term_frequencies.items():
            significant_terms = [
                term for term, freq in terms.items() if freq >= threshold
            ]
            if significant_terms:
                learned_patterns[label] = significant_terms[:10]  # Top 10

        stats = {
            "issues_analyzed": len(labeled_issues),
            "labels_found": len(term_frequencies),
            "patterns_learned": sum(len(p) for p in learned_patterns.values()),
            "learned_patterns": learned_patterns,
        }

        logger.info(f"Trained classifier from {len(labeled_issues)} labeled issues")

        return stats
