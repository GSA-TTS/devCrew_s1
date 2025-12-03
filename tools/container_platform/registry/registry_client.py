"""
Registry Client Module.

Comprehensive multi-registry container image management with support for:
- Docker Hub
- Amazon ECR (Elastic Container Registry)
- Google GCR (Google Container Registry)
- Azure ACR (Azure Container Registry)
- Harbor (Private Registry)

Features:
- Unified API across all registry types
- Authentication and credential management
- Image push/pull with progress tracking
- Cross-registry synchronization
- Image promotion workflows
- Manifest operations and tagging
- Registry catalog browsing
"""

import base64
import json
import logging
import os
import re
import subprocess
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

try:
    import boto3
    from botocore.exceptions import ClientError, NoCredentialsError

    AWS_AVAILABLE = True
except ImportError:
    AWS_AVAILABLE = False

try:
    from google.oauth2 import service_account

    GCP_AVAILABLE = True
except ImportError:
    GCP_AVAILABLE = False

try:
    from azure.identity import DefaultAzureCredential

    AZURE_AVAILABLE = True
except ImportError:
    AZURE_AVAILABLE = False

logger = logging.getLogger(__name__)


class RegistryType(Enum):
    """Supported registry types."""

    DOCKER_HUB = "dockerhub"
    ECR = "ecr"
    GCR = "gcr"
    ACR = "acr"
    HARBOR = "harbor"
    GENERIC = "generic"


class ImagePromotionStage(Enum):
    """Image promotion stages."""

    DEV = "dev"
    STAGING = "staging"
    PROD = "prod"


@dataclass
class RegistryConfig:
    """Registry configuration."""

    registry_type: RegistryType
    url: str
    username: Optional[str] = None
    password: Optional[str] = None
    region: Optional[str] = None  # For ECR
    project_id: Optional[str] = None  # For GCR
    subscription_id: Optional[str] = None  # For ACR
    insecure: bool = False
    credential_helper: Optional[str] = None


@dataclass
class ImageInfo:
    """Container image information."""

    registry: str
    repository: str
    tag: str
    digest: Optional[str] = None
    size: Optional[int] = None
    created: Optional[datetime] = None
    architecture: Optional[str] = None
    os: Optional[str] = None
    labels: Optional[Dict[str, str]] = None

    @property
    def full_name(self) -> str:
        """Get full image name."""
        return f"{self.registry}/{self.repository}:{self.tag}"


@dataclass
class PushPullProgress:
    """Progress tracking for push/pull operations."""

    total_bytes: int
    transferred_bytes: int
    layers_total: int
    layers_completed: int
    current_layer: str
    status: str
    percentage: float


class RegistryAuthenticationError(Exception):
    """Registry authentication failed."""

    pass


class RegistryOperationError(Exception):
    """Registry operation failed."""

    pass


class ImageNotFoundError(Exception):
    """Image not found in registry."""

    pass


class RegistryClient:
    """
    Multi-registry container image management client.

    Provides unified interface for working with multiple container registries
    including Docker Hub, AWS ECR, Google GCR, Azure ACR, and Harbor.
    """

    def __init__(
        self,
        config: RegistryConfig,
        timeout: int = 300,
        max_retries: int = 3,
        cache_dir: Optional[Path] = None,
    ):
        """
        Initialize registry client.

        Args:
            config: Registry configuration
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
            cache_dir: Directory for caching credentials and metadata
        """
        self.config = config
        self.timeout = timeout
        self.max_retries = max_retries
        self.cache_dir = cache_dir or Path.home() / ".container_platform" / "cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self._token: Optional[str] = None
        self._token_expiry: Optional[datetime] = None
        self._session = self._create_session()

        logger.info(
            f"Initialized registry client for {config.registry_type.value} "
            f"at {config.url}"
        )

    def _create_session(self) -> requests.Session:
        """Create HTTP session with retry logic."""
        session = requests.Session()

        retry_strategy = Retry(
            total=self.max_retries,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "PUT", "DELETE", "POST"],
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        return session

    def _get_auth_header(self) -> Dict[str, str]:
        """Get authentication headers."""
        if self._token and self._token_expiry and datetime.now() < self._token_expiry:
            return {"Authorization": f"Bearer {self._token}"}

        # Refresh token
        self._authenticate()

        if self._token:
            return {"Authorization": f"Bearer {self._token}"}

        return {}

    def _authenticate(self) -> None:
        """Authenticate with the registry."""
        if self.config.registry_type == RegistryType.DOCKER_HUB:
            self._authenticate_dockerhub()
        elif self.config.registry_type == RegistryType.ECR:
            self._authenticate_ecr()
        elif self.config.registry_type == RegistryType.GCR:
            self._authenticate_gcr()
        elif self.config.registry_type == RegistryType.ACR:
            self._authenticate_acr()
        elif self.config.registry_type == RegistryType.HARBOR:
            self._authenticate_harbor()
        else:
            self._authenticate_generic()

    def _authenticate_dockerhub(self) -> None:
        """Authenticate with Docker Hub."""
        if not self.config.username or not self.config.password:
            # Try to get credentials from config file
            creds = self._get_docker_config_credentials("index.docker.io")
            if creds:
                self.config.username, self.config.password = creds
            else:
                raise RegistryAuthenticationError("Docker Hub credentials not provided")

        url = "https://hub.docker.com/v2/users/login"
        payload = {
            "username": self.config.username,
            "password": self.config.password,
        }

        try:
            response = self._session.post(url, json=payload, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
            self._token = data.get("token")
            # Docker Hub tokens typically valid for 5 minutes
            self._token_expiry = datetime.now() + timedelta(minutes=5)
            logger.info("Successfully authenticated with Docker Hub")
        except requests.exceptions.RequestException as e:
            raise RegistryAuthenticationError(
                f"Docker Hub authentication failed: {e}"
            ) from e

    def _authenticate_ecr(self) -> None:
        """Authenticate with Amazon ECR."""
        if not AWS_AVAILABLE:
            raise RegistryAuthenticationError(
                "boto3 not available. Install with: pip install boto3"
            )

        try:
            ecr_client = boto3.client(
                "ecr", region_name=self.config.region or "us-east-1"
            )
            response = ecr_client.get_authorization_token()

            auth_data = response["authorizationData"][0]
            token = base64.b64decode(auth_data["authorizationToken"]).decode()
            username, password = token.split(":")

            self.config.username = username
            self.config.password = password
            self._token = password

            # ECR tokens valid for 12 hours
            expires_at = auth_data.get("expiresAt")
            if expires_at:
                self._token_expiry = expires_at
            else:
                self._token_expiry = datetime.now() + timedelta(hours=12)

            logger.info("Successfully authenticated with Amazon ECR")
        except (ClientError, NoCredentialsError) as e:
            raise RegistryAuthenticationError(f"ECR authentication failed: {e}") from e

    def _authenticate_gcr(self) -> None:
        """Authenticate with Google GCR."""
        if not GCP_AVAILABLE:
            raise RegistryAuthenticationError(
                "Google Cloud SDK not available. "
                "Install with: pip install google-cloud-storage"
            )

        try:
            # Try to use gcloud credential helper first
            result = subprocess.run(  # nosec B603 B607
                ["gcloud", "auth", "print-access-token"],
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
            )

            if result.returncode == 0:
                self._token = result.stdout.strip()
                self.config.username = "_token"
                # GCloud tokens typically valid for 1 hour
                self._token_expiry = datetime.now() + timedelta(hours=1)
                logger.info("Successfully authenticated with Google GCR")
            else:
                # Try service account key
                key_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
                if key_path and Path(key_path).exists():
                    credentials = service_account.Credentials.from_service_account_file(
                        key_path
                    )
                    # Use service account for authentication
                    self._token = credentials.token
                    self._token_expiry = datetime.now() + timedelta(hours=1)
                    logger.info(
                        "Successfully authenticated with Google GCR "
                        "using service account"
                    )
                else:
                    raise RegistryAuthenticationError(
                        "GCR authentication failed: No valid credentials found"
                    )
        except subprocess.TimeoutExpired as e:
            raise RegistryAuthenticationError(f"GCR authentication timeout: {e}") from e
        except Exception as e:
            raise RegistryAuthenticationError(f"GCR authentication failed: {e}") from e

    def _authenticate_acr(self) -> None:
        """Authenticate with Azure ACR."""
        if not AZURE_AVAILABLE:
            raise RegistryAuthenticationError(
                "Azure SDK not available. "
                "Install with: pip install azure-identity "
                "azure-mgmt-containerregistry"
            )

        try:
            credential = DefaultAzureCredential()

            # Try to get access token for ACR
            token = credential.get_token("https://management.azure.com/.default")
            self._token = token.token
            self._token_expiry = datetime.fromtimestamp(token.expires_on)

            # ACR uses service principal or managed identity
            self.config.username = "00000000-0000-0000-0000-000000000000"
            logger.info("Successfully authenticated with Azure ACR")
        except Exception as e:
            raise RegistryAuthenticationError(f"ACR authentication failed: {e}") from e

    def _authenticate_harbor(self) -> None:
        """Authenticate with Harbor registry."""
        if not self.config.username or not self.config.password:
            raise RegistryAuthenticationError("Harbor credentials not provided")

        # Harbor uses basic auth, create base64 encoded token
        credentials = f"{self.config.username}:{self.config.password}"
        self._token = base64.b64encode(credentials.encode()).decode()
        # Harbor tokens don't expire, but we'll refresh every hour
        self._token_expiry = datetime.now() + timedelta(hours=1)
        logger.info("Successfully authenticated with Harbor")

    def _authenticate_generic(self) -> None:
        """Authenticate with generic Docker Registry v2."""
        if not self.config.username or not self.config.password:
            # Try credential helper
            creds = self._get_docker_config_credentials(self.config.url)
            if creds:
                self.config.username, self.config.password = creds
            else:
                raise RegistryAuthenticationError("Registry credentials not provided")

        # Generic registry uses basic auth
        credentials = f"{self.config.username}:{self.config.password}"
        self._token = base64.b64encode(credentials.encode()).decode()
        self._token_expiry = datetime.now() + timedelta(hours=1)
        logger.info("Successfully authenticated with generic registry")

    def _get_docker_config_credentials(
        self, registry_url: str
    ) -> Optional[Tuple[str, str]]:
        """Get credentials from Docker config file."""
        config_path = Path.home() / ".docker" / "config.json"
        if not config_path.exists():
            return None

        try:
            with open(config_path, "r") as f:
                config = json.load(f)

            # Check auths section
            auths = config.get("auths", {})
            for url, auth_data in auths.items():
                if registry_url in url:
                    auth = auth_data.get("auth")
                    if auth:
                        decoded = base64.b64decode(auth).decode()
                        username, password = decoded.split(":", 1)
                        return username, password

            # Check credential helpers
            cred_helpers = config.get("credHelpers", {})
            for url, helper in cred_helpers.items():
                if registry_url in url:
                    return self._get_credential_helper_auth(helper, registry_url)

        except Exception as e:
            logger.warning(f"Failed to read Docker config: {e}")

        return None

    def _get_credential_helper_auth(
        self, helper: str, registry_url: str
    ) -> Optional[Tuple[str, str]]:
        """Get credentials from Docker credential helper."""
        try:
            result = subprocess.run(  # nosec B603
                [f"docker-credential-{helper}", "get"],
                input=registry_url.encode(),
                capture_output=True,
                timeout=10,
                check=False,
            )

            if result.returncode == 0:
                data = json.loads(result.stdout)
                username = data.get("Username")
                password = data.get("Secret")
                if username and password:
                    return username, password
        except Exception as e:
            logger.warning(f"Failed to use credential helper {helper}: {e}")

        return None

    def push_image(
        self, image_name: str, tag: str, callback: Optional[Callable] = None
    ) -> ImageInfo:
        """
        Push image to registry.

        Args:
            image_name: Image name (repository)
            tag: Image tag
            callback: Optional progress callback function

        Returns:
            ImageInfo object with pushed image details
        """
        full_image = f"{self.config.url}/{image_name}:{tag}"
        logger.info(f"Pushing image: {full_image}")

        try:
            # Use docker CLI for actual push operation
            cmd = ["docker", "push", full_image]

            process = subprocess.Popen(  # nosec B603
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
            )

            # Track progress
            progress = PushPullProgress(
                total_bytes=0,
                transferred_bytes=0,
                layers_total=0,
                layers_completed=0,
                current_layer="",
                status="starting",
                percentage=0.0,
            )

            if process.stdout:
                for line in process.stdout:
                    line = line.strip()
                    if not line:
                        continue

                    # Parse progress information
                    if "Pushed" in line or "Layer already exists" in line:
                        progress.layers_completed += 1
                        progress.status = "pushing"
                    elif "Pushing" in line:
                        progress.current_layer = line
                        progress.status = "pushing"

                    if progress.layers_total > 0:
                        progress.percentage = (
                            progress.layers_completed / progress.layers_total * 100
                        )

                    if callback:
                        callback(progress)

                    logger.debug(line)

            process.wait()

            if process.returncode != 0:
                raise RegistryOperationError(f"Failed to push image: {full_image}")

            # Get image info
            return self.get_image_info(image_name, tag)

        except subprocess.SubprocessError as e:
            raise RegistryOperationError(f"Failed to push image: {e}") from e

    def pull_image(
        self, image_name: str, tag: str, callback: Optional[Callable] = None
    ) -> ImageInfo:
        """
        Pull image from registry.

        Args:
            image_name: Image name (repository)
            tag: Image tag
            callback: Optional progress callback function

        Returns:
            ImageInfo object with pulled image details
        """
        full_image = f"{self.config.url}/{image_name}:{tag}"
        logger.info(f"Pulling image: {full_image}")

        try:
            cmd = ["docker", "pull", full_image]

            process = subprocess.Popen(  # nosec B603
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
            )

            progress = PushPullProgress(
                total_bytes=0,
                transferred_bytes=0,
                layers_total=0,
                layers_completed=0,
                current_layer="",
                status="starting",
                percentage=0.0,
            )

            if process.stdout:
                for line in process.stdout:
                    line = line.strip()
                    if not line:
                        continue

                    # Parse progress
                    if "Pull complete" in line or "Already exists" in line:
                        progress.layers_completed += 1
                        progress.status = "pulling"
                    elif "Pulling" in line:
                        progress.current_layer = line
                        progress.status = "pulling"

                    if progress.layers_total > 0:
                        progress.percentage = (
                            progress.layers_completed / progress.layers_total * 100
                        )

                    if callback:
                        callback(progress)

                    logger.debug(line)

            process.wait()

            if process.returncode != 0:
                raise RegistryOperationError(f"Failed to pull image: {full_image}")

            return self.get_image_info(image_name, tag)

        except subprocess.SubprocessError as e:
            raise RegistryOperationError(f"Failed to pull image: {e}") from e

    def get_image_info(self, image_name: str, tag: str) -> ImageInfo:
        """
        Get image information from registry.

        Args:
            image_name: Image name (repository)
            tag: Image tag

        Returns:
            ImageInfo object
        """
        manifest = self.get_manifest(image_name, tag)

        # Parse manifest to extract info
        config_digest = manifest.get("config", {}).get("digest")
        layers = manifest.get("layers", [])

        total_size = sum(layer.get("size", 0) for layer in layers)

        # Get config blob for additional metadata
        config = self._get_config_blob(image_name, config_digest)

        created_str = config.get("created")
        created = None
        if created_str:
            try:
                created = datetime.fromisoformat(created_str.replace("Z", "+00:00"))
            except ValueError:
                pass

        return ImageInfo(
            registry=self.config.url,
            repository=image_name,
            tag=tag,
            digest=manifest.get("digest"),
            size=total_size,
            created=created,
            architecture=config.get("architecture"),
            os=config.get("os"),
            labels=config.get("config", {}).get("Labels"),
        )

    def get_manifest(self, image_name: str, tag: str) -> Dict[str, Any]:
        """
        Get image manifest from registry.

        Args:
            image_name: Image name (repository)
            tag: Image tag

        Returns:
            Manifest dictionary
        """
        url = self._build_api_url(f"/v2/{image_name}/manifests/{tag}")

        headers = self._get_auth_header()
        headers["Accept"] = "application/vnd.docker.distribution.manifest.v2+json"

        try:
            response = self._session.get(url, headers=headers, timeout=self.timeout)
            response.raise_for_status()

            manifest = response.json()

            # Store digest from header
            digest = response.headers.get("Docker-Content-Digest")
            if digest:
                manifest["digest"] = digest

            return manifest

        except requests.exceptions.RequestException as e:
            if (
                hasattr(e, "response")
                and e.response is not None
                and e.response.status_code == 404
            ):
                raise ImageNotFoundError(f"Image not found: {image_name}:{tag}") from e
            raise RegistryOperationError(f"Failed to get manifest: {e}") from e

    def _get_config_blob(
        self, image_name: str, digest: Optional[str]
    ) -> Dict[str, Any]:
        """Get image config blob."""
        if not digest:
            return {}

        url = self._build_api_url(f"/v2/{image_name}/blobs/{digest}")
        headers = self._get_auth_header()

        try:
            response = self._session.get(url, headers=headers, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.warning(f"Failed to get config blob: {e}")
            return {}

    def tag_image(self, image_name: str, source_tag: str, target_tag: str) -> bool:
        """
        Create a new tag for an existing image.

        Args:
            image_name: Image name (repository)
            source_tag: Source tag
            target_tag: Target tag

        Returns:
            True if successful
        """
        logger.info(f"Tagging {image_name}:{source_tag} as {image_name}:{target_tag}")

        try:
            # Get manifest from source tag
            manifest = self.get_manifest(image_name, source_tag)

            # Put manifest with new tag
            url = self._build_api_url(f"/v2/{image_name}/manifests/{target_tag}")
            headers = self._get_auth_header()
            headers["Content-Type"] = (
                "application/vnd.docker.distribution.manifest.v2+json"
            )

            response = self._session.put(
                url, headers=headers, json=manifest, timeout=self.timeout
            )
            response.raise_for_status()

            logger.info(
                f"Successfully tagged {image_name}:{source_tag} "
                f"as {image_name}:{target_tag}"
            )
            return True

        except Exception as e:
            raise RegistryOperationError(f"Failed to tag image: {e}") from e

    def list_repositories(self) -> List[str]:
        """
        List all repositories in the registry.

        Returns:
            List of repository names
        """
        url = self._build_api_url("/v2/_catalog")
        headers = self._get_auth_header()

        repositories = []
        try:
            response = self._session.get(url, headers=headers, timeout=self.timeout)
            response.raise_for_status()

            data = response.json()
            repositories = data.get("repositories", [])

            logger.info(f"Found {len(repositories)} repositories")
            return repositories

        except requests.exceptions.RequestException as e:
            raise RegistryOperationError(f"Failed to list repositories: {e}") from e

    def list_tags(self, image_name: str) -> List[str]:
        """
        List all tags for a repository.

        Args:
            image_name: Image name (repository)

        Returns:
            List of tag names
        """
        url = self._build_api_url(f"/v2/{image_name}/tags/list")
        headers = self._get_auth_header()

        try:
            response = self._session.get(url, headers=headers, timeout=self.timeout)
            response.raise_for_status()

            data = response.json()
            tags = data.get("tags", [])

            logger.info(f"Found {len(tags)} tags for {image_name}")
            return tags

        except requests.exceptions.RequestException as e:
            if (
                hasattr(e, "response")
                and e.response is not None
                and e.response.status_code == 404
            ):
                raise ImageNotFoundError(f"Repository not found: {image_name}") from e
            raise RegistryOperationError(f"Failed to list tags: {e}") from e

    def delete_image(self, image_name: str, tag: str) -> bool:
        """
        Delete an image from the registry.

        Args:
            image_name: Image name (repository)
            tag: Image tag

        Returns:
            True if successful
        """
        logger.info(f"Deleting image: {image_name}:{tag}")

        try:
            # Get manifest to get digest
            manifest = self.get_manifest(image_name, tag)
            digest = manifest.get("digest")

            if not digest:
                raise RegistryOperationError("Could not get image digest")

            # Delete by digest
            url = self._build_api_url(f"/v2/{image_name}/manifests/{digest}")
            headers = self._get_auth_header()

            response = self._session.delete(url, headers=headers, timeout=self.timeout)
            response.raise_for_status()

            logger.info(f"Successfully deleted {image_name}:{tag}")
            return True

        except Exception as e:
            raise RegistryOperationError(f"Failed to delete image: {e}") from e

    def sync_image(
        self,
        source_registry: "RegistryClient",
        image_name: str,
        tag: str,
        target_image_name: Optional[str] = None,
        target_tag: Optional[str] = None,
    ) -> ImageInfo:
        """
        Synchronize image from another registry.

        Args:
            source_registry: Source registry client
            image_name: Source image name
            tag: Source image tag
            target_image_name: Target image name (defaults to source)
            target_tag: Target tag (defaults to source)

        Returns:
            ImageInfo object for synced image
        """
        target_image_name = target_image_name or image_name
        target_tag = target_tag or tag

        logger.info(
            f"Syncing image from "
            f"{source_registry.config.url}/{image_name}:{tag} to "
            f"{self.config.url}/{target_image_name}:{target_tag}"
        )

        try:
            # Pull from source
            source_full = f"{source_registry.config.url}/{image_name}:{tag}"
            target_full = f"{self.config.url}/{target_image_name}:{target_tag}"

            # Tag the source image with target registry
            subprocess.run(  # nosec B603 B607
                ["docker", "tag", source_full, target_full],
                check=True,
                capture_output=True,
            )

            # Push to target
            return self.push_image(target_image_name, target_tag)

        except subprocess.CalledProcessError as e:
            raise RegistryOperationError(f"Failed to sync image: {e}") from e

    def promote_image(
        self,
        image_name: str,
        current_stage: ImagePromotionStage,
        target_stage: ImagePromotionStage,
        version: str,
    ) -> ImageInfo:
        """
        Promote image through deployment stages.

        Args:
            image_name: Base image name
            current_stage: Current deployment stage
            target_stage: Target deployment stage
            version: Image version

        Returns:
            ImageInfo object for promoted image
        """
        source_tag = f"{current_stage.value}-{version}"
        target_tag = f"{target_stage.value}-{version}"

        logger.info(
            f"Promoting {image_name} from {current_stage.value} "
            f"to {target_stage.value}"
        )

        # Verify source exists
        try:
            self.get_image_info(image_name, source_tag)
        except ImageNotFoundError as e:
            raise RegistryOperationError(
                f"Source image not found: {image_name}:{source_tag}"
            ) from e

        # Tag with target stage
        self.tag_image(image_name, source_tag, target_tag)

        logger.info(
            f"Successfully promoted {image_name} "
            f"from {current_stage.value} to {target_stage.value}"
        )

        return self.get_image_info(image_name, target_tag)

    def _build_api_url(self, path: str) -> str:
        """Build full API URL."""
        base_url = self.config.url.rstrip("/")

        # Ensure URL has scheme
        if not base_url.startswith(("http://", "https://")):
            scheme = "http" if self.config.insecure else "https"
            base_url = f"{scheme}://{base_url}"

        return f"{base_url}{path}"

    def search_images(self, query: str, limit: int = 25) -> List[Dict[str, Any]]:
        """
        Search for images in the registry.

        Args:
            query: Search query
            limit: Maximum number of results

        Returns:
            List of matching images
        """
        if self.config.registry_type == RegistryType.DOCKER_HUB:
            return self._search_dockerhub(query, limit)
        else:
            # Generic search by listing and filtering
            return self._search_generic(query, limit)

    def _search_dockerhub(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """Search Docker Hub."""
        url = "https://hub.docker.com/v2/search/repositories/"
        params: Dict[str, Any] = {"query": query, "page_size": limit}

        try:
            response = self._session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()

            data = response.json()
            return data.get("results", [])

        except requests.exceptions.RequestException as e:
            logger.warning(f"Docker Hub search failed: {e}")
            return []

    def _search_generic(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """Search generic registry by filtering repositories."""
        try:
            repositories = self.list_repositories()
            pattern = re.compile(query, re.IGNORECASE)

            results = []
            for repo in repositories:
                if pattern.search(repo):
                    results.append(
                        {
                            "name": repo,
                            "namespace": (
                                repo.split("/")[0] if "/" in repo else "library"
                            ),
                        }
                    )

                if len(results) >= limit:
                    break

            return results

        except Exception as e:
            logger.warning(f"Registry search failed: {e}")
            return []

    def verify_image_signature(
        self, image_name: str, tag: str, public_key: Optional[str] = None
    ) -> bool:
        """
        Verify image signature using Docker Content Trust.

        Args:
            image_name: Image name
            tag: Image tag
            public_key: Optional public key for verification

        Returns:
            True if signature is valid
        """
        full_image = f"{self.config.url}/{image_name}:{tag}"

        try:
            # Use docker trust inspect
            cmd = ["docker", "trust", "inspect", "--pretty", full_image]

            result = subprocess.run(  # nosec B603
                cmd, capture_output=True, text=True, check=False
            )

            if result.returncode == 0:
                logger.info(f"Image signature verified: {full_image}")
                return True
            else:
                logger.warning(f"Image signature verification failed: {result.stderr}")
                return False

        except Exception as e:
            logger.warning(f"Failed to verify image signature: {e}")
            return False

    def get_registry_info(self) -> Dict[str, Any]:
        """
        Get registry information.

        Returns:
            Registry info dictionary
        """
        url = self._build_api_url("/v2/")
        headers = self._get_auth_header()

        try:
            response = self._session.get(url, headers=headers, timeout=self.timeout)
            response.raise_for_status()

            return {
                "url": self.config.url,
                "type": self.config.registry_type.value,
                "api_version": "v2",
                "authenticated": bool(self._token),
                "status": "ok",
            }

        except requests.exceptions.RequestException as e:
            return {
                "url": self.config.url,
                "type": self.config.registry_type.value,
                "status": "error",
                "error": str(e),
            }

    def cleanup_old_images(self, image_name: str, keep_count: int = 5) -> List[str]:
        """
        Clean up old image tags, keeping only the most recent.

        Args:
            image_name: Image name (repository)
            keep_count: Number of recent tags to keep

        Returns:
            List of deleted tags
        """
        logger.info(f"Cleaning up old images for {image_name}, keeping {keep_count}")

        try:
            tags = self.list_tags(image_name)

            # Sort tags (assuming semantic versioning or timestamp)
            tags.sort(reverse=True)

            # Tags to delete
            tags_to_delete = tags[keep_count:]

            deleted = []
            for tag in tags_to_delete:
                try:
                    self.delete_image(image_name, tag)
                    deleted.append(tag)
                except Exception as e:
                    logger.warning(f"Failed to delete {image_name}:{tag}: {e}")

            logger.info(f"Deleted {len(deleted)} old tags for {image_name}")
            return deleted

        except Exception as e:
            raise RegistryOperationError(f"Failed to cleanup images: {e}") from e

    def close(self) -> None:
        """Close the registry client and cleanup resources."""
        if self._session:
            self._session.close()
        logger.info("Registry client closed")
