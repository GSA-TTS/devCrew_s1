"""
Figma API Client for Design Platform.

Production-ready HTTP wrapper for Figma REST API with comprehensive error
handling, rate limiting, retry logic, and Pydantic validation.

Features:
    - Bearer token authentication
    - Rate limiting handling (429 responses)
    - Exponential backoff retry logic
    - Request/response logging
    - Type-safe Pydantic models
    - Comprehensive error handling
    - File structure and property retrieval
    - Node export (PNG/SVG/PDF)
    - Component and style extraction
    - Comment posting

Example:
    >>> figma = FigmaClient(access_token="figd_xxx")
    >>> file = figma.get_file(file_key="ABC123")
    >>> exports = figma.export_nodes(
    ...     file_key="ABC123",
    ...     node_ids=["1:5", "1:6"],
    ...     format="png",
    ...     scale=2.0
    ... )
"""

import logging
import time
from enum import Enum
from typing import Any, Dict, List, Optional

import requests
from pydantic import BaseModel, Field

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class ExportFormat(str, Enum):
    """Supported export formats for Figma nodes."""

    PNG = "png"
    SVG = "svg"
    PDF = "pdf"
    JPG = "jpg"


class NodeType(str, Enum):
    """Figma node types."""

    DOCUMENT = "DOCUMENT"
    CANVAS = "CANVAS"
    FRAME = "FRAME"
    GROUP = "GROUP"
    VECTOR = "VECTOR"
    BOOLEAN_OPERATION = "BOOLEAN_OPERATION"
    STAR = "STAR"
    LINE = "LINE"
    ELLIPSE = "ELLIPSE"
    REGULAR_POLYGON = "REGULAR_POLYGON"
    RECTANGLE = "RECTANGLE"
    TEXT = "TEXT"
    SLICE = "SLICE"
    COMPONENT = "COMPONENT"
    COMPONENT_SET = "COMPONENT_SET"
    INSTANCE = "INSTANCE"


class BoundingBox(BaseModel):
    """Absolute bounding box coordinates for a node."""

    x: float = Field(..., description="X coordinate of top-left corner")
    y: float = Field(..., description="Y coordinate of top-left corner")
    width: float = Field(..., description="Width of bounding box")
    height: float = Field(..., description="Height of bounding box")


class Color(BaseModel):
    """RGBA color representation."""

    r: float = Field(..., ge=0.0, le=1.0, description="Red channel (0-1)")
    g: float = Field(..., ge=0.0, le=1.0, description="Green channel (0-1)")
    b: float = Field(..., ge=0.0, le=1.0, description="Blue channel (0-1)")
    a: float = Field(default=1.0, ge=0.0, le=1.0, description="Alpha channel (0-1)")

    def to_hex(self) -> str:
        """Convert RGBA color to hex format."""
        return (
            f"#{int(self.r * 255):02x}"
            f"{int(self.g * 255):02x}"
            f"{int(self.b * 255):02x}"
        )

    def to_rgba_string(self) -> str:
        """Convert to CSS rgba() format."""
        r_val = int(self.r * 255)
        g_val = int(self.g * 255)
        b_val = int(self.b * 255)
        return f"rgba({r_val}, {g_val}, {b_val}, {self.a})"


class FigmaNode(BaseModel):
    """Figma node representation with core properties."""

    id: str = Field(..., description="Unique node identifier")
    name: str = Field(..., description="Human-readable node name")
    type: NodeType = Field(..., description="Node type enum")
    visible: bool = Field(default=True, description="Node visibility")
    absolute_bounding_box: Optional[BoundingBox] = Field(
        None, alias="absoluteBoundingBox", description="Absolute position and size"
    )
    background_color: Optional[Color] = Field(
        None, alias="backgroundColor", description="Background color for frames"
    )
    children: List["FigmaNode"] = Field(default_factory=list, description="Child nodes")
    export_settings: List[Dict[str, Any]] = Field(
        default_factory=list,
        alias="exportSettings",
        description="Export configuration",
    )

    class Config:
        """Pydantic configuration."""

        populate_by_name = True
        use_enum_values = False


class FigmaFile(BaseModel):
    """Figma file structure with metadata."""

    document: FigmaNode = Field(..., description="Root document node")
    name: str = Field(..., description="File name")
    last_modified: str = Field(
        ..., alias="lastModified", description="Last modification timestamp ISO 8601"
    )
    version: str = Field(..., description="File version identifier")
    thumbnail_url: Optional[str] = Field(
        None, alias="thumbnailUrl", description="File thumbnail URL"
    )
    schema_version: int = Field(
        default=0, alias="schemaVersion", description="Figma API schema version"
    )
    components: Dict[str, Any] = Field(
        default_factory=dict, description="Component definitions"
    )
    component_sets: Dict[str, Any] = Field(
        default_factory=dict,
        alias="componentSets",
        description="Component set definitions",
    )
    styles: Dict[str, Any] = Field(
        default_factory=dict, description="Style definitions"
    )

    class Config:
        """Pydantic configuration."""

        populate_by_name = True


class FigmaExport(BaseModel):
    """Export result for a Figma node."""

    node_id: str = Field(..., description="Node ID that was exported")
    format: ExportFormat = Field(..., description="Export format")
    url: Optional[str] = Field(None, description="Temporary download URL")
    image_data: Optional[bytes] = Field(None, description="Downloaded image bytes")
    error: Optional[str] = Field(None, description="Error message if export failed")

    class Config:
        """Pydantic configuration."""

        arbitrary_types_allowed = True


class FigmaAPIError(Exception):
    """Base exception for Figma API errors."""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        response_body: Optional[str] = None,
    ):
        """Initialize Figma API error."""
        self.message = message
        self.status_code = status_code
        self.response_body = response_body
        super().__init__(self.message)


class RateLimitError(FigmaAPIError):
    """Exception raised when rate limit is exceeded."""

    def __init__(self, retry_after: Optional[int] = None):
        """Initialize rate limit error."""
        self.retry_after = retry_after
        message = f"Rate limit exceeded. Retry after {retry_after} seconds."
        super().__init__(message, status_code=429)


class AuthenticationError(FigmaAPIError):
    """Exception raised for authentication failures."""

    def __init__(self):
        """Initialize authentication error."""
        super().__init__("Invalid or missing access token", status_code=401)


class NotFoundError(FigmaAPIError):
    """Exception raised when resource is not found."""

    def __init__(self, resource: str):
        """Initialize not found error."""
        super().__init__(f"Resource not found: {resource}", status_code=404)


class ForbiddenError(FigmaAPIError):
    """Exception raised when access is forbidden."""

    def __init__(self, resource: str):
        """Initialize forbidden error."""
        super().__init__(f"Access forbidden to resource: {resource}", status_code=403)


class FigmaClient:
    """
    Production-ready HTTP client for Figma REST API.

    Provides methods for file operations, node exports, component extraction,
    style retrieval, and comment posting with comprehensive error handling
    and retry logic.

    Attributes:
        access_token: Figma API access token
        base_url: Base URL for Figma API (default: https://api.figma.com/v1)
        max_retries: Maximum number of retry attempts
        timeout: Request timeout in seconds
    """

    def __init__(
        self,
        access_token: str,
        base_url: str = "https://api.figma.com/v1",
        max_retries: int = 3,
        timeout: int = 30,
    ):
        """
        Initialize Figma API client.

        Args:
            access_token: Figma personal access token (figd_xxx format)
            base_url: Base URL for Figma API
            max_retries: Maximum retry attempts for failed requests
            timeout: Request timeout in seconds

        Raises:
            ValueError: If access_token is empty
        """
        if not access_token:
            raise ValueError("access_token cannot be empty")

        self.access_token = access_token
        self.base_url = base_url.rstrip("/")
        self.max_retries = max_retries
        self.timeout = timeout

        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json",
            }
        )

        logger.info("FigmaClient initialized with base_url=%s", self.base_url)

    def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        retry_count: int = 0,
    ) -> requests.Response:
        """
        Make HTTP request with retry logic and error handling.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            params: Query parameters
            json_data: JSON request body
            retry_count: Current retry attempt number

        Returns:
            Response object

        Raises:
            RateLimitError: When rate limit is exceeded
            AuthenticationError: When authentication fails
            NotFoundError: When resource is not found
            ForbiddenError: When access is forbidden
            FigmaAPIError: For other API errors
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"

        try:
            logger.debug("Making %s request to %s (retry=%d)", method, url, retry_count)

            response = self.session.request(
                method=method,
                url=url,
                params=params,
                json=json_data,
                timeout=self.timeout,
            )

            # Handle rate limiting
            if response.status_code == 429:
                retry_after = int(response.headers.get("Retry-After", 60))
                logger.warning("Rate limit hit. Retry after %d seconds", retry_after)

                if retry_count < self.max_retries:
                    time.sleep(retry_after)
                    return self._make_request(
                        method, endpoint, params, json_data, retry_count + 1
                    )
                else:
                    raise RateLimitError(retry_after=retry_after)

            # Handle authentication errors
            if response.status_code == 401:
                logger.error("Authentication failed")
                raise AuthenticationError()

            # Handle forbidden errors
            if response.status_code == 403:
                logger.error("Access forbidden to %s", endpoint)
                raise ForbiddenError(resource=endpoint)

            # Handle not found errors
            if response.status_code == 404:
                logger.error("Resource not found: %s", endpoint)
                raise NotFoundError(resource=endpoint)

            # Handle server errors with retry
            if response.status_code >= 500:
                logger.warning("Server error: %d", response.status_code)

                if retry_count < self.max_retries:
                    wait_time = 2**retry_count  # Exponential backoff
                    logger.info("Retrying after %d seconds", wait_time)
                    time.sleep(wait_time)
                    return self._make_request(
                        method, endpoint, params, json_data, retry_count + 1
                    )
                else:
                    raise FigmaAPIError(
                        message=f"Server error after {self.max_retries} retries",
                        status_code=response.status_code,
                        response_body=response.text,
                    )

            # Handle other client errors
            if response.status_code >= 400:
                raise FigmaAPIError(
                    message=f"API error: {response.text}",
                    status_code=response.status_code,
                    response_body=response.text,
                )

            response.raise_for_status()
            return response

        except requests.exceptions.Timeout as exc:
            logger.error("Request timeout after %d seconds", self.timeout)
            if retry_count < self.max_retries:
                wait_time = 2**retry_count
                time.sleep(wait_time)
                return self._make_request(
                    method, endpoint, params, json_data, retry_count + 1
                )
            raise FigmaAPIError(f"Request timeout: {str(exc)}") from exc

        except requests.exceptions.RequestException as exc:
            logger.error("Request exception: %s", str(exc))
            raise FigmaAPIError(f"Request failed: {str(exc)}") from exc

    def get_file(
        self, file_key: str, version: Optional[str] = None, depth: int = 2
    ) -> FigmaFile:
        """
        Get Figma file structure and properties.

        Args:
            file_key: Figma file key (from URL: figma.com/file/{file_key})
            version: Specific version ID to retrieve (optional)
            depth: Tree depth to retrieve (1-5, default=2)

        Returns:
            FigmaFile object with document structure

        Raises:
            ValueError: If file_key is empty or depth is invalid
            FigmaAPIError: For API errors
        """
        if not file_key:
            raise ValueError("file_key cannot be empty")

        if not 1 <= depth <= 5:
            raise ValueError("depth must be between 1 and 5")

        params: Dict[str, Any] = {"depth": depth}
        if version:
            params["version"] = version

        logger.info("Fetching file: %s (depth=%d)", file_key, depth)

        response = self._make_request("GET", f"/files/{file_key}", params=params)
        data = response.json()

        return FigmaFile(**data)

    def export_nodes(
        self,
        file_key: str,
        node_ids: List[str],
        export_format: str = "png",
        scale: float = 2.0,
        download: bool = True,
    ) -> List[FigmaExport]:
        """
        Export Figma nodes as images.

        Args:
            file_key: Figma file key
            node_ids: List of node IDs to export (e.g., ["1:5", "1:6"])
            export_format: Export format (png, svg, pdf, jpg)
            scale: Scale factor for raster exports (0.01-4.0)
            download: Whether to download image data

        Returns:
            List of FigmaExport objects with URLs and optional image data

        Raises:
            ValueError: If parameters are invalid
            FigmaAPIError: For API errors
        """
        if not file_key:
            raise ValueError("file_key cannot be empty")

        if not node_ids:
            raise ValueError("node_ids cannot be empty")

        if export_format not in [f.value for f in ExportFormat]:
            raise ValueError(
                f"Invalid format: {export_format}. "
                f"Must be one of {[f.value for f in ExportFormat]}"
            )

        if not 0.01 <= scale <= 4.0:
            raise ValueError("scale must be between 0.01 and 4.0")

        params = {
            "ids": ",".join(node_ids),
            "format": export_format,
            "scale": scale,
        }

        logger.info(
            "Exporting %d nodes from file %s (format=%s, scale=%.2f)",
            len(node_ids),
            file_key,
            export_format,
            scale,
        )

        response = self._make_request("GET", f"/images/{file_key}", params=params)
        data = response.json()

        exports = []
        images = data.get("images", {})
        err = data.get("err", None)

        for node_id in node_ids:
            url = images.get(node_id)

            if url:
                image_data = None
                if download:
                    try:
                        logger.debug("Downloading image for node %s", node_id)
                        img_response = requests.get(url, timeout=self.timeout)
                        img_response.raise_for_status()
                        image_data = img_response.content
                    except requests.exceptions.RequestException as exc:
                        logger.error(
                            "Failed to download image for node %s: %s",
                            node_id,
                            str(exc),
                        )

                exports.append(
                    FigmaExport(
                        node_id=node_id,
                        format=ExportFormat(export_format),
                        url=url,
                        image_data=image_data,
                        error=None,
                    )
                )
            else:
                exports.append(
                    FigmaExport(
                        node_id=node_id,
                        format=ExportFormat(export_format),
                        url=None,
                        image_data=None,
                        error=err or f"Export failed for node {node_id}",
                    )
                )

        logger.info("Successfully exported %d nodes", len(exports))
        return exports

    def get_components(self, file_key: str) -> List[FigmaNode]:
        """
        Get all component definitions from a Figma file.

        Args:
            file_key: Figma file key

        Returns:
            List of FigmaNode objects representing components

        Raises:
            ValueError: If file_key is empty
            FigmaAPIError: For API errors
        """
        if not file_key:
            raise ValueError("file_key cannot be empty")

        logger.info("Fetching components from file: %s", file_key)

        file_data = self.get_file(file_key, depth=3)
        components = []

        def find_components(node: FigmaNode) -> None:
            """Recursively find component nodes."""
            if node.type in (NodeType.COMPONENT, NodeType.COMPONENT_SET):
                components.append(node)

            for child in node.children:
                find_components(child)

        find_components(file_data.document)

        logger.info("Found %d components", len(components))
        return components

    def get_styles(self, file_key: str) -> Dict[str, Any]:
        """
        Retrieve design styles from a Figma file.

        Args:
            file_key: Figma file key

        Returns:
            Dictionary of style definitions organized by type

        Raises:
            ValueError: If file_key is empty
            FigmaAPIError: For API errors
        """
        if not file_key:
            raise ValueError("file_key cannot be empty")

        logger.info("Fetching styles from file: %s", file_key)

        response = self._make_request("GET", f"/files/{file_key}/styles")
        data = response.json()

        styles = data.get("meta", {}).get("styles", [])
        organized_styles: Dict[str, List[Dict[str, Any]]] = {
            "fill": [],
            "text": [],
            "effect": [],
            "grid": [],
        }

        for style in styles:
            style_type = style.get("style_type", "").lower()
            if style_type in organized_styles:
                organized_styles[style_type].append(style)

        logger.info(
            "Retrieved styles: fill=%d, text=%d, effect=%d, grid=%d",
            len(organized_styles["fill"]),
            len(organized_styles["text"]),
            len(organized_styles["effect"]),
            len(organized_styles["grid"]),
        )

        return organized_styles

    def post_comment(
        self, file_key: str, message: str, position: Dict[str, float]
    ) -> Dict[str, Any]:
        """
        Post a comment on a Figma design.

        Args:
            file_key: Figma file key
            message: Comment text
            position: Comment position with 'x' and 'y' coordinates

        Returns:
            Dictionary with comment metadata including ID

        Raises:
            ValueError: If parameters are invalid
            FigmaAPIError: For API errors
        """
        if not file_key:
            raise ValueError("file_key cannot be empty")

        if not message:
            raise ValueError("message cannot be empty")

        if not position or "x" not in position or "y" not in position:
            raise ValueError("position must contain 'x' and 'y' coordinates")

        payload = {
            "message": message,
            "client_meta": {
                "x": position["x"],
                "y": position["y"],
            },
        }

        logger.info("Posting comment to file: %s", file_key)

        response = self._make_request(
            "POST", f"/files/{file_key}/comments", json_data=payload
        )
        data = response.json()

        logger.info("Comment posted successfully: id=%s", data.get("id"))
        return data

    def get_file_nodes(
        self, file_key: str, node_ids: List[str]
    ) -> Dict[str, FigmaNode]:
        """
        Get specific nodes from a Figma file by ID.

        Args:
            file_key: Figma file key
            node_ids: List of node IDs to retrieve

        Returns:
            Dictionary mapping node IDs to FigmaNode objects

        Raises:
            ValueError: If parameters are invalid
            FigmaAPIError: For API errors
        """
        if not file_key:
            raise ValueError("file_key cannot be empty")

        if not node_ids:
            raise ValueError("node_ids cannot be empty")

        params = {"ids": ",".join(node_ids)}

        logger.info("Fetching %d specific nodes from file: %s", len(node_ids), file_key)

        response = self._make_request("GET", f"/files/{file_key}/nodes", params=params)
        data = response.json()

        nodes = {}
        for node_id, node_data in data.get("nodes", {}).items():
            if node_data:
                nodes[node_id] = FigmaNode(**node_data.get("document", {}))

        logger.info("Successfully retrieved %d nodes", len(nodes))
        return nodes

    def get_file_versions(
        self, file_key: str, page_size: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Get version history for a Figma file.

        Args:
            file_key: Figma file key
            page_size: Number of versions to return (max 100)

        Returns:
            List of version history entries

        Raises:
            ValueError: If parameters are invalid
            FigmaAPIError: For API errors
        """
        if not file_key:
            raise ValueError("file_key cannot be empty")

        if not 1 <= page_size <= 100:
            raise ValueError("page_size must be between 1 and 100")

        params = {"page_size": page_size}

        logger.info("Fetching version history for file: %s", file_key)

        response = self._make_request(
            "GET", f"/files/{file_key}/versions", params=params
        )
        data = response.json()

        versions = data.get("versions", [])
        logger.info("Retrieved %d versions", len(versions))

        return versions

    def close(self) -> None:
        """Close the HTTP session and cleanup resources."""
        if self.session:
            self.session.close()
            logger.info("FigmaClient session closed")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


# Enable forward references for recursive models
FigmaNode.model_rebuild()
