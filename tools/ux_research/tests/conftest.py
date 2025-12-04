"""
Pytest configuration and shared fixtures for UX Research tests.

This module provides:
- Pytest configuration
- Shared test fixtures
- Mock objects and data
- Test utilities
"""

import asyncio
import json
import tempfile
from pathlib import Path
from typing import AsyncGenerator, Dict, List
from unittest.mock import AsyncMock, MagicMock, Mock

import pytest


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def temp_dir():
    """Create temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_html_with_issues():
    """Sample HTML page with accessibility issues."""
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <title>Test Page</title>
    </head>
    <body>
        <!-- Missing alt text -->
        <img src="image.jpg">

        <!-- Low contrast -->
        <p style="color: #777; background: #fff;">Low contrast text</p>

        <!-- Missing form label -->
        <form>
            <input type="text" name="email">
            <button type="submit">Submit</button>
        </form>

        <!-- Non-semantic markup -->
        <div onclick="handleClick()">Clickable div</div>

        <!-- Missing heading hierarchy -->
        <h3>Section heading without h1 or h2</h3>

        <!-- Empty link -->
        <a href="#"></a>

        <!-- Missing aria-label on icon button -->
        <button><i class="icon-search"></i></button>
    </body>
    </html>
    """


@pytest.fixture
def sample_html_accessible():
    """Sample HTML page with good accessibility."""
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <title>Accessible Test Page</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body>
        <header>
            <h1>Main Heading</h1>
            <nav aria-label="Main navigation">
                <ul>
                    <li><a href="/">Home</a></li>
                    <li><a href="/about">About</a></li>
                </ul>
            </nav>
        </header>

        <main>
            <h2>Section Heading</h2>
            <img src="image.jpg" alt="Description of image">

            <form>
                <label for="email">Email Address</label>
                <input type="email" id="email" name="email" required>
                <button type="submit">Submit Form</button>
            </form>

            <button aria-label="Search">
                <i class="icon-search"></i>
            </button>
        </main>

        <footer>
            <p>&copy; 2024 Accessible Site</p>
        </footer>
    </body>
    </html>
    """


@pytest.fixture
def sample_feedback_csv(temp_dir):
    """Create sample feedback CSV file."""
    csv_content = """timestamp,user_id,feedback,rating,category
2024-01-01 10:00:00,user1,The interface is confusing,2,usability
2024-01-01 11:00:00,user2,Love the new design!,5,design
2024-01-01 12:00:00,user3,Cannot find the search button,1,navigation
2024-01-01 13:00:00,user4,Great experience overall,4,general
2024-01-01 14:00:00,user5,Too many clicks to complete task,2,usability
2024-01-01 15:00:00,user6,Excellent accessibility features,5,accessibility
2024-01-01 16:00:00,user7,Font size too small,3,design
2024-01-01 17:00:00,user8,Perfect for my needs,5,general
2024-01-01 18:00:00,user9,Slow loading times,2,performance
2024-01-01 19:00:00,user10,Intuitive navigation,4,navigation
"""
    csv_path = temp_dir / "feedback.csv"
    csv_path.write_text(csv_content)
    return csv_path


@pytest.fixture
def sample_feedback_json():
    """Sample feedback data in JSON format."""
    return [
        {
            "id": "fb1",
            "timestamp": "2024-01-01T10:00:00Z",
            "user_id": "user1",
            "feedback": "The interface is confusing",
            "rating": 2,
            "category": "usability",
            "source": "survey",
        },
        {
            "id": "fb2",
            "timestamp": "2024-01-01T11:00:00Z",
            "user_id": "user2",
            "feedback": "Love the new design!",
            "rating": 5,
            "category": "design",
            "source": "survey",
        },
        {
            "id": "fb3",
            "timestamp": "2024-01-01T12:00:00Z",
            "user_id": "user3",
            "feedback": "Cannot find the search button",
            "rating": 1,
            "category": "navigation",
            "source": "support",
        },
    ]


@pytest.fixture
def mock_axe_results():
    """Mock axe-core audit results."""
    return {
        "violations": [
            {
                "id": "image-alt",
                "impact": "critical",
                "description": "Images must have alternate text",
                "help": "Ensures <img> elements have alternate text",
                "helpUrl": "https://dequeuniversity.com/rules/axe/4.8/image-alt",
                "nodes": [
                    {
                        "html": '<img src="image.jpg">',
                        "target": ["img"],
                        "failureSummary": "Fix any of the following:\n"
                        "  Element does not have an alt attribute",
                    }
                ],
            },
            {
                "id": "color-contrast",
                "impact": "serious",
                "description": "Elements must have sufficient color contrast",
                "help": "Ensures contrast ratio meets WCAG AA requirements",
                "helpUrl": "https://dequeuniversity.com/rules/axe/4.8/color-contrast",
                "nodes": [
                    {
                        "html": '<p style="color: #777; background: #fff;">',
                        "target": ["p"],
                        "failureSummary": "Fix any of the following:\n"
                        "  Element has insufficient color contrast",
                    }
                ],
            },
            {
                "id": "label",
                "impact": "critical",
                "description": "Form elements must have labels",
                "help": "Ensures form field has a label",
                "helpUrl": "https://dequeuniversity.com/rules/axe/4.8/label",
                "nodes": [
                    {
                        "html": '<input type="text" name="email">',
                        "target": ['input[name="email"]'],
                        "failureSummary": "Fix any of the following:\n"
                        "  Form element does not have a label",
                    }
                ],
            },
        ],
        "passes": [],
        "incomplete": [],
        "inapplicable": [],
    }


@pytest.fixture
def mock_lighthouse_results():
    """Mock Lighthouse audit results."""
    return {
        "categories": {
            "accessibility": {
                "score": 0.75,
                "title": "Accessibility",
                "auditRefs": [
                    {"id": "aria-valid-attr", "weight": 1},
                    {"id": "color-contrast", "weight": 2},
                ],
            },
            "performance": {"score": 0.85, "title": "Performance"},
            "best-practices": {"score": 0.90, "title": "Best Practices"},
            "seo": {"score": 0.80, "title": "SEO"},
        },
        "audits": {
            "color-contrast": {
                "score": 0,
                "displayValue": "3 elements",
                "details": {
                    "items": [
                        {
                            "node": {
                                "selector": "p",
                                "snippet": '<p style="color: #777">',
                            }
                        }
                    ]
                },
            }
        },
    }


@pytest.fixture
def mock_google_analytics_data():
    """Mock Google Analytics API response."""
    return {
        "reports": [
            {
                "columnHeader": {
                    "dimensions": ["ga:pagePath"],
                    "metricHeader": {
                        "metricHeaderEntries": [
                            {"name": "ga:pageviews", "type": "INTEGER"},
                            {"name": "ga:avgTimeOnPage", "type": "TIME"},
                            {"name": "ga:bounceRate", "type": "PERCENT"},
                        ]
                    },
                },
                "data": {
                    "rows": [
                        {
                            "dimensions": ["/"],
                            "metrics": [{"values": ["1000", "120.5", "35.2"]}],
                        },
                        {
                            "dimensions": ["/about"],
                            "metrics": [{"values": ["500", "90.3", "42.1"]}],
                        },
                        {
                            "dimensions": ["/contact"],
                            "metrics": [{"values": ["300", "60.8", "55.7"]}],
                        },
                    ]
                },
            }
        ]
    }


@pytest.fixture
def mock_hotjar_heatmap_data():
    """Mock Hotjar heatmap data."""
    return {
        "heatmaps": [
            {
                "id": "hm1",
                "url": "https://example.com",
                "type": "click",
                "data": {
                    "clicks": [
                        {"x": 100, "y": 200, "count": 50},
                        {"x": 150, "y": 250, "count": 30},
                        {"x": 200, "y": 300, "count": 20},
                    ]
                },
            },
            {
                "id": "hm2",
                "url": "https://example.com",
                "type": "scroll",
                "data": {
                    "scroll_depth": [
                        {"depth": 25, "percentage": 80},
                        {"depth": 50, "percentage": 60},
                        {"depth": 75, "percentage": 40},
                        {"depth": 100, "percentage": 20},
                    ]
                },
            },
        ]
    }


@pytest.fixture
def mock_sentiment_results():
    """Mock sentiment analysis results."""
    return [
        {
            "text": "The interface is confusing",
            "sentiment": "negative",
            "score": -0.7,
            "confidence": 0.85,
        },
        {
            "text": "Love the new design!",
            "sentiment": "positive",
            "score": 0.9,
            "confidence": 0.92,
        },
        {
            "text": "Cannot find the search button",
            "sentiment": "negative",
            "score": -0.6,
            "confidence": 0.78,
        },
    ]


@pytest.fixture
def mock_heuristic_evaluation():
    """Mock Nielsen's 10 heuristics evaluation."""
    return {
        "heuristics": [
            {
                "id": "H1",
                "name": "Visibility of system status",
                "score": 7,
                "findings": [
                    "Loading indicators present",
                    "Missing progress feedback on form submission",
                ],
                "severity": "medium",
            },
            {
                "id": "H2",
                "name": "Match between system and real world",
                "score": 8,
                "findings": [
                    "Clear, familiar language used",
                    "Icons match industry standards",
                ],
                "severity": "low",
            },
            {
                "id": "H3",
                "name": "User control and freedom",
                "score": 6,
                "findings": [
                    "Missing undo functionality",
                    "No clear exit from modal dialogs",
                ],
                "severity": "high",
            },
        ],
        "overall_score": 7.0,
        "total_issues": 5,
        "critical_issues": 1,
    }


@pytest.fixture
def mock_playwright_page():
    """Mock Playwright page object."""
    page = AsyncMock()
    page.goto = AsyncMock()
    page.content = AsyncMock(return_value="<html><body>Test</body></html>")
    page.title = AsyncMock(return_value="Test Page")
    page.url = "https://example.com"
    page.viewport_size = {"width": 1920, "height": 1080}
    page.screenshot = AsyncMock()
    page.evaluate = AsyncMock()
    return page


@pytest.fixture
def mock_playwright_browser():
    """Mock Playwright browser object."""
    browser = AsyncMock()
    page = AsyncMock()
    context = AsyncMock()
    context.new_page = AsyncMock(return_value=page)
    browser.new_context = AsyncMock(return_value=context)
    return browser


@pytest.fixture
def sample_wcag_violations():
    """Sample WCAG violation data."""
    return [
        {
            "rule": "WCAG2AA.Principle1.Guideline1_4.1_4_3.G18.Fail",
            "type": "error",
            "code": "color-contrast",
            "message": "Text has insufficient contrast ratio",
            "context": '<p style="color: #777;">',
            "selector": "html > body > p:nth-child(2)",
            "runner": "axe",
            "wcag_level": "AA",
            "wcag_criterion": "1.4.3",
        },
        {
            "rule": "WCAG2AA.Principle1.Guideline1_1.1_1_1.H37",
            "type": "error",
            "code": "image-alt",
            "message": "Image missing alt attribute",
            "context": '<img src="image.jpg">',
            "selector": "html > body > img:nth-child(1)",
            "runner": "axe",
            "wcag_level": "A",
            "wcag_criterion": "1.1.1",
        },
    ]


@pytest.fixture
def sample_remediation_guide():
    """Sample remediation guide data."""
    return {
        "violation_id": "image-alt",
        "wcag_criterion": "1.1.1",
        "level": "A",
        "title": "Images must have alternate text",
        "description": "All images must have meaningful alternative text",
        "impact": "critical",
        "remediation_steps": [
            "Add alt attribute to all <img> elements",
            "Provide descriptive text that conveys the image content",
            'Use empty alt="" for decorative images',
        ],
        "code_example_before": '<img src="logo.png">',
        "code_example_after": '<img src="logo.png" alt="Company Logo">',
        "resources": [
            "https://www.w3.org/WAI/WCAG21/Understanding/non-text-content.html"
        ],
    }


@pytest.fixture
def mock_github_client():
    """Mock GitHub API client."""
    client = Mock()
    client.create_issue = Mock(return_value={"number": 123, "url": "https://..."})
    client.get_issues = Mock(return_value=[])
    client.update_issue = Mock()
    return client


# Utility functions for tests


def create_mock_audit_result(
    violations: int = 3, warnings: int = 2, notices: int = 5
) -> Dict:
    """Create mock accessibility audit result."""
    return {
        "url": "https://example.com",
        "timestamp": "2024-01-01T00:00:00Z",
        "violations": violations,
        "warnings": warnings,
        "notices": notices,
        "score": max(0, 100 - (violations * 10) - (warnings * 5)),
        "wcag_level": "AA",
        "details": [],
    }


def create_mock_feedback_batch(count: int = 100) -> List[Dict]:
    """Create batch of mock feedback items."""
    sentiments = ["positive", "negative", "neutral"]
    categories = ["usability", "design", "navigation", "performance", "accessibility"]

    feedback_items = []
    for i in range(count):
        feedback_items.append(
            {
                "id": f"fb{i}",
                "timestamp": f"2024-01-01T{i%24:02d}:00:00Z",
                "user_id": f"user{i}",
                "feedback": f"Test feedback {i}",
                "rating": (i % 5) + 1,
                "category": categories[i % len(categories)],
                "sentiment": sentiments[i % len(sentiments)],
                "source": "survey",
            }
        )

    return feedback_items


@pytest.fixture
def large_feedback_dataset():
    """Create large feedback dataset for performance testing."""
    return create_mock_feedback_batch(1000)


# Async fixtures


@pytest.fixture
async def async_temp_dir():
    """Async temporary directory fixture."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
async def mock_async_http_client():
    """Mock async HTTP client."""
    client = AsyncMock()
    client.get = AsyncMock()
    client.post = AsyncMock()
    return client
