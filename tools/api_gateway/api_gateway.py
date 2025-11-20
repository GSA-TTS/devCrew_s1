"""
Issue #41: API Gateway Integration Module
Implements Kong and Tyk API gateway integration.
"""

import json
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

import httpx
from pydantic import BaseModel, Field, HttpUrl


class GatewayType(str, Enum):
    """API Gateway types."""

    KONG = "kong"
    TYK = "tyk"


class RouteMethod(str, Enum):
    """HTTP methods for routes."""

    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"
    OPTIONS = "OPTIONS"


class PluginType(str, Enum):
    """API Gateway plugin types."""

    JWT = "jwt"
    RATE_LIMITING = "rate-limiting"
    CORS = "cors"
    REQUEST_TRANSFORMER = "request-transformer"
    RESPONSE_TRANSFORMER = "response-transformer"
    IP_RESTRICTION = "ip-restriction"
    ACL = "acl"
    KEY_AUTH = "key-auth"
    OAUTH2 = "oauth2"


class RouteConfig(BaseModel):
    """Route configuration."""

    name: str = Field(..., min_length=1)
    paths: List[str] = Field(..., min_items=1)
    methods: List[RouteMethod] = Field(..., min_items=1)
    upstream_url: HttpUrl
    strip_path: bool = Field(default=True)
    preserve_host: bool = Field(default=False)


class PluginConfig(BaseModel):
    """Plugin configuration."""

    plugin_type: PluginType
    enabled: bool = Field(default=True)
    config: Dict[str, Any] = Field(default_factory=dict)


class ServiceConfig(BaseModel):
    """Service configuration."""

    name: str = Field(..., min_length=1)
    url: HttpUrl
    protocol: str = Field(default="http")
    host: str
    port: int = Field(default=80)
    path: Optional[str] = None
    retries: int = Field(default=5, ge=0)
    connect_timeout: int = Field(default=60000, gt=0)
    write_timeout: int = Field(default=60000, gt=0)
    read_timeout: int = Field(default=60000, gt=0)


class BaseGateway:
    """Base API Gateway client."""

    def __init__(self, admin_url: str, api_key: Optional[str] = None):
        """
        Initialize gateway client.

        Args:
            admin_url: Admin API URL
            api_key: API key for authentication
        """
        self.admin_url = admin_url.rstrip("/")
        self.api_key = api_key
        self.client = httpx.AsyncClient(timeout=30.0)

    def _get_headers(self) -> Dict[str, str]:
        """Get request headers with authentication."""
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["apikey"] = self.api_key
        return headers

    async def health_check(self) -> Dict[str, Any]:
        """
        Check gateway health.

        Returns:
            Health check response

        Raises:
            httpx.HTTPError: If health check fails
        """
        raise NotImplementedError

    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()


class KongGateway(BaseGateway):
    """Kong API Gateway client."""

    async def health_check(self) -> Dict[str, Any]:
        """
        Check Kong health.

        Returns:
            Health check response
        """
        response = await self.client.get(f"{self.admin_url}/status")
        response.raise_for_status()
        return response.json()

    async def create_service(self, service: ServiceConfig) -> Dict[str, Any]:
        """
        Create a service in Kong.

        Args:
            service: Service configuration

        Returns:
            Created service

        Raises:
            httpx.HTTPError: If service creation fails
        """
        payload = {
            "name": service.name,
            "url": str(service.url),
            "protocol": service.protocol,
            "host": service.host,
            "port": service.port,
            "retries": service.retries,
            "connect_timeout": service.connect_timeout,
            "write_timeout": service.write_timeout,
            "read_timeout": service.read_timeout,
        }

        if service.path:
            payload["path"] = service.path

        response = await self.client.post(
            f"{self.admin_url}/services",
            json=payload,
            headers=self._get_headers(),
        )
        response.raise_for_status()
        return response.json()

    async def get_service(self, service_name: str) -> Optional[Dict[str, Any]]:
        """
        Get service by name.

        Args:
            service_name: Service name

        Returns:
            Service data or None
        """
        try:
            response = await self.client.get(
                f"{self.admin_url}/services/{service_name}",
                headers=self._get_headers(),
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            raise

    async def create_route(
        self, service_name: str, route: RouteConfig
    ) -> Dict[str, Any]:
        """
        Create a route for a service.

        Args:
            service_name: Service name
            route: Route configuration

        Returns:
            Created route

        Raises:
            httpx.HTTPError: If route creation fails
        """
        payload = {
            "name": route.name,
            "paths": route.paths,
            "methods": [m.value for m in route.methods],
            "strip_path": route.strip_path,
            "preserve_host": route.preserve_host,
        }

        response = await self.client.post(
            f"{self.admin_url}/services/{service_name}/routes",
            json=payload,
            headers=self._get_headers(),
        )
        response.raise_for_status()
        return response.json()

    async def delete_route(self, route_id: str) -> bool:
        """
        Delete a route.

        Args:
            route_id: Route ID

        Returns:
            True if deleted, False otherwise
        """
        try:
            response = await self.client.delete(
                f"{self.admin_url}/routes/{route_id}",
                headers=self._get_headers(),
            )
            response.raise_for_status()
            return True
        except httpx.HTTPStatusError:
            return False

    async def add_plugin(
        self, service_name: str, plugin: PluginConfig
    ) -> Dict[str, Any]:
        """
        Add plugin to service.

        Args:
            service_name: Service name
            plugin: Plugin configuration

        Returns:
            Created plugin

        Raises:
            httpx.HTTPError: If plugin creation fails
        """
        payload = {
            "name": plugin.plugin_type.value,
            "enabled": plugin.enabled,
            "config": plugin.config,
        }

        response = await self.client.post(
            f"{self.admin_url}/services/{service_name}/plugins",
            json=payload,
            headers=self._get_headers(),
        )
        response.raise_for_status()
        return response.json()

    async def configure_jwt(
        self, service_name: str, secret_key: str
    ) -> Dict[str, Any]:
        """
        Configure JWT authentication for service.

        Args:
            service_name: Service name
            secret_key: JWT secret key

        Returns:
            Plugin configuration
        """
        plugin = PluginConfig(
            plugin_type=PluginType.JWT,
            config={
                "secret_is_base64": False,
                "key_claim_name": "kid",
                "claims_to_verify": ["exp"],
            },
        )
        return await self.add_plugin(service_name, plugin)

    async def configure_rate_limiting(
        self, service_name: str, requests_per_minute: int
    ) -> Dict[str, Any]:
        """
        Configure rate limiting for service.

        Args:
            service_name: Service name
            requests_per_minute: Max requests per minute

        Returns:
            Plugin configuration
        """
        plugin = PluginConfig(
            plugin_type=PluginType.RATE_LIMITING,
            config={
                "minute": requests_per_minute,
                "policy": "local",
            },
        )
        return await self.add_plugin(service_name, plugin)

    async def configure_cors(self, service_name: str) -> Dict[str, Any]:
        """
        Configure CORS for service.

        Args:
            service_name: Service name

        Returns:
            Plugin configuration
        """
        plugin = PluginConfig(
            plugin_type=PluginType.CORS,
            config={
                "origins": ["*"],
                "methods": ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
                "headers": ["Accept", "Content-Type", "Authorization"],
                "exposed_headers": ["X-Auth-Token"],
                "credentials": True,
                "max_age": 3600,
            },
        )
        return await self.add_plugin(service_name, plugin)


class TykGateway(BaseGateway):
    """Tyk API Gateway client."""

    async def health_check(self) -> Dict[str, Any]:
        """
        Check Tyk health.

        Returns:
            Health check response
        """
        response = await self.client.get(
            f"{self.admin_url}/hello",
            headers=self._get_headers(),
        )
        response.raise_for_status()
        return {"status": "healthy", "response": response.json()}

    async def create_api(
        self, service: ServiceConfig, route: RouteConfig
    ) -> Dict[str, Any]:
        """
        Create an API in Tyk.

        Args:
            service: Service configuration
            route: Route configuration

        Returns:
            Created API

        Raises:
            httpx.HTTPError: If API creation fails
        """
        api_definition = {
            "name": service.name,
            "slug": service.name.lower().replace(" ", "-"),
            "api_id": f"{service.name.lower()}-{datetime.utcnow().timestamp()}",
            "org_id": "default",
            "use_keyless": False,
            "auth": {"auth_header_name": "Authorization"},
            "definition": {
                "location": "header",
                "key": "x-api-version",
            },
            "version_data": {
                "not_versioned": True,
                "versions": {
                    "Default": {
                        "name": "Default",
                        "use_extended_paths": True,
                    }
                },
            },
            "proxy": {
                "listen_path": route.paths[0],
                "target_url": str(service.url),
                "strip_listen_path": route.strip_path,
            },
            "active": True,
        }

        response = await self.client.post(
            f"{self.admin_url}/apis",
            json=api_definition,
            headers=self._get_headers(),
        )
        response.raise_for_status()
        return response.json()

    async def get_api(self, api_id: str) -> Optional[Dict[str, Any]]:
        """
        Get API by ID.

        Args:
            api_id: API ID

        Returns:
            API data or None
        """
        try:
            response = await self.client.get(
                f"{self.admin_url}/apis/{api_id}",
                headers=self._get_headers(),
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            raise

    async def delete_api(self, api_id: str) -> bool:
        """
        Delete an API.

        Args:
            api_id: API ID

        Returns:
            True if deleted, False otherwise
        """
        try:
            response = await self.client.delete(
                f"{self.admin_url}/apis/{api_id}",
                headers=self._get_headers(),
            )
            response.raise_for_status()
            return True
        except httpx.HTTPStatusError:
            return False

    async def configure_rate_limiting(
        self, api_id: str, requests_per_minute: int
    ) -> Dict[str, Any]:
        """
        Configure rate limiting for API.

        Args:
            api_id: API ID
            requests_per_minute: Max requests per minute

        Returns:
            Updated API configuration
        """
        api_data = await self.get_api(api_id)
        if not api_data:
            raise ValueError(f"API {api_id} not found")

        # Add rate limiting configuration
        api_data["rate_limit"] = {
            "rate": requests_per_minute,
            "per": 60,
        }

        response = await self.client.put(
            f"{self.admin_url}/apis/{api_id}",
            json=api_data,
            headers=self._get_headers(),
        )
        response.raise_for_status()
        return response.json()


class GatewayManager:
    """Manage API Gateway operations."""

    def __init__(self, gateway_type: GatewayType, admin_url: str, api_key: str):
        """
        Initialize gateway manager.

        Args:
            gateway_type: Type of gateway
            admin_url: Admin API URL
            api_key: API key
        """
        self.gateway_type = gateway_type

        if gateway_type == GatewayType.KONG:
            self.gateway: BaseGateway = KongGateway(admin_url, api_key)
        elif gateway_type == GatewayType.TYK:
            self.gateway = TykGateway(admin_url, api_key)
        else:
            raise ValueError(f"Unsupported gateway type: {gateway_type}")

    async def setup_customer_api(
        self, upstream_url: str
    ) -> Dict[str, Any]:
        """
        Setup customer API with authentication and rate limiting.

        Args:
            upstream_url: Upstream service URL

        Returns:
            Setup result
        """
        service = ServiceConfig(
            name="customer-api",
            url=upstream_url,
            host="localhost",
            port=8000,
        )

        route = RouteConfig(
            name="customer-routes",
            paths=["/api/customers"],
            methods=[RouteMethod.GET, RouteMethod.POST, RouteMethod.PUT, RouteMethod.DELETE],  # noqa: E501
            upstream_url=upstream_url,
        )

        if isinstance(self.gateway, KongGateway):
            # Create service and route
            service_result = await self.gateway.create_service(service)
            route_result = await self.gateway.create_route(service.name, route)

            # Configure plugins
            await self.gateway.configure_jwt(service.name, "secret-key")
            await self.gateway.configure_rate_limiting(service.name, 100)
            await self.gateway.configure_cors(service.name)

            return {
                "gateway": "kong",
                "service": service_result,
                "route": route_result,
            }
        elif isinstance(self.gateway, TykGateway):
            # Create API
            api_result = await self.gateway.create_api(service, route)

            # Configure rate limiting
            api_id = api_result.get("key")
            await self.gateway.configure_rate_limiting(api_id, 100)

            return {
                "gateway": "tyk",
                "api": api_result,
            }

    async def close(self):
        """Close gateway connection."""
        await self.gateway.close()
