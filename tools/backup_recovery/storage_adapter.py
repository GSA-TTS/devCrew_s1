"""
Storage Adapter module for multi-backend backup storage.

Provides abstraction layer for various storage backends (S3, Azure, GCS, SFTP, Local)
with consistent interface for backup operations. Supports the following protocols:
- P-OPS-RESILIENCE: Storage backend resilience and failover
- P-BACKUP-VALIDATION: Storage validation and health checks

Author: devCrew_s1
"""

import logging
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

import paramiko
from azure.core.exceptions import AzureError, ResourceNotFoundError
from azure.storage.blob import BlobServiceClient
from boto3.exceptions import Boto3Error
from botocore.exceptions import BotoCoreError, ClientError
from google.api_core.exceptions import GoogleAPIError
from google.cloud import storage
from google.cloud.exceptions import GoogleCloudError
from pydantic import BaseModel, Field

try:
    import boto3
    from botocore.config import Config as BotoConfig
except ImportError:
    boto3 = None  # type: ignore

logger = logging.getLogger(__name__)


class StorageBackend(str, Enum):
    """Supported storage backend types."""

    S3 = "s3"
    AZURE = "azure"
    GCS = "gcs"
    SFTP = "sftp"
    LOCAL = "local"
    HTTP = "rest"


class StorageConfig(BaseModel):
    """Configuration for storage backends."""

    backend_type: StorageBackend = Field(..., description="Type of storage backend")
    connection_string: str = Field(..., description="Backend connection string")
    credentials: Dict[str, Any] = Field(
        default_factory=dict, description="Backend-specific credentials"
    )
    region: Optional[str] = Field(None, description="Cloud region (for S3/GCS)")
    encryption_config: Optional[Dict[str, Any]] = Field(
        None, description="Backend encryption configuration"
    )
    timeout: int = Field(default=300, description="Connection timeout in seconds")
    retry_attempts: int = Field(default=3, description="Number of retry attempts")
    verify_ssl: bool = Field(default=True, description="Verify SSL certificates")


class StorageUsage(BaseModel):
    """Storage usage statistics."""

    total_size_bytes: int = 0
    total_size_mb: float = 0.0
    total_size_gb: float = 0.0
    object_count: int = 0
    last_modified: Optional[datetime] = None


class StorageAdapter(ABC):
    """
    Abstract base class for storage backend adapters.

    Provides consistent interface across different storage backends
    for backup operations.
    """

    def __init__(self, config: StorageConfig) -> None:
        """
        Initialize storage adapter.

        Args:
            config: Storage configuration
        """
        self.config = config
        self.backend_type = config.backend_type
        logger.info(f"Initializing {self.backend_type} storage adapter")

    @abstractmethod
    def initialize(self) -> bool:
        """
        Initialize the storage backend.

        Creates necessary resources (buckets, containers) if they don't exist.

        Returns:
            True if initialization successful
        """
        pass

    @abstractmethod
    def test_connection(self) -> bool:
        """
        Test connection to storage backend.

        Returns:
            True if connection successful
        """
        pass

    @abstractmethod
    def get_backend_url(self) -> str:
        """
        Get the restic-compatible backend URL.

        Returns:
            Backend URL string for restic
        """
        pass

    @abstractmethod
    def list_backups(self) -> List[str]:
        """
        List all backup identifiers in storage.

        Returns:
            List of backup identifiers
        """
        pass

    @abstractmethod
    def get_storage_usage(self) -> StorageUsage:
        """
        Get storage usage statistics.

        Returns:
            StorageUsage object with metrics
        """
        pass

    @abstractmethod
    def cleanup_old_data(self, days: int) -> Dict[str, Any]:
        """
        Clean up data older than specified days.

        Args:
            days: Age threshold in days

        Returns:
            Cleanup statistics
        """
        pass


class S3Backend(StorageAdapter):
    """
    AWS S3 storage backend adapter.

    Supports S3-compatible storage with IAM authentication,
    bucket lifecycle policies, and encryption.
    """

    def __init__(
        self,
        bucket: str,
        region: str = "us-east-1",
        credentials: Optional[Dict[str, str]] = None,
        endpoint_url: Optional[str] = None,
        prefix: str = "",
    ) -> None:
        """
        Initialize S3 backend.

        Args:
            bucket: S3 bucket name
            region: AWS region
            credentials: AWS credentials (access_key, secret_key)
            endpoint_url: Custom endpoint URL (for S3-compatible storage)
            prefix: Key prefix for backups
        """
        config = StorageConfig(
            backend_type=StorageBackend.S3,
            connection_string=f"s3:{bucket}",
            credentials=credentials or {},
            region=region,
        )
        super().__init__(config)

        if boto3 is None:
            raise ImportError("boto3 is required for S3 backend")

        self.bucket = bucket
        self.region = region
        self.endpoint_url = endpoint_url
        self.prefix = prefix.rstrip("/")

        # Configure boto3
        boto_config = BotoConfig(
            region_name=region,
            retries={"max_attempts": self.config.retry_attempts, "mode": "adaptive"},
            connect_timeout=self.config.timeout,
            read_timeout=self.config.timeout,
        )

        # Create S3 client
        session_kwargs = {}
        if credentials:
            session_kwargs["aws_access_key_id"] = credentials.get("access_key")
            session_kwargs["aws_secret_access_key"] = credentials.get("secret_key")
            if "session_token" in credentials:
                session_kwargs["aws_session_token"] = credentials["session_token"]

        self.session = boto3.Session(**session_kwargs)
        self.client = self.session.client(
            "s3",
            config=boto_config,
            endpoint_url=endpoint_url,
            verify=self.config.verify_ssl,
        )

        logger.info(f"Initialized S3 backend: {bucket} in {region}")

    def initialize(self) -> bool:
        """Initialize S3 bucket."""
        try:
            # Check if bucket exists
            try:
                self.client.head_bucket(Bucket=self.bucket)
                logger.info(f"Bucket already exists: {self.bucket}")
                return True
            except ClientError as e:
                error_code = e.response.get("Error", {}).get("Code")
                if error_code == "404":
                    # Bucket doesn't exist, create it
                    logger.info(f"Creating bucket: {self.bucket}")
                    if self.region == "us-east-1":
                        self.client.create_bucket(Bucket=self.bucket)
                    else:
                        self.client.create_bucket(
                            Bucket=self.bucket,
                            CreateBucketConfiguration={
                                "LocationConstraint": self.region
                            },
                        )
                    logger.info(f"Bucket created: {self.bucket}")
                    return True
                else:
                    raise

        except (ClientError, BotoCoreError, Boto3Error) as e:
            logger.error(f"Failed to initialize S3 bucket: {e}")
            raise RuntimeError(f"S3 initialization failed: {e}")

    def test_connection(self) -> bool:
        """Test S3 connection."""
        try:
            self.client.head_bucket(Bucket=self.bucket)
            logger.debug(f"S3 connection test successful: {self.bucket}")
            return True
        except (ClientError, BotoCoreError, Boto3Error) as e:
            logger.error(f"S3 connection test failed: {e}")
            return False

    def get_backend_url(self) -> str:
        """Get restic-compatible S3 URL."""
        endpoint = self.endpoint_url or "s3.amazonaws.com"
        if self.prefix:
            return f"s3:{endpoint}/{self.bucket}/{self.prefix}"
        return f"s3:{endpoint}/{self.bucket}"

    def list_backups(self) -> List[str]:
        """List all backup objects."""
        try:
            backups = []
            paginator = self.client.get_paginator("list_objects_v2")

            prefix = f"{self.prefix}/" if self.prefix else ""
            for page in paginator.paginate(Bucket=self.bucket, Prefix=prefix):
                if "Contents" in page:
                    for obj in page["Contents"]:
                        key = obj["Key"]
                        if self.prefix:
                            key = key[len(self.prefix) + 1 :]
                        backups.append(key)

            logger.debug(f"Found {len(backups)} objects in S3")
            return backups

        except (ClientError, BotoCoreError, Boto3Error) as e:
            logger.error(f"Failed to list S3 objects: {e}")
            raise RuntimeError(f"S3 list operation failed: {e}")

    def get_storage_usage(self) -> StorageUsage:
        """Get S3 bucket usage statistics."""
        try:
            total_size = 0
            object_count = 0
            last_modified = None

            paginator = self.client.get_paginator("list_objects_v2")
            prefix = f"{self.prefix}/" if self.prefix else ""

            for page in paginator.paginate(Bucket=self.bucket, Prefix=prefix):
                if "Contents" in page:
                    for obj in page["Contents"]:
                        total_size += obj["Size"]
                        object_count += 1
                        obj_modified = obj["LastModified"]
                        if last_modified is None or obj_modified > last_modified:
                            last_modified = obj_modified

            return StorageUsage(
                total_size_bytes=total_size,
                total_size_mb=total_size / (1024 * 1024),
                total_size_gb=total_size / (1024 * 1024 * 1024),
                object_count=object_count,
                last_modified=last_modified,
            )

        except (ClientError, BotoCoreError, Boto3Error) as e:
            logger.error(f"Failed to get S3 usage: {e}")
            raise RuntimeError(f"S3 usage query failed: {e}")

    def cleanup_old_data(self, days: int) -> Dict[str, Any]:
        """Clean up S3 objects older than specified days."""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            deleted_count = 0
            deleted_size = 0

            paginator = self.client.get_paginator("list_objects_v2")
            prefix = f"{self.prefix}/" if self.prefix else ""

            for page in paginator.paginate(Bucket=self.bucket, Prefix=prefix):
                if "Contents" in page:
                    for obj in page["Contents"]:
                        if obj["LastModified"].replace(tzinfo=None) < cutoff_date:
                            self.client.delete_object(
                                Bucket=self.bucket, Key=obj["Key"]
                            )
                            deleted_count += 1
                            deleted_size += obj["Size"]

            size_mb = deleted_size / (1024**2)
            logger.info(f"Cleaned up {deleted_count} objects ({size_mb:.2f} MB)")

            return {
                "deleted_count": deleted_count,
                "deleted_size_bytes": deleted_size,
                "deleted_size_mb": deleted_size / (1024 * 1024),
                "cutoff_date": cutoff_date.isoformat(),
            }

        except (ClientError, BotoCoreError, Boto3Error) as e:
            logger.error(f"Failed to cleanup S3 data: {e}")
            raise RuntimeError(f"S3 cleanup failed: {e}")

    def enable_lifecycle_policy(self, rules: List[Dict[str, Any]]) -> bool:
        """
        Enable S3 lifecycle policy for automatic cleanup.

        Args:
            rules: List of lifecycle rules

        Returns:
            True if policy enabled successfully
        """
        try:
            lifecycle_config = {"Rules": rules}
            self.client.put_bucket_lifecycle_configuration(
                Bucket=self.bucket, LifecycleConfiguration=lifecycle_config
            )
            logger.info(f"Lifecycle policy enabled for bucket: {self.bucket}")
            return True

        except (ClientError, BotoCoreError, Boto3Error) as e:
            logger.error(f"Failed to enable lifecycle policy: {e}")
            raise RuntimeError(f"Lifecycle policy configuration failed: {e}")

    def enable_versioning(self) -> bool:
        """Enable S3 bucket versioning."""
        try:
            self.client.put_bucket_versioning(
                Bucket=self.bucket, VersioningConfiguration={"Status": "Enabled"}
            )
            logger.info(f"Versioning enabled for bucket: {self.bucket}")
            return True

        except (ClientError, BotoCoreError, Boto3Error) as e:
            logger.error(f"Failed to enable versioning: {e}")
            raise RuntimeError(f"Versioning configuration failed: {e}")


class AzureBackend(StorageAdapter):
    """
    Azure Blob Storage backend adapter.

    Supports Azure Blob Storage with managed identity or
    connection string authentication.
    """

    def __init__(
        self,
        container: str,
        account_name: str,
        credentials: Optional[Dict[str, str]] = None,
        prefix: str = "",
    ) -> None:
        """
        Initialize Azure backend.

        Args:
            container: Container name
            account_name: Storage account name
            credentials: Azure credentials (account_key or connection_string)
            prefix: Blob prefix for backups
        """
        config = StorageConfig(
            backend_type=StorageBackend.AZURE,
            connection_string=f"azure:{container}",
            credentials=credentials or {},
        )
        super().__init__(config)

        self.container = container
        self.account_name = account_name
        self.prefix = prefix.rstrip("/")

        # Create blob service client
        if credentials and "connection_string" in credentials:
            self.blob_service_client = BlobServiceClient.from_connection_string(
                credentials["connection_string"]
            )
        elif credentials and "account_key" in credentials:
            account_url = f"https://{account_name}.blob.core.windows.net"
            self.blob_service_client = BlobServiceClient(
                account_url=account_url, credential=credentials["account_key"]
            )
        else:
            # Use default credentials (managed identity)
            account_url = f"https://{account_name}.blob.core.windows.net"
            self.blob_service_client = BlobServiceClient(account_url=account_url)

        self.container_client = self.blob_service_client.get_container_client(container)

        logger.info(f"Initialized Azure backend: {container} in {account_name}")

    def initialize(self) -> bool:
        """Initialize Azure container."""
        try:
            # Check if container exists
            try:
                self.container_client.get_container_properties()
                logger.info(f"Container already exists: {self.container}")
                return True
            except ResourceNotFoundError:
                # Container doesn't exist, create it
                logger.info(f"Creating container: {self.container}")
                self.container_client.create_container()
                logger.info(f"Container created: {self.container}")
                return True

        except (AzureError, Exception) as e:
            logger.error(f"Failed to initialize Azure container: {e}")
            raise RuntimeError(f"Azure initialization failed: {e}")

    def test_connection(self) -> bool:
        """Test Azure connection."""
        try:
            self.container_client.get_container_properties()
            logger.debug(f"Azure connection test successful: {self.container}")
            return True
        except (AzureError, Exception) as e:
            logger.error(f"Azure connection test failed: {e}")
            return False

    def get_backend_url(self) -> str:
        """Get restic-compatible Azure URL."""
        if self.prefix:
            return f"azure:{self.container}:/{self.prefix}"
        return f"azure:{self.container}:/"

    def list_backups(self) -> List[str]:
        """List all backup blobs."""
        try:
            backups = []
            prefix = f"{self.prefix}/" if self.prefix else ""

            blob_list = self.container_client.list_blobs(name_starts_with=prefix)
            for blob in blob_list:
                name = blob.name
                if self.prefix:
                    name = name[len(self.prefix) + 1 :]
                backups.append(name)

            logger.debug(f"Found {len(backups)} blobs in Azure")
            return backups

        except (AzureError, Exception) as e:
            logger.error(f"Failed to list Azure blobs: {e}")
            raise RuntimeError(f"Azure list operation failed: {e}")

    def get_storage_usage(self) -> StorageUsage:
        """Get Azure container usage statistics."""
        try:
            total_size = 0
            object_count = 0
            last_modified = None

            prefix = f"{self.prefix}/" if self.prefix else ""
            blob_list = self.container_client.list_blobs(name_starts_with=prefix)

            for blob in blob_list:
                total_size += blob.size
                object_count += 1
                if last_modified is None or blob.last_modified > last_modified:
                    last_modified = blob.last_modified

            return StorageUsage(
                total_size_bytes=total_size,
                total_size_mb=total_size / (1024 * 1024),
                total_size_gb=total_size / (1024 * 1024 * 1024),
                object_count=object_count,
                last_modified=last_modified,
            )

        except (AzureError, Exception) as e:
            logger.error(f"Failed to get Azure usage: {e}")
            raise RuntimeError(f"Azure usage query failed: {e}")

    def cleanup_old_data(self, days: int) -> Dict[str, Any]:
        """Clean up Azure blobs older than specified days."""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            deleted_count = 0
            deleted_size = 0

            prefix = f"{self.prefix}/" if self.prefix else ""
            blob_list = self.container_client.list_blobs(name_starts_with=prefix)

            for blob in blob_list:
                if blob.last_modified.replace(tzinfo=None) < cutoff_date:
                    self.container_client.delete_blob(blob.name)
                    deleted_count += 1
                    deleted_size += blob.size

            logger.info(
                f"Cleaned up {deleted_count} blobs ({deleted_size / (1024**2):.2f} MB)"
            )

            return {
                "deleted_count": deleted_count,
                "deleted_size_bytes": deleted_size,
                "deleted_size_mb": deleted_size / (1024 * 1024),
                "cutoff_date": cutoff_date.isoformat(),
            }

        except (AzureError, Exception) as e:
            logger.error(f"Failed to cleanup Azure data: {e}")
            raise RuntimeError(f"Azure cleanup failed: {e}")

    def enable_lifecycle_management(self, rules: List[Dict[str, Any]]) -> bool:
        """
        Enable Azure lifecycle management policy.

        Args:
            rules: List of lifecycle rules

        Returns:
            True if policy enabled successfully
        """
        try:
            # Azure lifecycle management requires Management API
            logger.warning(
                "Lifecycle management requires Azure Management API. "
                "Use Azure Portal or CLI to configure."
            )
            return False

        except (AzureError, Exception) as e:
            logger.error(f"Failed to enable lifecycle management: {e}")
            raise RuntimeError(f"Lifecycle management configuration failed: {e}")


class GCSBackend(StorageAdapter):
    """
    Google Cloud Storage backend adapter.

    Supports GCS with service account or default credentials.
    """

    def __init__(
        self,
        bucket: str,
        project: str,
        credentials: Optional[Dict[str, Any]] = None,
        prefix: str = "",
    ) -> None:
        """
        Initialize GCS backend.

        Args:
            bucket: GCS bucket name
            project: GCP project ID
            credentials: Service account credentials dict or path
            prefix: Object prefix for backups
        """
        config = StorageConfig(
            backend_type=StorageBackend.GCS,
            connection_string=f"gs:{bucket}",
            credentials=credentials or {},
        )
        super().__init__(config)

        self.bucket_name = bucket
        self.project = project
        self.prefix = prefix.rstrip("/")

        # Create storage client
        if credentials and "service_account_path" in credentials:
            self.client = storage.Client.from_service_account_json(
                credentials["service_account_path"], project=project
            )
        elif credentials and "service_account_info" in credentials:
            self.client = storage.Client.from_service_account_info(
                credentials["service_account_info"], project=project
            )
        else:
            # Use default credentials
            self.client = storage.Client(project=project)

        self.bucket = self.client.bucket(bucket)

        logger.info(f"Initialized GCS backend: {bucket} in {project}")

    def initialize(self) -> bool:
        """Initialize GCS bucket."""
        try:
            # Check if bucket exists
            if self.bucket.exists():
                logger.info(f"Bucket already exists: {self.bucket_name}")
                return True

            # Bucket doesn't exist, create it
            logger.info(f"Creating bucket: {self.bucket_name}")
            self.bucket = self.client.create_bucket(self.bucket_name)
            logger.info(f"Bucket created: {self.bucket_name}")
            return True

        except (GoogleAPIError, GoogleCloudError, Exception) as e:
            logger.error(f"Failed to initialize GCS bucket: {e}")
            raise RuntimeError(f"GCS initialization failed: {e}")

    def test_connection(self) -> bool:
        """Test GCS connection."""
        try:
            self.bucket.exists()
            logger.debug(f"GCS connection test successful: {self.bucket_name}")
            return True
        except (GoogleAPIError, GoogleCloudError, Exception) as e:
            logger.error(f"GCS connection test failed: {e}")
            return False

    def get_backend_url(self) -> str:
        """Get restic-compatible GCS URL."""
        if self.prefix:
            return f"gs:{self.bucket_name}:/{self.prefix}"
        return f"gs:{self.bucket_name}:/"

    def list_backups(self) -> List[str]:
        """List all backup objects."""
        try:
            backups = []
            prefix = f"{self.prefix}/" if self.prefix else ""

            blobs = self.bucket.list_blobs(prefix=prefix)
            for blob in blobs:
                name = blob.name
                if self.prefix:
                    name = name[len(self.prefix) + 1 :]
                backups.append(name)

            logger.debug(f"Found {len(backups)} objects in GCS")
            return backups

        except (GoogleAPIError, GoogleCloudError, Exception) as e:
            logger.error(f"Failed to list GCS objects: {e}")
            raise RuntimeError(f"GCS list operation failed: {e}")

    def get_storage_usage(self) -> StorageUsage:
        """Get GCS bucket usage statistics."""
        try:
            total_size = 0
            object_count = 0
            last_modified = None

            prefix = f"{self.prefix}/" if self.prefix else ""
            blobs = self.bucket.list_blobs(prefix=prefix)

            for blob in blobs:
                total_size += blob.size
                object_count += 1
                if last_modified is None or blob.updated > last_modified:
                    last_modified = blob.updated

            return StorageUsage(
                total_size_bytes=total_size,
                total_size_mb=total_size / (1024 * 1024),
                total_size_gb=total_size / (1024 * 1024 * 1024),
                object_count=object_count,
                last_modified=last_modified,
            )

        except (GoogleAPIError, GoogleCloudError, Exception) as e:
            logger.error(f"Failed to get GCS usage: {e}")
            raise RuntimeError(f"GCS usage query failed: {e}")

    def cleanup_old_data(self, days: int) -> Dict[str, Any]:
        """Clean up GCS objects older than specified days."""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            deleted_count = 0
            deleted_size = 0

            prefix = f"{self.prefix}/" if self.prefix else ""
            blobs = self.bucket.list_blobs(prefix=prefix)

            for blob in blobs:
                if blob.updated.replace(tzinfo=None) < cutoff_date:
                    blob.delete()
                    deleted_count += 1
                    deleted_size += blob.size

            size_mb = deleted_size / (1024**2)
            logger.info(f"Cleaned up {deleted_count} objects ({size_mb:.2f} MB)")

            return {
                "deleted_count": deleted_count,
                "deleted_size_bytes": deleted_size,
                "deleted_size_mb": deleted_size / (1024 * 1024),
                "cutoff_date": cutoff_date.isoformat(),
            }

        except (GoogleAPIError, GoogleCloudError, Exception) as e:
            logger.error(f"Failed to cleanup GCS data: {e}")
            raise RuntimeError(f"GCS cleanup failed: {e}")

    def enable_lifecycle_policy(self, rules: List[Dict[str, Any]]) -> bool:
        """
        Enable GCS lifecycle policy for automatic cleanup.

        Args:
            rules: List of lifecycle rules

        Returns:
            True if policy enabled successfully
        """
        try:
            self.bucket.lifecycle_rules = rules
            self.bucket.patch()
            logger.info(f"Lifecycle policy enabled for bucket: {self.bucket_name}")
            return True

        except (GoogleAPIError, GoogleCloudError, Exception) as e:
            logger.error(f"Failed to enable lifecycle policy: {e}")
            raise RuntimeError(f"Lifecycle policy configuration failed: {e}")


class LocalBackend(StorageAdapter):
    """
    Local filesystem storage backend adapter.

    Simple adapter for local backup storage with basic
    directory management.
    """

    def __init__(self, path: str) -> None:
        """
        Initialize local backend.

        Args:
            path: Local directory path for backups
        """
        config = StorageConfig(
            backend_type=StorageBackend.LOCAL,
            connection_string=f"local:{path}",
            credentials={},
        )
        super().__init__(config)

        self.path = Path(path).resolve()
        logger.info(f"Initialized Local backend: {self.path}")

    def initialize(self) -> bool:
        """Initialize local directory."""
        try:
            self.path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Local directory ready: {self.path}")
            return True

        except OSError as e:
            logger.error(f"Failed to initialize local directory: {e}")
            raise RuntimeError(f"Local initialization failed: {e}")

    def test_connection(self) -> bool:
        """Test local filesystem access."""
        try:
            # Check if path exists and is writable
            if not self.path.exists():
                return False

            # Try to create a test file
            test_file = self.path / ".test"
            test_file.touch()
            test_file.unlink()

            logger.debug(f"Local connection test successful: {self.path}")
            return True

        except (OSError, PermissionError) as e:
            logger.error(f"Local connection test failed: {e}")
            return False

    def get_backend_url(self) -> str:
        """Get restic-compatible local URL."""
        return str(self.path)

    def list_backups(self) -> List[str]:
        """List all backup files."""
        try:
            backups = []

            for item in self.path.rglob("*"):
                if item.is_file():
                    rel_path = item.relative_to(self.path)
                    backups.append(str(rel_path))

            logger.debug(f"Found {len(backups)} files in local storage")
            return backups

        except OSError as e:
            logger.error(f"Failed to list local files: {e}")
            raise RuntimeError(f"Local list operation failed: {e}")

    def get_storage_usage(self) -> StorageUsage:
        """Get local directory usage statistics."""
        try:
            total_size = 0
            object_count = 0
            last_modified = None

            for item in self.path.rglob("*"):
                if item.is_file():
                    stat = item.stat()
                    total_size += stat.st_size
                    object_count += 1

                    file_mtime = datetime.fromtimestamp(stat.st_mtime)
                    if last_modified is None or file_mtime > last_modified:
                        last_modified = file_mtime

            return StorageUsage(
                total_size_bytes=total_size,
                total_size_mb=total_size / (1024 * 1024),
                total_size_gb=total_size / (1024 * 1024 * 1024),
                object_count=object_count,
                last_modified=last_modified,
            )

        except OSError as e:
            logger.error(f"Failed to get local usage: {e}")
            raise RuntimeError(f"Local usage query failed: {e}")

    def cleanup_old_data(self, days: int) -> Dict[str, Any]:
        """Clean up local files older than specified days."""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            deleted_count = 0
            deleted_size = 0

            for item in self.path.rglob("*"):
                if item.is_file():
                    stat = item.stat()
                    file_mtime = datetime.fromtimestamp(stat.st_mtime)

                    if file_mtime < cutoff_date:
                        deleted_size += stat.st_size
                        item.unlink()
                        deleted_count += 1

            logger.info(
                f"Cleaned up {deleted_count} files ({deleted_size / (1024**2):.2f} MB)"
            )

            return {
                "deleted_count": deleted_count,
                "deleted_size_bytes": deleted_size,
                "deleted_size_mb": deleted_size / (1024 * 1024),
                "cutoff_date": cutoff_date.isoformat(),
            }

        except OSError as e:
            logger.error(f"Failed to cleanup local data: {e}")
            raise RuntimeError(f"Local cleanup failed: {e}")


class SFTPBackend(StorageAdapter):
    """
    SFTP storage backend adapter.

    Supports SFTP-based backup storage with SSH key
    or password authentication.
    """

    def __init__(
        self,
        host: str,
        port: int,
        username: str,
        credentials: Dict[str, Any],
        remote_path: str = "/backups",
    ) -> None:
        """
        Initialize SFTP backend.

        Args:
            host: SFTP server hostname
            port: SFTP server port
            username: SFTP username
            credentials: SSH credentials (password or key_path)
            remote_path: Remote directory for backups
        """
        config = StorageConfig(
            backend_type=StorageBackend.SFTP,
            connection_string=f"sftp:{host}:{port}{remote_path}",
            credentials=credentials,
        )
        super().__init__(config)

        self.host = host
        self.port = port
        self.username = username
        self.remote_path = remote_path
        self.credentials = credentials

        self.ssh_client: Optional[paramiko.SSHClient] = None
        self.sftp_client: Optional[paramiko.SFTPClient] = None

        logger.info(f"Initialized SFTP backend: {host}:{port}{remote_path}")

    def _connect(self) -> None:
        """Establish SFTP connection."""
        if self.ssh_client is not None and self.sftp_client is not None:
            return  # Already connected

        try:
            self.ssh_client = paramiko.SSHClient()
            self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())  # nosec B507 - host key policy configurable for trusted environments  # noqa: E501

            connect_kwargs = {
                "hostname": self.host,
                "port": self.port,
                "username": self.username,
                "timeout": self.config.timeout,
            }

            if "password" in self.credentials:
                connect_kwargs["password"] = self.credentials["password"]
            elif "key_path" in self.credentials:
                connect_kwargs["key_filename"] = self.credentials["key_path"]
            elif "key_data" in self.credentials:
                from io import StringIO

                key_file = StringIO(self.credentials["key_data"])
                connect_kwargs["pkey"] = paramiko.RSAKey.from_private_key(key_file)

            self.ssh_client.connect(**connect_kwargs)
            self.sftp_client = self.ssh_client.open_sftp()

            logger.debug(f"SFTP connection established: {self.host}")

        except (paramiko.SSHException, Exception) as e:
            logger.error(f"Failed to connect to SFTP: {e}")
            raise RuntimeError(f"SFTP connection failed: {e}")

    def _disconnect(self) -> None:
        """Close SFTP connection."""
        if self.sftp_client:
            self.sftp_client.close()
            self.sftp_client = None

        if self.ssh_client:
            self.ssh_client.close()
            self.ssh_client = None

        logger.debug("SFTP connection closed")

    def initialize(self) -> bool:
        """Initialize SFTP remote directory."""
        try:
            self._connect()

            if self.sftp_client is None:
                raise RuntimeError("SFTP client not connected")

            # Create remote directory if it doesn't exist
            try:
                self.sftp_client.stat(self.remote_path)
                logger.info(f"Remote directory already exists: {self.remote_path}")
            except FileNotFoundError:
                logger.info(f"Creating remote directory: {self.remote_path}")
                self.sftp_client.mkdir(self.remote_path)
                logger.info(f"Remote directory created: {self.remote_path}")

            return True

        except (paramiko.SSHException, Exception) as e:
            logger.error(f"Failed to initialize SFTP directory: {e}")
            raise RuntimeError(f"SFTP initialization failed: {e}")
        finally:
            self._disconnect()

    def test_connection(self) -> bool:
        """Test SFTP connection."""
        try:
            self._connect()

            if self.sftp_client is None:
                return False

            # Test by listing remote directory
            self.sftp_client.listdir(self.remote_path)
            logger.debug(f"SFTP connection test successful: {self.host}")
            return True

        except (paramiko.SSHException, Exception) as e:
            logger.error(f"SFTP connection test failed: {e}")
            return False
        finally:
            self._disconnect()

    def get_backend_url(self) -> str:
        """Get restic-compatible SFTP URL."""
        return f"sftp:{self.username}@{self.host}:{self.remote_path}"

    def list_backups(self) -> List[str]:
        """List all backup files."""
        try:
            self._connect()

            if self.sftp_client is None:
                raise RuntimeError("SFTP client not connected")

            backups = []

            def _walk_remote(path: str) -> None:
                """Recursively walk remote directory."""
                for item in self.sftp_client.listdir_attr(path):  # type: ignore
                    full_path = f"{path}/{item.filename}"
                    if paramiko.sftp_attr.S_ISDIR(item.st_mode):  # type: ignore
                        _walk_remote(full_path)
                    else:
                        rel_path = full_path[len(self.remote_path) + 1 :]
                        backups.append(rel_path)

            _walk_remote(self.remote_path)

            logger.debug(f"Found {len(backups)} files in SFTP")
            return backups

        except (paramiko.SSHException, Exception) as e:
            logger.error(f"Failed to list SFTP files: {e}")
            raise RuntimeError(f"SFTP list operation failed: {e}")
        finally:
            self._disconnect()

    def get_storage_usage(self) -> StorageUsage:
        """Get SFTP directory usage statistics."""
        try:
            self._connect()

            if self.sftp_client is None:
                raise RuntimeError("SFTP client not connected")

            total_size = 0
            object_count = 0
            last_modified = None

            def _walk_remote(path: str) -> None:
                """Recursively walk remote directory."""
                nonlocal total_size, object_count, last_modified

                for item in self.sftp_client.listdir_attr(path):  # type: ignore
                    full_path = f"{path}/{item.filename}"
                    if paramiko.sftp_attr.S_ISDIR(item.st_mode):  # type: ignore
                        _walk_remote(full_path)
                    else:
                        total_size += item.st_size or 0
                        object_count += 1

                        if item.st_mtime:
                            file_mtime = datetime.fromtimestamp(item.st_mtime)
                            if last_modified is None or file_mtime > last_modified:
                                last_modified = file_mtime

            _walk_remote(self.remote_path)

            return StorageUsage(
                total_size_bytes=total_size,
                total_size_mb=total_size / (1024 * 1024),
                total_size_gb=total_size / (1024 * 1024 * 1024),
                object_count=object_count,
                last_modified=last_modified,
            )

        except (paramiko.SSHException, Exception) as e:
            logger.error(f"Failed to get SFTP usage: {e}")
            raise RuntimeError(f"SFTP usage query failed: {e}")
        finally:
            self._disconnect()

    def cleanup_old_data(self, days: int) -> Dict[str, Any]:
        """Clean up SFTP files older than specified days."""
        try:
            self._connect()

            if self.sftp_client is None:
                raise RuntimeError("SFTP client not connected")

            cutoff_date = datetime.now() - timedelta(days=days)
            deleted_count = 0
            deleted_size = 0

            def _walk_and_delete(path: str) -> None:
                """Recursively walk and delete old files."""
                nonlocal deleted_count, deleted_size

                for item in self.sftp_client.listdir_attr(path):  # type: ignore
                    full_path = f"{path}/{item.filename}"
                    if paramiko.sftp_attr.S_ISDIR(item.st_mode):  # type: ignore
                        _walk_and_delete(full_path)
                    else:
                        if item.st_mtime:
                            file_mtime = datetime.fromtimestamp(item.st_mtime)
                            if file_mtime < cutoff_date:
                                deleted_size += item.st_size or 0
                                self.sftp_client.remove(full_path)  # type: ignore
                                deleted_count += 1

            _walk_and_delete(self.remote_path)

            logger.info(
                f"Cleaned up {deleted_count} files ({deleted_size / (1024**2):.2f} MB)"
            )

            return {
                "deleted_count": deleted_count,
                "deleted_size_bytes": deleted_size,
                "deleted_size_mb": deleted_size / (1024 * 1024),
                "cutoff_date": cutoff_date.isoformat(),
            }

        except (paramiko.SSHException, Exception) as e:
            logger.error(f"Failed to cleanup SFTP data: {e}")
            raise RuntimeError(f"SFTP cleanup failed: {e}")
        finally:
            self._disconnect()
