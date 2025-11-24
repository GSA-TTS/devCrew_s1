"""
Browser Automation Module.

Provides browser automation capabilities using Playwright for JavaScript rendering,
screenshot capture, network monitoring, and dynamic content extraction.
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from playwright.async_api import Browser, BrowserContext, Page, Playwright, Response
from playwright.async_api import TimeoutError as PlaywrightTimeoutError
from playwright.async_api import async_playwright
from pydantic import BaseModel, Field, field_validator


class BrowserAutomationError(Exception):
    """Base exception for browser automation errors."""

    pass


class RenderTimeoutError(BrowserAutomationError):
    """Raised when page rendering times out."""

    pass


class NavigationError(BrowserAutomationError):
    """Raised when navigation fails."""

    pass


class BrowserType(str, Enum):
    """Supported browser types."""

    CHROMIUM = "chromium"
    FIREFOX = "firefox"
    WEBKIT = "webkit"


class WaitStrategy(str, Enum):
    """Wait strategies for page loading."""

    LOAD = "load"
    DOMCONTENTLOADED = "domcontentloaded"
    NETWORKIDLE = "networkidle"
    COMMIT = "commit"


class ViewportConfig(BaseModel):
    """Viewport configuration for responsive testing."""

    width: int = Field(default=1920, ge=320, le=7680)
    height: int = Field(default=1080, ge=240, le=4320)
    device_scale_factor: float = Field(default=1.0, ge=0.5, le=3.0)
    is_mobile: bool = Field(default=False)
    has_touch: bool = Field(default=False)

    @field_validator("width", "height")
    @classmethod
    def validate_dimension(cls, v: int) -> int:
        """Validate viewport dimensions."""
        if v < 320:
            raise ValueError("Dimension must be at least 320 pixels")
        return v


class BrowserConfig(BaseModel):
    """Browser-specific configuration settings."""

    browser_type: BrowserType = Field(default=BrowserType.CHROMIUM)
    headless: bool = Field(default=True)
    timeout: int = Field(default=30000, ge=1000, le=300000)
    slow_mo: int = Field(default=0, ge=0, le=5000)
    args: List[str] = Field(default_factory=list)
    proxy: Optional[Dict[str, str]] = Field(default=None)
    downloads_path: Optional[str] = Field(default=None)
    ignore_https_errors: bool = Field(default=False)
    java_script_enabled: bool = Field(default=True)

    @field_validator("timeout")
    @classmethod
    def validate_timeout(cls, v: int) -> int:
        """Validate timeout is reasonable."""
        if v < 1000:
            raise ValueError("Timeout must be at least 1000ms")
        if v > 300000:
            raise ValueError("Timeout must not exceed 300000ms (5 minutes)")
        return v


class RenderConfig(BaseModel):
    """Configuration for browser rendering."""

    browser_type: BrowserType = Field(default=BrowserType.CHROMIUM)
    headless: bool = Field(default=True)
    viewport: ViewportConfig = Field(default_factory=ViewportConfig)
    wait_strategy: WaitStrategy = Field(default=WaitStrategy.NETWORKIDLE)
    timeout: int = Field(default=30000, ge=1000, le=300000)
    user_agent: Optional[str] = Field(default=None)
    extra_http_headers: Dict[str, str] = Field(default_factory=dict)
    ignore_https_errors: bool = Field(default=False)
    java_script_enabled: bool = Field(default=True)
    block_images: bool = Field(default=False)
    block_media: bool = Field(default=False)
    geolocation: Optional[Dict[str, float]] = Field(default=None)
    timezone_id: Optional[str] = Field(default=None)
    locale: Optional[str] = Field(default=None)
    permissions: List[str] = Field(default_factory=list)
    proxy: Optional[Dict[str, str]] = Field(default=None)

    @field_validator("timeout")
    @classmethod
    def validate_timeout(cls, v: int) -> int:
        """Validate timeout is reasonable."""
        if v < 1000:
            raise ValueError("Timeout must be at least 1000ms")
        if v > 300000:
            raise ValueError("Timeout must not exceed 300000ms")
        return v


class NetworkRequest(BaseModel):
    """Network request information."""

    url: str
    method: str
    resource_type: str
    status: Optional[int] = None
    status_text: Optional[str] = None
    headers: Dict[str, str] = Field(default_factory=dict)
    timing: Dict[str, float] = Field(default_factory=dict)
    size: Optional[int] = None


class ConsoleMessage(BaseModel):
    """Console message from browser."""

    type: str
    text: str
    location: Optional[Dict[str, Any]] = None
    timestamp: float


class RenderedPage(BaseModel):
    """Result of page rendering with all collected data."""

    url: str
    final_url: Optional[str] = None
    html: str
    title: Optional[str] = None
    screenshot: Optional[str] = None
    network_requests: List[NetworkRequest] = Field(default_factory=list)
    console_logs: List[ConsoleMessage] = Field(default_factory=list)
    render_time: float
    metadata: Dict[str, Any] = Field(default_factory=dict)
    cookies: List[Dict[str, Any]] = Field(default_factory=list)
    local_storage: Dict[str, str] = Field(default_factory=dict)
    session_storage: Dict[str, str] = Field(default_factory=dict)
    performance_metrics: Dict[str, Any] = Field(default_factory=dict)


@dataclass
class BrowserSession:
    """Browser session container."""

    playwright: Playwright
    browser: Browser
    context: BrowserContext
    page: Page
    created_at: float = field(default_factory=time.time)


class BrowserAutomation:
    """
    Browser automation class using Playwright.

    Provides comprehensive browser automation capabilities including JavaScript
    rendering, screenshot capture, network monitoring, and dynamic content
    extraction.
    """

    def __init__(self, config: RenderConfig) -> None:
        """
        Initialize browser automation.

        Args:
            config: Render configuration settings

        Raises:
            BrowserAutomationError: If initialization fails
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        self._playwright: Optional[Playwright] = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        self._page: Optional[Page] = None
        self._sessions: List[BrowserSession] = []
        self._network_requests: List[NetworkRequest] = []
        self._console_messages: List[ConsoleMessage] = []

    async def __aenter__(self) -> "BrowserAutomation":
        """
        Enter async context manager.

        Returns:
            Self for context manager protocol

        Raises:
            BrowserAutomationError: If browser initialization fails
        """
        try:
            await self._initialize_browser()
            return self
        except Exception as e:
            await self._cleanup()
            raise BrowserAutomationError(
                f"Failed to initialize browser: {str(e)}"
            ) from e

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """
        Exit async context manager.

        Args:
            exc_type: Exception type if raised
            exc_val: Exception value if raised
            exc_tb: Exception traceback if raised
        """
        await self._cleanup()

    async def _initialize_browser(self) -> None:
        """
        Initialize Playwright browser and context.

        Raises:
            BrowserAutomationError: If browser initialization fails
        """
        try:
            self._playwright = await async_playwright().start()

            browser_args = []
            if self.config.proxy is None:
                browser_args.append("--disable-blink-features=AutomationControlled")

            browser_kwargs: Dict[str, Any] = {
                "headless": self.config.headless,
                "args": browser_args,
            }

            if self.config.proxy:
                browser_kwargs["proxy"] = self.config.proxy

            if self.config.browser_type == BrowserType.CHROMIUM:
                self._browser = await self._playwright.chromium.launch(**browser_kwargs)
            elif self.config.browser_type == BrowserType.FIREFOX:
                self._browser = await self._playwright.firefox.launch(**browser_kwargs)
            elif self.config.browser_type == BrowserType.WEBKIT:
                self._browser = await self._playwright.webkit.launch(**browser_kwargs)
            else:
                raise BrowserAutomationError(
                    f"Unsupported browser type: {self.config.browser_type}"
                )

            context_kwargs: Dict[str, Any] = {
                "viewport": {
                    "width": self.config.viewport.width,
                    "height": self.config.viewport.height,
                },
                "device_scale_factor": self.config.viewport.device_scale_factor,
                "is_mobile": self.config.viewport.is_mobile,
                "has_touch": self.config.viewport.has_touch,
                "java_script_enabled": self.config.java_script_enabled,
                "ignore_https_errors": self.config.ignore_https_errors,
            }

            if self.config.user_agent:
                context_kwargs["user_agent"] = self.config.user_agent

            if self.config.extra_http_headers:
                context_kwargs["extra_http_headers"] = self.config.extra_http_headers

            if self.config.geolocation:
                context_kwargs["geolocation"] = self.config.geolocation

            if self.config.timezone_id:
                context_kwargs["timezone_id"] = self.config.timezone_id

            if self.config.locale:
                context_kwargs["locale"] = self.config.locale

            if self.config.permissions:
                context_kwargs["permissions"] = self.config.permissions

            self._context = await self._browser.new_context(**context_kwargs)

            if self.config.block_images or self.config.block_media:
                await self._context.route(
                    "**/*",
                    lambda route: self._handle_route(route),
                )

            self._page = await self._context.new_page()
            self._page.set_default_timeout(self.config.timeout)

            self._setup_event_listeners()

            self.logger.info(f"Browser initialized: {self.config.browser_type.value}")

        except Exception as e:
            raise BrowserAutomationError(
                f"Failed to initialize browser: {str(e)}"
            ) from e

    async def _handle_route(self, route: Any) -> None:
        """
        Handle route interception for resource blocking.

        Args:
            route: Playwright route object
        """
        resource_type = route.request.resource_type
        if self.config.block_images and resource_type == "image":
            await route.abort()
        elif self.config.block_media and resource_type in ["media", "font"]:
            await route.abort()
        else:
            await route.continue_()

    def _setup_event_listeners(self) -> None:
        """Set up event listeners for network and console monitoring."""
        if self._page is None:
            return

        self._page.on("response", self._on_response)
        self._page.on("console", self._on_console)
        self._page.on("pageerror", self._on_page_error)

    def _on_response(self, response: Response) -> None:
        """
        Handle response events.

        Args:
            response: Playwright response object
        """
        try:
            request = response.request
            network_req = NetworkRequest(
                url=request.url,
                method=request.method,
                resource_type=request.resource_type,
                status=response.status,
                status_text=response.status_text,
                headers=dict(response.headers),
                timing={},
            )
            self._network_requests.append(network_req)
        except Exception as e:
            self.logger.warning(f"Failed to capture network request: {e}")

    def _on_console(self, msg: Any) -> None:
        """
        Handle console message events.

        Args:
            msg: Playwright console message object
        """
        try:
            console_msg = ConsoleMessage(
                type=msg.type,
                text=msg.text,
                location=msg.location,
                timestamp=time.time(),
            )
            self._console_messages.append(console_msg)
        except Exception as e:
            self.logger.warning(f"Failed to capture console message: {e}")

    def _on_page_error(self, error: Any) -> None:
        """
        Handle page error events.

        Args:
            error: Page error object
        """
        self.logger.warning(f"Page error: {error}")

    async def render_page(
        self,
        url: str,
        wait_for_selector: Optional[str] = None,
        execute_script: Optional[str] = None,
    ) -> RenderedPage:
        """
        Render page with JavaScript execution and collect all data.

        Args:
            url: URL to render
            wait_for_selector: Optional CSS selector to wait for
            execute_script: Optional JavaScript to execute

        Returns:
            RenderedPage object with all collected data

        Raises:
            NavigationError: If navigation fails
            RenderTimeoutError: If rendering times out
            BrowserAutomationError: For other browser errors
        """
        if self._page is None:
            raise BrowserAutomationError("Browser not initialized")

        start_time = time.time()
        self._network_requests.clear()
        self._console_messages.clear()

        try:
            response = await self._page.goto(
                url,
                wait_until=self.config.wait_strategy.value,
                timeout=self.config.timeout,
            )

            if response is None:
                raise NavigationError(f"Failed to navigate to {url}")

            if not response.ok:
                self.logger.warning(f"Response status {response.status} for {url}")

            if wait_for_selector:
                try:
                    await self._page.wait_for_selector(
                        wait_for_selector, timeout=self.config.timeout
                    )
                except PlaywrightTimeoutError as e:
                    raise RenderTimeoutError(
                        f"Timeout waiting for selector: {wait_for_selector}"
                    ) from e

            if execute_script:
                try:
                    await self._page.evaluate(execute_script)
                except Exception as e:
                    self.logger.warning(f"Script execution failed: {e}")

            html = await self._page.content()
            title = await self._page.title()
            final_url = self._page.url

            cookies = await self._context.cookies()  # type: ignore

            local_storage = await self._page.evaluate(
                "() => Object.assign({}, window.localStorage)"
            )
            session_storage = await self._page.evaluate(
                "() => Object.assign({}, window.sessionStorage)"
            )

            performance_metrics = await self._get_performance_metrics()

            render_time = time.time() - start_time

            return RenderedPage(
                url=url,
                final_url=final_url,
                html=html,
                title=title,
                screenshot=None,
                network_requests=self._network_requests.copy(),
                console_logs=self._console_messages.copy(),
                render_time=render_time,
                metadata={
                    "status": response.status,
                    "status_text": response.status_text,
                    "content_type": response.headers.get("content-type"),
                },
                cookies=cookies,
                local_storage=local_storage,
                session_storage=session_storage,
                performance_metrics=performance_metrics,
            )

        except PlaywrightTimeoutError as e:
            raise RenderTimeoutError(f"Timeout rendering page {url}: {str(e)}") from e
        except NavigationError:
            raise
        except Exception as e:
            raise BrowserAutomationError(
                f"Failed to render page {url}: {str(e)}"
            ) from e

    async def take_screenshot(
        self,
        url: str,
        full_page: bool = True,
        selector: Optional[str] = None,
        wait_for_selector: Optional[str] = None,
    ) -> bytes:
        """
        Capture screenshot of page or specific element.

        Args:
            url: URL to screenshot
            full_page: Capture full scrollable page
            selector: CSS selector of element to screenshot
            wait_for_selector: Optional selector to wait for before capture

        Returns:
            Screenshot as bytes

        Raises:
            NavigationError: If navigation fails
            RenderTimeoutError: If rendering times out
            BrowserAutomationError: For other errors
        """
        if self._page is None:
            raise BrowserAutomationError("Browser not initialized")

        try:
            await self._page.goto(
                url,
                wait_until=self.config.wait_strategy.value,
                timeout=self.config.timeout,
            )

            if wait_for_selector:
                try:
                    await self._page.wait_for_selector(
                        wait_for_selector, timeout=self.config.timeout
                    )
                except PlaywrightTimeoutError as e:
                    raise RenderTimeoutError(
                        f"Timeout waiting for selector: {wait_for_selector}"
                    ) from e

            if selector:
                element = await self._page.query_selector(selector)
                if element is None:
                    raise BrowserAutomationError(f"Element not found: {selector}")
                screenshot_bytes = await element.screenshot()
            else:
                screenshot_bytes = await self._page.screenshot(full_page=full_page)

            return screenshot_bytes

        except PlaywrightTimeoutError as e:
            raise RenderTimeoutError(
                f"Timeout taking screenshot of {url}: {str(e)}"
            ) from e
        except Exception as e:
            raise BrowserAutomationError(f"Failed to take screenshot: {str(e)}") from e

    async def wait_for_selector(
        self, selector: str, timeout: Optional[int] = None, state: str = "visible"
    ) -> bool:
        """
        Wait for element to be present on page.

        Args:
            selector: CSS selector to wait for
            timeout: Optional timeout override in milliseconds
            state: Element state to wait for (visible, attached, hidden)

        Returns:
            True if element found, False otherwise

        Raises:
            BrowserAutomationError: If browser not initialized
        """
        if self._page is None:
            raise BrowserAutomationError("Browser not initialized")

        wait_timeout = timeout if timeout is not None else self.config.timeout

        try:
            await self._page.wait_for_selector(
                selector, timeout=wait_timeout, state=state
            )
            return True
        except PlaywrightTimeoutError:
            return False
        except Exception as e:
            self.logger.warning(f"Error waiting for selector {selector}: {e}")
            return False

    async def extract_rendered_html(
        self, url: str, wait_for_selector: Optional[str] = None
    ) -> str:
        """
        Get fully rendered HTML after JavaScript execution.

        Args:
            url: URL to extract HTML from
            wait_for_selector: Optional selector to wait for

        Returns:
            Rendered HTML as string

        Raises:
            NavigationError: If navigation fails
            RenderTimeoutError: If rendering times out
            BrowserAutomationError: For other errors
        """
        if self._page is None:
            raise BrowserAutomationError("Browser not initialized")

        try:
            await self._page.goto(
                url,
                wait_until=self.config.wait_strategy.value,
                timeout=self.config.timeout,
            )

            if wait_for_selector:
                try:
                    await self._page.wait_for_selector(
                        wait_for_selector, timeout=self.config.timeout
                    )
                except PlaywrightTimeoutError as e:
                    raise RenderTimeoutError(
                        f"Timeout waiting for selector: {wait_for_selector}"
                    ) from e

            html = await self._page.content()
            return html

        except PlaywrightTimeoutError as e:
            raise RenderTimeoutError(
                f"Timeout extracting HTML from {url}: {str(e)}"
            ) from e
        except Exception as e:
            raise BrowserAutomationError(f"Failed to extract HTML: {str(e)}") from e

    async def get_network_requests(
        self, url: str, filter_type: Optional[str] = None
    ) -> List[NetworkRequest]:
        """
        Capture network activity during page load.

        Args:
            url: URL to monitor
            filter_type: Optional resource type filter

        Returns:
            List of network requests

        Raises:
            NavigationError: If navigation fails
            BrowserAutomationError: For other errors
        """
        if self._page is None:
            raise BrowserAutomationError("Browser not initialized")

        self._network_requests.clear()

        try:
            await self._page.goto(
                url,
                wait_until=self.config.wait_strategy.value,
                timeout=self.config.timeout,
            )

            requests = self._network_requests.copy()

            if filter_type:
                requests = [req for req in requests if req.resource_type == filter_type]

            return requests

        except Exception as e:
            raise BrowserAutomationError(
                f"Failed to capture network requests: {str(e)}"
            ) from e

    async def execute_script(self, script: str, *args: Any) -> Any:
        """
        Execute JavaScript in page context.

        Args:
            script: JavaScript code to execute
            *args: Arguments to pass to script

        Returns:
            Script return value

        Raises:
            BrowserAutomationError: If execution fails
        """
        if self._page is None:
            raise BrowserAutomationError("Browser not initialized")

        try:
            result = await self._page.evaluate(script, *args)
            return result
        except Exception as e:
            raise BrowserAutomationError(f"Failed to execute script: {str(e)}") from e

    async def fill_form(
        self, selector: str, value: str, wait_timeout: Optional[int] = None
    ) -> None:
        """
        Fill form field with value.

        Args:
            selector: CSS selector for form field
            value: Value to fill
            wait_timeout: Optional timeout for waiting

        Raises:
            BrowserAutomationError: If operation fails
        """
        if self._page is None:
            raise BrowserAutomationError("Browser not initialized")

        timeout = wait_timeout if wait_timeout is not None else self.config.timeout

        try:
            await self._page.fill(selector, value, timeout=timeout)
        except Exception as e:
            raise BrowserAutomationError(
                f"Failed to fill form field {selector}: {str(e)}"
            ) from e

    async def click_element(
        self, selector: str, wait_timeout: Optional[int] = None
    ) -> None:
        """
        Click element on page.

        Args:
            selector: CSS selector for element
            wait_timeout: Optional timeout for waiting

        Raises:
            BrowserAutomationError: If operation fails
        """
        if self._page is None:
            raise BrowserAutomationError("Browser not initialized")

        timeout = wait_timeout if wait_timeout is not None else self.config.timeout

        try:
            await self._page.click(selector, timeout=timeout)
        except Exception as e:
            raise BrowserAutomationError(
                f"Failed to click element {selector}: {str(e)}"
            ) from e

    async def scroll_to_bottom(self, wait_time: float = 1.0) -> None:
        """
        Scroll page to bottom to trigger lazy loading.

        Args:
            wait_time: Time to wait between scrolls in seconds

        Raises:
            BrowserAutomationError: If operation fails
        """
        if self._page is None:
            raise BrowserAutomationError("Browser not initialized")

        try:
            await self._page.evaluate(
                """
                async () => {
                    await new Promise((resolve) => {
                        let totalHeight = 0;
                        const distance = 100;
                        const timer = setInterval(() => {
                            const scrollHeight = document.body.scrollHeight;
                            window.scrollBy(0, distance);
                            totalHeight += distance;

                            if(totalHeight >= scrollHeight){
                                clearInterval(timer);
                                resolve();
                            }
                        }, 100);
                    });
                }
            """
            )
            await asyncio.sleep(wait_time)
        except Exception as e:
            raise BrowserAutomationError(f"Failed to scroll page: {str(e)}") from e

    async def get_cookies(self) -> List[Dict[str, Any]]:
        """
        Get all cookies from current context.

        Returns:
            List of cookie dictionaries

        Raises:
            BrowserAutomationError: If browser not initialized
        """
        if self._context is None:
            raise BrowserAutomationError("Browser context not initialized")

        try:
            cookies = await self._context.cookies()
            return cookies
        except Exception as e:
            raise BrowserAutomationError(f"Failed to get cookies: {str(e)}") from e

    async def set_cookies(self, cookies: List[Dict[str, Any]]) -> None:
        """
        Set cookies in current context.

        Args:
            cookies: List of cookie dictionaries

        Raises:
            BrowserAutomationError: If operation fails
        """
        if self._context is None:
            raise BrowserAutomationError("Browser context not initialized")

        try:
            await self._context.add_cookies(cookies)
        except Exception as e:
            raise BrowserAutomationError(f"Failed to set cookies: {str(e)}") from e

    async def _get_performance_metrics(self) -> Dict[str, Any]:
        """
        Get performance metrics from page.

        Returns:
            Dictionary of performance metrics
        """
        if self._page is None:
            return {}

        try:
            metrics = await self._page.evaluate(
                """
                () => {
                    const perfData = window.performance.timing;
                    const navigation = performance.getEntriesByType('navigation')[0];
                    return {
                        domContentLoaded: perfData.domContentLoadedEventEnd -
                            perfData.navigationStart,
                        loadComplete: perfData.loadEventEnd -
                            perfData.navigationStart,
                        domInteractive: perfData.domInteractive -
                            perfData.navigationStart,
                        firstPaint: navigation ?
                            navigation.responseEnd - navigation.fetchStart : 0,
                    };
                }
            """
            )
            return metrics
        except Exception as e:
            self.logger.warning(f"Failed to get performance metrics: {e}")
            return {}

    async def create_new_page(self) -> Page:
        """
        Create a new page in the current context.

        Returns:
            New page instance

        Raises:
            BrowserAutomationError: If context not initialized
        """
        if self._context is None:
            raise BrowserAutomationError("Browser context not initialized")

        try:
            page = await self._context.new_page()
            page.set_default_timeout(self.config.timeout)
            return page
        except Exception as e:
            raise BrowserAutomationError(f"Failed to create new page: {str(e)}") from e

    async def _cleanup(self) -> None:
        """Clean up browser resources."""
        try:
            if self._page:
                await self._page.close()
                self._page = None

            if self._context:
                await self._context.close()
                self._context = None

            if self._browser:
                await self._browser.close()
                self._browser = None

            if self._playwright:
                await self._playwright.stop()
                self._playwright = None

            self.logger.info("Browser cleanup completed")

        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")


async def render_page_simple(
    url: str,
    headless: bool = True,
    timeout: int = 30000,
    wait_strategy: WaitStrategy = WaitStrategy.NETWORKIDLE,
) -> RenderedPage:
    """
    Simple helper function to render a single page.

    Args:
        url: URL to render
        headless: Run in headless mode
        timeout: Timeout in milliseconds
        wait_strategy: Wait strategy for page loading

    Returns:
        RenderedPage object

    Raises:
        BrowserAutomationError: If rendering fails
    """
    config = RenderConfig(
        headless=headless,
        timeout=timeout,
        wait_strategy=wait_strategy,
    )

    async with BrowserAutomation(config) as browser:
        return await browser.render_page(url)


async def take_screenshot_simple(
    url: str,
    output_path: Union[str, Path],
    full_page: bool = True,
    headless: bool = True,
) -> None:
    """
    Simple helper function to take a screenshot and save to file.

    Args:
        url: URL to screenshot
        output_path: Path to save screenshot
        full_page: Capture full scrollable page
        headless: Run in headless mode

    Raises:
        BrowserAutomationError: If screenshot fails
    """
    config = RenderConfig(headless=headless)

    async with BrowserAutomation(config) as browser:
        screenshot_bytes = await browser.take_screenshot(url, full_page=full_page)
        Path(output_path).write_bytes(screenshot_bytes)
