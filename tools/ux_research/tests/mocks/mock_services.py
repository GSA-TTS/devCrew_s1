"""
Mock service implementations for testing.

Provides mock implementations of:
- Playwright browser
- Google Analytics API
- Hotjar API
- GitHub API
- External services
"""

from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, Mock


class MockPlaywrightBrowser:
    """Mock Playwright browser for testing."""

    def __init__(self):
        """Initialize mock browser."""
        self.contexts = []
        self.is_connected = True

    async def new_context(self, **kwargs) -> "MockBrowserContext":
        """Create new browser context."""
        context = MockBrowserContext(**kwargs)
        self.contexts.append(context)
        return context

    async def close(self):
        """Close browser."""
        self.is_connected = False
        for context in self.contexts:
            await context.close()


class MockBrowserContext:
    """Mock browser context."""

    def __init__(self, **kwargs):
        """Initialize mock context."""
        self.viewport = kwargs.get("viewport", {"width": 1920, "height": 1080})
        self.user_agent = kwargs.get("user_agent", "Mozilla/5.0")
        self.pages = []
        self.is_closed = False

    async def new_page(self) -> "MockPage":
        """Create new page."""
        page = MockPage(context=self)
        self.pages.append(page)
        return page

    async def close(self):
        """Close context."""
        self.is_closed = True
        for page in self.pages:
            await page.close()


class MockPage:
    """Mock Playwright page."""

    def __init__(self, context: MockBrowserContext):
        """Initialize mock page."""
        self.context = context
        self.url = ""
        self.title_text = ""
        self.content_html = ""
        self.viewport = context.viewport
        self.is_closed = False
        self.screenshots = []

    async def goto(self, url: str, **kwargs):
        """Navigate to URL."""
        self.url = url
        # Simulate page load
        self.content_html = f"<html><body>Mock content for {url}</body></html>"
        self.title_text = f"Mock Title for {url}"

    async def content(self) -> str:
        """Get page content."""
        return self.content_html

    async def title(self) -> str:
        """Get page title."""
        return self.title_text

    async def screenshot(self, **kwargs) -> bytes:
        """Take screenshot."""
        screenshot_data = b"mock_screenshot_data"
        self.screenshots.append(screenshot_data)
        return screenshot_data

    async def evaluate(self, script: str, **kwargs) -> Any:
        """Evaluate JavaScript."""
        # Return mock axe results if axe script
        if "axe" in script.lower():
            return {
                "violations": [],
                "passes": [],
                "incomplete": [],
                "inapplicable": [],
            }
        return None

    async def close(self):
        """Close page."""
        self.is_closed = True

    async def set_viewport_size(self, viewport: Dict[str, int]):
        """Set viewport size."""
        self.viewport = viewport


class MockGoogleAnalyticsClient:
    """Mock Google Analytics API client."""

    def __init__(self, credentials: Optional[Dict] = None):
        """Initialize mock GA client."""
        self.credentials = credentials
        self.is_authenticated = True

    async def get_report(
        self,
        view_id: str,
        start_date: str,
        end_date: str,
        metrics: List[str],
        dimensions: Optional[List[str]] = None,
    ) -> Dict:
        """Get analytics report."""
        return {
            "reports": [
                {
                    "data": {
                        "rows": [
                            {
                                "dimensions": ["/"],
                                "metrics": [{"values": ["1000", "120.5", "35.2"]}],
                            }
                        ]
                    }
                }
            ]
        }

    async def get_realtime_data(self, view_id: str) -> Dict:
        """Get real-time analytics data."""
        return {"activeUsers": 42, "topPages": ["/", "/products", "/about"]}


class MockHotjarClient:
    """Mock Hotjar API client."""

    def __init__(self, api_key: str):
        """Initialize mock Hotjar client."""
        self.api_key = api_key
        self.is_authenticated = True

    async def get_heatmaps(self, site_id: str) -> Dict:
        """Get heatmaps for site."""
        return {
            "heatmaps": [
                {
                    "id": "hm_001",
                    "url": "https://example.com",
                    "type": "click",
                    "data": {"clicks": [{"x": 100, "y": 200, "count": 50}]},
                }
            ]
        }

    async def get_recordings(self, site_id: str, limit: int = 10) -> Dict:
        """Get session recordings."""
        return {
            "recordings": [
                {"id": "rec_001", "duration": 300, "pages": ["/", "/products"]}
            ]
        }

    async def get_surveys(self, site_id: str) -> Dict:
        """Get survey responses."""
        return {"surveys": [{"id": "srv_001", "responses": 100, "nps_score": 42}]}


class MockGitHubClient:
    """Mock GitHub API client."""

    def __init__(self, token: str):
        """Initialize mock GitHub client."""
        self.token = token
        self.is_authenticated = True
        self.issues = []

    async def create_issue(
        self, repo: str, title: str, body: str, labels: Optional[List[str]] = None
    ) -> Dict:
        """Create GitHub issue."""
        issue = {
            "number": len(self.issues) + 1,
            "title": title,
            "body": body,
            "labels": labels or [],
            "state": "open",
            "url": f"https://github.com/{repo}/issues/{len(self.issues) + 1}",
        }
        self.issues.append(issue)
        return issue

    async def get_issues(
        self, repo: str, state: str = "open", labels: Optional[List[str]] = None
    ) -> List[Dict]:
        """Get repository issues."""
        filtered_issues = self.issues

        if state:
            filtered_issues = [i for i in filtered_issues if i["state"] == state]

        if labels:
            filtered_issues = [
                i
                for i in filtered_issues
                if any(label in i["labels"] for label in labels)
            ]

        return filtered_issues

    async def update_issue(self, repo: str, issue_number: int, **kwargs) -> Dict:
        """Update issue."""
        for issue in self.issues:
            if issue["number"] == issue_number:
                issue.update(kwargs)
                return issue
        raise ValueError(f"Issue {issue_number} not found")

    async def close_issue(self, repo: str, issue_number: int) -> Dict:
        """Close issue."""
        return await self.update_issue(repo, issue_number, state="closed")


class MockAxeCoreEngine:
    """Mock axe-core accessibility engine."""

    def __init__(self):
        """Initialize mock axe engine."""
        self.rules_enabled = True

    async def run(self, page: MockPage, options: Optional[Dict] = None) -> Dict:
        """Run accessibility audit."""
        violations = []

        # Simulate finding violations in HTML content
        if "<img" in page.content_html and "alt=" not in page.content_html:
            violations.append(
                {
                    "id": "image-alt",
                    "impact": "critical",
                    "description": "Images must have alternate text",
                    "nodes": [{"html": "<img src='...'>"}],
                }
            )

        return {
            "violations": violations,
            "passes": [],
            "incomplete": [],
            "inapplicable": [],
            "timestamp": "2024-01-01T00:00:00Z",
            "url": page.url,
        }


class MockLighthouseRunner:
    """Mock Lighthouse audit runner."""

    def __init__(self):
        """Initialize mock Lighthouse runner."""
        self.chrome_flags = []

    async def run(self, url: str, options: Optional[Dict] = None) -> Dict:
        """Run Lighthouse audit."""
        return {
            "categories": {
                "accessibility": {"score": 0.85, "title": "Accessibility"},
                "performance": {"score": 0.90, "title": "Performance"},
                "best-practices": {"score": 0.92, "title": "Best Practices"},
                "seo": {"score": 0.88, "title": "SEO"},
            },
            "audits": {},
        }


class MockSentimentModel:
    """Mock NLP sentiment analysis model."""

    def __init__(self):
        """Initialize mock sentiment model."""
        self.is_loaded = True

    def predict(self, text: str) -> Dict[str, Any]:
        """Predict sentiment for text."""
        # Simple mock logic based on keywords
        text_lower = text.lower()

        if any(
            word in text_lower for word in ["love", "great", "excellent", "amazing"]
        ):
            return {"sentiment": "positive", "score": 0.9, "confidence": 0.85}
        elif any(word in text_lower for word in ["hate", "terrible", "awful", "bad"]):
            return {"sentiment": "negative", "score": -0.9, "confidence": 0.85}
        else:
            return {"sentiment": "neutral", "score": 0.0, "confidence": 0.70}

    def predict_batch(self, texts: List[str]) -> List[Dict[str, Any]]:
        """Predict sentiment for batch of texts."""
        return [self.predict(text) for text in texts]


class MockEmailService:
    """Mock email service for sending reports."""

    def __init__(self):
        """Initialize mock email service."""
        self.sent_emails = []

    async def send_email(
        self, to: str, subject: str, body: str, attachments: Optional[List[str]] = None
    ) -> bool:
        """Send email."""
        email = {
            "to": to,
            "subject": subject,
            "body": body,
            "attachments": attachments or [],
            "sent_at": "2024-01-01T00:00:00Z",
        }
        self.sent_emails.append(email)
        return True


class MockSlackClient:
    """Mock Slack client for notifications."""

    def __init__(self, webhook_url: str):
        """Initialize mock Slack client."""
        self.webhook_url = webhook_url
        self.messages = []

    async def send_message(
        self, channel: str, text: str, attachments: Optional[List[Dict]] = None
    ) -> Dict:
        """Send Slack message."""
        message = {
            "channel": channel,
            "text": text,
            "attachments": attachments or [],
            "ts": "1234567890.123456",
        }
        self.messages.append(message)
        return message


# Factory functions for creating mock instances


def create_mock_playwright() -> MockPlaywrightBrowser:
    """Create mock Playwright browser instance."""
    return MockPlaywrightBrowser()


def create_mock_ga_client(
    credentials: Optional[Dict] = None,
) -> MockGoogleAnalyticsClient:
    """Create mock Google Analytics client."""
    return MockGoogleAnalyticsClient(credentials)


def create_mock_hotjar_client(api_key: str = "test_key") -> MockHotjarClient:
    """Create mock Hotjar client."""
    return MockHotjarClient(api_key)


def create_mock_github_client(token: str = "test_token") -> MockGitHubClient:
    """Create mock GitHub client."""
    return MockGitHubClient(token)


def create_mock_axe_engine() -> MockAxeCoreEngine:
    """Create mock axe-core engine."""
    return MockAxeCoreEngine()


def create_mock_lighthouse() -> MockLighthouseRunner:
    """Create mock Lighthouse runner."""
    return MockLighthouseRunner()


def create_mock_sentiment_model() -> MockSentimentModel:
    """Create mock sentiment model."""
    return MockSentimentModel()
