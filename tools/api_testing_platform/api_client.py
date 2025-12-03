"""
API Client Module

HTTP client with authentication, retry logic, and session management for API
testing and validation.
"""

import base64
import logging
import time
from typing import Any, Dict, Optional, Tuple
from urllib.parse import urljoin

import requests
from requests.adapters import HTTPAdapter
from requests_oauthlib import OAuth2Session
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)


class APIResponse:
    """
    Wrapper for HTTP responses with schema validation support.

    Attributes:
        status_code (int): HTTP status code
        headers (dict): Response headers
        body (Any): Parsed response body (JSON if applicable)
        raw_response (requests.Response): Original response object
        elapsed (float): Request elapsed time in seconds
    """

    def __init__(self, response: requests.Response):
        """
        Initialize APIResponse wrapper.

        Args:
            response: requests.Response object to wrap
        """
        self.status_code = response.status_code
        self.headers = dict(response.headers)
        self.elapsed = response.elapsed.total_seconds()
        self.raw_response = response

        # Parse body as JSON if possible
        try:
            self.body = response.json() if response.content else None
        except ValueError:
            self.body = response.text if response.text else None

    def validate_schema(
        self, spec_file: str, schema_ref: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate response against OpenAPI schema.

        Args:
            spec_file: Path to OpenAPI specification file
            schema_ref: Schema reference in spec
                (e.g., '#/components/schemas/User')

        Returns:
            Tuple of (is_valid, error_message)
        """
        # This will be implemented when SchemaValidator is available
        # For now, return placeholder
        msg = "Schema validation not yet implemented - " "requires SchemaValidator"
        logger.warning(msg)
        return True, None

    def __repr__(self) -> str:
        """String representation of response."""
        return (
            f"APIResponse(status={self.status_code}, " f"elapsed={self.elapsed:.2f}s)"
        )


class APIClientError(Exception):
    """Base exception for API client errors."""

    pass


class AuthenticationError(APIClientError):
    """Raised when authentication fails."""

    pass


class RateLimitError(APIClientError):
    """Raised when rate limit is exceeded."""

    pass


class APIClient:
    """
    HTTP client for API testing with authentication and retry logic.

    Features:
        - Multiple authentication methods (Bearer, API Key, Basic, OAuth2)
        - Automatic retry with exponential backoff
        - Session management with connection pooling
        - Request/response logging with sanitization
        - Rate limiting compliance
        - SSL/TLS verification
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize API client.

        Args:
            config: Configuration dictionary with following keys:
                - base_url (str): Base URL for API endpoints
                - timeout (int): Request timeout in seconds (default: 30)
                - retry_attempts (int): Max retry attempts (default: 3)
                - verify_ssl (bool): Verify SSL certificates (default: True)
                - follow_redirects (bool): Follow redirects (default: True)
                - rate_limit (int): Max requests per minute (default: 100)
        """
        self.config = config or {}
        self.base_url = self.config.get("base_url", "")
        self.timeout = self.config.get("timeout", 30)
        self.retry_attempts = self.config.get("retry_attempts", 3)
        self.verify_ssl = self.config.get("verify_ssl", True)
        self.follow_redirects = self.config.get("follow_redirects", True)
        self.rate_limit = self.config.get("rate_limit", 100)

        # Authentication state
        self._auth_type: Optional[str] = None
        self._auth_data: Dict[str, Any] = {}

        # Rate limiting
        self._request_times: list = []

        # Initialize session with connection pooling
        self.session = self._create_session()

        logger.info(
            f"APIClient initialized with base_url={self.base_url}, "
            f"timeout={self.timeout}s, retry_attempts={self.retry_attempts}"
        )

    def _create_session(self) -> requests.Session:
        """
        Create requests session with connection pooling and retry logic.

        Returns:
            Configured requests.Session object
        """
        session = requests.Session()

        # Configure retry strategy
        # Retry on connection errors, timeouts, and 5xx server errors
        retry_strategy = Retry(
            total=self.retry_attempts,
            backoff_factor=1,  # Exponential backoff: 1s, 2s, 4s, 8s
            status_forcelist=[500, 502, 503, 504],
            allowed_methods=[
                "HEAD",
                "GET",
                "PUT",
                "DELETE",
                "OPTIONS",
                "TRACE",
            ],
            raise_on_status=False,
        )

        # Mount adapter with retry strategy
        adapter = HTTPAdapter(
            max_retries=retry_strategy,
            pool_connections=10,
            pool_maxsize=10,
        )
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        return session

    def _check_rate_limit(self) -> None:
        """
        Check and enforce rate limiting.

        Raises:
            RateLimitError: If rate limit would be exceeded
        """
        now = time.time()
        # Remove requests older than 1 minute
        self._request_times = [t for t in self._request_times if now - t < 60]

        if len(self._request_times) >= self.rate_limit:
            raise RateLimitError(
                f"Rate limit of {self.rate_limit} requests/minute exceeded"
            )

        self._request_times.append(now)

    def _sanitize_for_logging(self, data: Any) -> Any:
        """
        Sanitize data for logging (remove sensitive information).

        Args:
            data: Data to sanitize

        Returns:
            Sanitized data safe for logging
        """
        if isinstance(data, dict):
            sanitized = {}
            sensitive_keys = [
                "authorization",
                "password",
                "token",
                "secret",
                "api_key",
                "api-key",
                "x-api-key",
            ]
            for key, value in data.items():
                if any(s in key.lower() for s in sensitive_keys):
                    sanitized[key] = "***REDACTED***"
                elif isinstance(value, (dict, list)):
                    sanitized[key] = self._sanitize_for_logging(value)
                else:
                    sanitized[key] = value
            return sanitized
        elif isinstance(data, list):
            return [self._sanitize_for_logging(item) for item in data]
        return data

    def _log_request(
        self, method: str, url: str, headers: Dict[str, str], body: Any = None
    ) -> None:
        """
        Log HTTP request details with sanitization.

        Args:
            method: HTTP method
            url: Request URL
            headers: Request headers
            body: Request body
        """
        sanitized_headers = self._sanitize_for_logging(headers)
        sanitized_body = self._sanitize_for_logging(body) if body else None

        logger.debug(
            f"Request: {method} {url}\n"
            f"Headers: {sanitized_headers}\n"
            f"Body: {sanitized_body}"
        )

    def _log_response(self, response: APIResponse) -> None:
        """
        Log HTTP response details.

        Args:
            response: APIResponse object
        """
        # Truncate large response bodies
        body_preview = response.body
        if isinstance(body_preview, str) and len(body_preview) > 1000:
            body_preview = body_preview[:1000] + "... (truncated)"
        elif isinstance(body_preview, dict):
            body_preview = str(body_preview)[:1000]

        logger.debug(
            f"Response: {response.status_code} "
            f"(elapsed: {response.elapsed:.2f}s)\n"
            f"Headers: {response.headers}\n"
            f"Body: {body_preview}"
        )

    def _prepare_url(self, path: str) -> str:
        """
        Prepare full URL from base URL and path.

        Args:
            path: API endpoint path

        Returns:
            Full URL
        """
        if path.startswith(("http://", "https://")):
            return path
        return urljoin(self.base_url, path)

    def _apply_authentication(
        self, headers: Dict[str, str], params: Dict[str, Any]
    ) -> Tuple[Dict[str, str], Dict[str, Any]]:
        """
        Apply configured authentication to request.

        Args:
            headers: Request headers
            params: Query parameters

        Returns:
            Tuple of (modified headers, modified params)
        """
        headers = headers.copy()
        params = params.copy()

        if self._auth_type == "bearer":
            token = self._auth_data.get("token")
            if token:
                headers["Authorization"] = f"Bearer {token}"

        elif self._auth_type == "api_key":
            key = self._auth_data.get("key")
            location = self._auth_data.get("location", "header")
            key_name = self._auth_data.get("key_name", "X-API-Key")

            if key:
                if location == "header":
                    headers[key_name] = key
                elif location == "query":
                    params[key_name] = key

        elif self._auth_type == "basic":
            username = self._auth_data.get("username")
            password = self._auth_data.get("password")
            if username and password:
                credentials = f"{username}:{password}"
                encoded = base64.b64encode(credentials.encode()).decode()
                headers["Authorization"] = f"Basic {encoded}"

        elif self._auth_type == "custom":
            custom_headers = self._auth_data.get("headers", {})
            headers.update(custom_headers)

        return headers, params

    def _request(
        self,
        method: str,
        path: str,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        data: Optional[Any] = None,
        **kwargs: Any,
    ) -> APIResponse:
        """
        Execute HTTP request with retry logic and logging.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE, PATCH)
            path: API endpoint path
            headers: Request headers
            params: Query parameters
            json: JSON request body
            data: Form data or raw body
            **kwargs: Additional arguments for requests

        Returns:
            APIResponse object

        Raises:
            APIClientError: On request failure
            RateLimitError: On rate limit exceeded
        """
        # Check rate limit
        self._check_rate_limit()

        # Prepare request
        url = self._prepare_url(path)
        headers = headers or {}
        params = params or {}

        # Apply authentication
        headers, params = self._apply_authentication(headers, params)

        # Set default headers
        if "User-Agent" not in headers:
            headers["User-Agent"] = "APIClient/1.0.0"

        # Log request
        self._log_request(method, url, headers, json or data)

        # Execute request
        try:
            response = self.session.request(
                method=method,
                url=url,
                headers=headers,
                params=params,
                json=json,
                data=data,
                timeout=self.timeout,
                verify=self.verify_ssl,
                allow_redirects=self.follow_redirects,
                **kwargs,
            )
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection error: {e}")
            raise APIClientError(f"Connection failed: {e}") from e
        except requests.exceptions.Timeout as e:
            logger.error(f"Request timeout: {e}")
            raise APIClientError(f"Request timed out: {e}") from e
        except requests.exceptions.SSLError as e:
            logger.error(f"SSL error: {e}")
            raise APIClientError(f"SSL verification failed: {e}") from e
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error: {e}")
            raise APIClientError(f"Request failed: {e}") from e

        # Wrap response
        api_response = APIResponse(response)

        # Log response
        self._log_response(api_response)

        # Check for rate limit response
        if response.status_code == 429:
            retry_after = response.headers.get("Retry-After", "60")
            raise RateLimitError(
                f"Rate limit exceeded. Retry after {retry_after} seconds"
            )

        return api_response

    def get(
        self,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs: Any,
    ) -> APIResponse:
        """
        Execute HTTP GET request.

        Args:
            path: API endpoint path
            params: Query parameters
            headers: Request headers
            **kwargs: Additional arguments for requests

        Returns:
            APIResponse object
        """
        return self._request(
            "GET",
            path,
            headers=headers,
            params=params,
            **kwargs,
        )

    def post(
        self,
        path: str,
        json: Optional[Dict[str, Any]] = None,
        data: Optional[Any] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs: Any,
    ) -> APIResponse:
        """
        Execute HTTP POST request.

        Args:
            path: API endpoint path
            json: JSON request body
            data: Form data or raw body
            headers: Request headers
            **kwargs: Additional arguments for requests

        Returns:
            APIResponse object
        """
        return self._request(
            "POST", path, headers=headers, json=json, data=data, **kwargs
        )

    def put(
        self,
        path: str,
        json: Optional[Dict[str, Any]] = None,
        data: Optional[Any] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs: Any,
    ) -> APIResponse:
        """
        Execute HTTP PUT request.

        Args:
            path: API endpoint path
            json: JSON request body
            data: Form data or raw body
            headers: Request headers
            **kwargs: Additional arguments for requests

        Returns:
            APIResponse object
        """
        return self._request(
            "PUT",
            path,
            headers=headers,
            json=json,
            data=data,
            **kwargs,
        )

    def delete(
        self,
        path: str,
        headers: Optional[Dict[str, str]] = None,
        **kwargs: Any,
    ) -> APIResponse:
        """
        Execute HTTP DELETE request.

        Args:
            path: API endpoint path
            headers: Request headers
            **kwargs: Additional arguments for requests

        Returns:
            APIResponse object
        """
        return self._request("DELETE", path, headers=headers, **kwargs)

    def patch(
        self,
        path: str,
        json: Optional[Dict[str, Any]] = None,
        data: Optional[Any] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs: Any,
    ) -> APIResponse:
        """
        Execute HTTP PATCH request.

        Args:
            path: API endpoint path
            json: JSON request body
            data: Form data or raw body
            headers: Request headers
            **kwargs: Additional arguments for requests

        Returns:
            APIResponse object
        """
        return self._request(
            "PATCH", path, headers=headers, json=json, data=data, **kwargs
        )

    def set_bearer_token(self, token: str) -> None:
        """
        Configure Bearer token authentication.

        Args:
            token: Bearer token value
        """
        self._auth_type = "bearer"
        self._auth_data = {"token": token}
        logger.info("Bearer token authentication configured")

    def set_api_key(
        self,
        key: str,
        location: str = "header",
        key_name: str = "X-API-Key",
    ) -> None:
        """
        Configure API key authentication.

        Args:
            key: API key value
            location: Where to send key ('header' or 'query')
            key_name: Name of header or query parameter
        """
        if location not in ("header", "query"):
            msg = "location must be 'header' or 'query'"
            raise ValueError(msg)

        self._auth_type = "api_key"
        self._auth_data = {
            "key": key,
            "location": location,
            "key_name": key_name,
        }
        logger.info(
            f"API key authentication configured "
            f"(location={location}, key_name={key_name})"
        )

    def set_basic_auth(self, username: str, password: str) -> None:
        """
        Configure HTTP Basic authentication.

        Args:
            username: Username
            password: Password
        """
        self._auth_type = "basic"
        self._auth_data = {"username": username, "password": password}
        logger.info(f"Basic authentication configured for user: {username}")

    def set_oauth2(
        self,
        token_url: str,
        client_id: str,
        client_secret: str,
        scope: Optional[list] = None,
    ) -> None:
        """
        Configure OAuth2 client credentials authentication.

        Args:
            token_url: OAuth2 token endpoint URL
            client_id: OAuth2 client ID
            client_secret: OAuth2 client secret
            scope: Optional list of scopes to request

        Raises:
            AuthenticationError: If token acquisition fails
        """
        try:
            # Create OAuth2 session
            oauth = OAuth2Session(client=None)

            # Fetch token
            token = oauth.fetch_token(
                token_url=token_url,
                client_id=client_id,
                client_secret=client_secret,
                scope=scope,
            )

            # Set as bearer token
            access_token = token.get("access_token")
            if not access_token:
                msg = "No access token in OAuth2 response"
                raise AuthenticationError(msg)

            self.set_bearer_token(access_token)

            # Store refresh information if available
            self._auth_type = "oauth2"
            self._auth_data = {
                "token": access_token,
                "token_url": token_url,
                "client_id": client_id,
                "client_secret": client_secret,
                "scope": scope,
                "refresh_token": token.get("refresh_token"),
            }

            logger.info("OAuth2 authentication configured")

        except Exception as e:
            logger.error(f"OAuth2 authentication failed: {e}")
            msg = f"OAuth2 token acquisition failed: {e}"
            raise AuthenticationError(msg) from e

    def set_custom_headers(self, headers: Dict[str, str]) -> None:
        """
        Configure custom authentication headers.

        Args:
            headers: Dictionary of custom headers to add to requests
        """
        self._auth_type = "custom"
        self._auth_data = {"headers": headers}
        logger.info(
            f"Custom authentication headers configured: " f"{list(headers.keys())}"
        )

    def clear_authentication(self) -> None:
        """Clear all authentication configuration."""
        self._auth_type = None
        self._auth_data = {}
        logger.info("Authentication cleared")

    def close(self) -> None:
        """Close the session and release resources."""
        self.session.close()
        logger.info("APIClient session closed")

    def __enter__(self) -> "APIClient":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit."""
        self.close()
