"""
Terraform state management for remote backends.

This module handles remote state operations including configuration,
locking, backup, and recovery for S3, Azure Blob, and GCS backends.
"""

import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Any, List
from dataclasses import dataclass


logger = logging.getLogger(__name__)


class StateError(Exception):
    """Base exception for state operations."""
    pass


class StateLockError(StateError):
    """Exception raised when state lock operations fail."""
    pass


class StateBackupError(StateError):
    """Exception raised when state backup operations fail."""
    pass


@dataclass
class StateLock:
    """Container for state lock information."""
    lock_id: str
    operation: str
    who: str
    version: str
    created: str
    path: str


@dataclass
class StateBackup:
    """Container for state backup information."""
    timestamp: str
    version: int
    size: int
    backend: str
    path: str


class StateManager:
    """
    Terraform state manager for remote backends.

    Handles state operations, locking, backup, and recovery across
    different cloud provider backends.
    """

    def __init__(self, backend_type: str, backend_config: Dict[str, str]):
        """
        Initialize state manager.

        Args:
            backend_type: Backend type (s3, azurerm, gcs)
            backend_config: Backend configuration parameters
        """
        self.backend_type = backend_type.lower()
        self.backend_config = backend_config
        self._client = None

        self._initialize_backend()

    def _initialize_backend(self) -> None:
        """Initialize backend-specific client."""
        if self.backend_type == "s3":
            self._initialize_s3()
        elif self.backend_type == "azurerm":
            self._initialize_azure()
        elif self.backend_type == "gcs":
            self._initialize_gcs()
        else:
            raise StateError(
                f"Unsupported backend type: {self.backend_type}. "
                f"Supported: s3, azurerm, gcs"
            )

    def _initialize_s3(self) -> None:
        """Initialize S3 backend client."""
        try:
            import boto3

            self._client = boto3.client(
                "s3",
                region_name=self.backend_config.get("region", "us-east-1")
            )

            # Verify bucket exists
            bucket = self.backend_config.get("bucket")
            if bucket:
                self._client.head_bucket(Bucket=bucket)
                logger.info(f"S3 backend initialized: {bucket}")

        except ImportError:
            raise StateError("boto3 not installed. Install with: pip install boto3")
        except Exception as e:
            logger.warning(f"S3 backend initialization failed: {e}")

    def _initialize_azure(self) -> None:
        """Initialize Azure Storage backend client."""
        try:
            from azure.storage.blob import BlobServiceClient
            from azure.identity import DefaultAzureCredential

            storage_account = self.backend_config.get("storage_account_name")
            access_key = self.backend_config.get("access_key")

            if access_key:
                account_url = f"https://{storage_account}.blob.core.windows.net"
                self._client = BlobServiceClient(
                    account_url=account_url,
                    credential=access_key
                )
            else:
                account_url = f"https://{storage_account}.blob.core.windows.net"
                self._client = BlobServiceClient(
                    account_url=account_url,
                    credential=DefaultAzureCredential()
                )

            logger.info(f"Azure Storage backend initialized: {storage_account}")

        except ImportError:
            raise StateError(
                "Azure SDK not installed. Install with: "
                "pip install azure-storage-blob azure-identity"
            )
        except Exception as e:
            logger.warning(f"Azure backend initialization failed: {e}")

    def _initialize_gcs(self) -> None:
        """Initialize GCS backend client."""
        try:
            from google.cloud import storage

            self._client = storage.Client()

            # Verify bucket exists
            bucket = self.backend_config.get("bucket")
            if bucket:
                bucket_obj = self._client.bucket(bucket)
                bucket_obj.exists()
                logger.info(f"GCS backend initialized: {bucket}")

        except ImportError:
            raise StateError(
                "Google Cloud SDK not installed. Install with: "
                "pip install google-cloud-storage"
            )
        except Exception as e:
            logger.warning(f"GCS backend initialization failed: {e}")

    def get_state(self) -> Dict[str, Any]:
        """
        Retrieve current state from backend.

        Returns:
            State as dictionary

        Raises:
            StateError: If state retrieval fails
        """
        try:
            if self.backend_type == "s3":
                return self._get_state_s3()
            elif self.backend_type == "azurerm":
                return self._get_state_azure()
            elif self.backend_type == "gcs":
                return self._get_state_gcs()
        except Exception as e:
            raise StateError(f"Failed to retrieve state: {e}")

    def _get_state_s3(self) -> Dict[str, Any]:
        """Get state from S3 backend."""
        bucket = self.backend_config["bucket"]
        key = self.backend_config["key"]

        response = self._client.get_object(Bucket=bucket, Key=key)
        state_data = response["Body"].read().decode("utf-8")

        return json.loads(state_data)

    def _get_state_azure(self) -> Dict[str, Any]:
        """Get state from Azure Storage backend."""
        from azure.storage.blob import BlobClient

        container = self.backend_config["container_name"]
        blob_name = self.backend_config["key"]

        blob_client = self._client.get_blob_client(
            container=container,
            blob=blob_name
        )

        state_data = blob_client.download_blob().readall().decode("utf-8")
        return json.loads(state_data)

    def _get_state_gcs(self) -> Dict[str, Any]:
        """Get state from GCS backend."""
        bucket_name = self.backend_config["bucket"]
        prefix = self.backend_config.get("prefix", "")
        blob_name = f"{prefix}/default.tfstate" if prefix else "default.tfstate"

        bucket = self._client.bucket(bucket_name)
        blob = bucket.blob(blob_name)

        state_data = blob.download_as_text()
        return json.loads(state_data)

    def backup_state(self, backup_path: Optional[Path] = None) -> StateBackup:
        """
        Create a backup of the current state.

        Args:
            backup_path: Local path to save backup (optional)

        Returns:
            StateBackup information

        Raises:
            StateBackupError: If backup fails
        """
        try:
            state = self.get_state()
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            if backup_path:
                backup_file = backup_path / f"terraform_state_{timestamp}.json"
                backup_file.write_text(json.dumps(state, indent=2))
                logger.info(f"State backed up to: {backup_file}")

            # Also backup to remote backend
            backup_info = self._backup_to_backend(state, timestamp)

            return StateBackup(
                timestamp=timestamp,
                version=state.get("version", 0),
                size=len(json.dumps(state)),
                backend=self.backend_type,
                path=backup_info
            )

        except Exception as e:
            raise StateBackupError(f"Failed to backup state: {e}")

    def _backup_to_backend(self, state: Dict[str, Any], timestamp: str) -> str:
        """
        Backup state to remote backend.

        Args:
            state: State data
            timestamp: Backup timestamp

        Returns:
            Backup location path
        """
        if self.backend_type == "s3":
            return self._backup_s3(state, timestamp)
        elif self.backend_type == "azurerm":
            return self._backup_azure(state, timestamp)
        elif self.backend_type == "gcs":
            return self._backup_gcs(state, timestamp)

    def _backup_s3(self, state: Dict[str, Any], timestamp: str) -> str:
        """Backup state to S3."""
        bucket = self.backend_config["bucket"]
        key = self.backend_config["key"]
        backup_key = f"{key}.{timestamp}.backup"

        self._client.put_object(
            Bucket=bucket,
            Key=backup_key,
            Body=json.dumps(state, indent=2).encode("utf-8"),
            ServerSideEncryption="AES256"
        )

        return f"s3://{bucket}/{backup_key}"

    def _backup_azure(self, state: Dict[str, Any], timestamp: str) -> str:
        """Backup state to Azure Storage."""
        container = self.backend_config["container_name"]
        blob_name = self.backend_config["key"]
        backup_blob = f"{blob_name}.{timestamp}.backup"

        blob_client = self._client.get_blob_client(
            container=container,
            blob=backup_blob
        )

        blob_client.upload_blob(
            json.dumps(state, indent=2).encode("utf-8"),
            overwrite=True
        )

        storage_account = self.backend_config["storage_account_name"]
        return f"https://{storage_account}.blob.core.windows.net/{container}/{backup_blob}"

    def _backup_gcs(self, state: Dict[str, Any], timestamp: str) -> str:
        """Backup state to GCS."""
        bucket_name = self.backend_config["bucket"]
        prefix = self.backend_config.get("prefix", "")
        blob_name = f"{prefix}/default.tfstate" if prefix else "default.tfstate"
        backup_blob = f"{blob_name}.{timestamp}.backup"

        bucket = self._client.bucket(bucket_name)
        blob = bucket.blob(backup_blob)

        blob.upload_from_string(
            json.dumps(state, indent=2),
            content_type="application/json"
        )

        return f"gs://{bucket_name}/{backup_blob}"

    def list_backups(self) -> List[StateBackup]:
        """
        List available state backups.

        Returns:
            List of StateBackup objects
        """
        if self.backend_type == "s3":
            return self._list_backups_s3()
        elif self.backend_type == "azurerm":
            return self._list_backups_azure()
        elif self.backend_type == "gcs":
            return self._list_backups_gcs()

        return []

    def _list_backups_s3(self) -> List[StateBackup]:
        """List backups in S3."""
        bucket = self.backend_config["bucket"]
        key = self.backend_config["key"]
        prefix = f"{key}."

        backups = []
        response = self._client.list_objects_v2(Bucket=bucket, Prefix=prefix)

        for obj in response.get("Contents", []):
            if obj["Key"].endswith(".backup"):
                timestamp = obj["Key"].split(".")[-2]
                backups.append(
                    StateBackup(
                        timestamp=timestamp,
                        version=0,
                        size=obj["Size"],
                        backend="s3",
                        path=f"s3://{bucket}/{obj['Key']}"
                    )
                )

        return sorted(backups, key=lambda x: x.timestamp, reverse=True)

    def _list_backups_azure(self) -> List[StateBackup]:
        """List backups in Azure Storage."""
        container = self.backend_config["container_name"]
        blob_name = self.backend_config["key"]

        backups = []
        container_client = self._client.get_container_client(container)
        blobs = container_client.list_blobs(name_starts_with=blob_name)

        for blob in blobs:
            if blob.name.endswith(".backup"):
                timestamp = blob.name.split(".")[-2]
                backups.append(
                    StateBackup(
                        timestamp=timestamp,
                        version=0,
                        size=blob.size,
                        backend="azurerm",
                        path=blob.name
                    )
                )

        return sorted(backups, key=lambda x: x.timestamp, reverse=True)

    def _list_backups_gcs(self) -> List[StateBackup]:
        """List backups in GCS."""
        bucket_name = self.backend_config["bucket"]
        prefix = self.backend_config.get("prefix", "")
        blob_prefix = f"{prefix}/default.tfstate" if prefix else "default.tfstate"

        backups = []
        bucket = self._client.bucket(bucket_name)
        blobs = bucket.list_blobs(prefix=blob_prefix)

        for blob in blobs:
            if blob.name.endswith(".backup"):
                timestamp = blob.name.split(".")[-2]
                backups.append(
                    StateBackup(
                        timestamp=timestamp,
                        version=0,
                        size=blob.size,
                        backend="gcs",
                        path=f"gs://{bucket_name}/{blob.name}"
                    )
                )

        return sorted(backups, key=lambda x: x.timestamp, reverse=True)

    def restore_state(self, backup: StateBackup) -> None:
        """
        Restore state from a backup.

        Args:
            backup: StateBackup to restore

        Raises:
            StateError: If restore fails
        """
        logger.warning(f"Restoring state from backup: {backup.path}")

        try:
            if self.backend_type == "s3":
                self._restore_s3(backup)
            elif self.backend_type == "azurerm":
                self._restore_azure(backup)
            elif self.backend_type == "gcs":
                self._restore_gcs(backup)

            logger.info("State restored successfully")

        except Exception as e:
            raise StateError(f"Failed to restore state: {e}")

    def _restore_s3(self, backup: StateBackup) -> None:
        """Restore state from S3 backup."""
        bucket = self.backend_config["bucket"]
        key = self.backend_config["key"]
        backup_key = backup.path.replace(f"s3://{bucket}/", "")

        # Copy backup to current state
        self._client.copy_object(
            Bucket=bucket,
            CopySource={"Bucket": bucket, "Key": backup_key},
            Key=key
        )

    def _restore_azure(self, backup: StateBackup) -> None:
        """Restore state from Azure Storage backup."""
        container = self.backend_config["container_name"]
        blob_name = self.backend_config["key"]

        source_blob = self._client.get_blob_client(
            container=container,
            blob=backup.path
        )

        dest_blob = self._client.get_blob_client(
            container=container,
            blob=blob_name
        )

        # Copy backup to current state
        dest_blob.start_copy_from_url(source_blob.url)

    def _restore_gcs(self, backup: StateBackup) -> None:
        """Restore state from GCS backup."""
        bucket_name = self.backend_config["bucket"]
        prefix = self.backend_config.get("prefix", "")
        current_blob = f"{prefix}/default.tfstate" if prefix else "default.tfstate"

        backup_blob_name = backup.path.replace(f"gs://{bucket_name}/", "")

        bucket = self._client.bucket(bucket_name)
        source_blob = bucket.blob(backup_blob_name)
        dest_blob = bucket.blob(current_blob)

        # Copy backup to current state
        bucket.copy_blob(source_blob, bucket, dest_blob.name)

    def check_lock(self) -> Optional[StateLock]:
        """
        Check if state is locked.

        Returns:
            StateLock if locked, None otherwise
        """
        if self.backend_type == "s3":
            return self._check_lock_s3()
        elif self.backend_type == "azurerm":
            return self._check_lock_azure()
        elif self.backend_type == "gcs":
            return self._check_lock_gcs()

        return None

    def _check_lock_s3(self) -> Optional[StateLock]:
        """Check S3 state lock using DynamoDB."""
        try:
            import boto3

            dynamodb_table = self.backend_config.get("dynamodb_table")
            if not dynamodb_table:
                return None

            dynamodb = boto3.resource(
                "dynamodb",
                region_name=self.backend_config.get("region", "us-east-1")
            )

            table = dynamodb.Table(dynamodb_table)
            key = self.backend_config["key"]

            response = table.get_item(Key={"LockID": key})

            if "Item" in response:
                item = response["Item"]
                return StateLock(
                    lock_id=item.get("LockID", ""),
                    operation=item.get("Operation", ""),
                    who=item.get("Who", ""),
                    version=item.get("Version", ""),
                    created=item.get("Created", ""),
                    path=item.get("Path", "")
                )

        except Exception as e:
            logger.warning(f"Failed to check S3 lock: {e}")

        return None

    def _check_lock_azure(self) -> Optional[StateLock]:
        """Check Azure Storage state lock."""
        try:
            container = self.backend_config["container_name"]
            blob_name = f"{self.backend_config['key']}.lock"

            blob_client = self._client.get_blob_client(
                container=container,
                blob=blob_name
            )

            if blob_client.exists():
                lock_data = json.loads(blob_client.download_blob().readall())
                return StateLock(**lock_data)

        except Exception as e:
            logger.warning(f"Failed to check Azure lock: {e}")

        return None

    def _check_lock_gcs(self) -> Optional[StateLock]:
        """Check GCS state lock."""
        try:
            bucket_name = self.backend_config["bucket"]
            prefix = self.backend_config.get("prefix", "")
            lock_blob = f"{prefix}/default.tflock" if prefix else "default.tflock"

            bucket = self._client.bucket(bucket_name)
            blob = bucket.blob(lock_blob)

            if blob.exists():
                lock_data = json.loads(blob.download_as_text())
                return StateLock(**lock_data)

        except Exception as e:
            logger.warning(f"Failed to check GCS lock: {e}")

        return None

    def force_unlock(self) -> None:
        """
        Force unlock the state.

        WARNING: Only use this if you're certain no other operation is running.

        Raises:
            StateLockError: If force unlock fails
        """
        logger.warning("Force unlocking state - use with caution!")

        try:
            if self.backend_type == "s3":
                self._force_unlock_s3()
            elif self.backend_type == "azurerm":
                self._force_unlock_azure()
            elif self.backend_type == "gcs":
                self._force_unlock_gcs()

            logger.info("State force unlocked")

        except Exception as e:
            raise StateLockError(f"Failed to force unlock: {e}")

    def _force_unlock_s3(self) -> None:
        """Force unlock S3 state."""
        import boto3

        dynamodb_table = self.backend_config.get("dynamodb_table")
        if not dynamodb_table:
            return

        dynamodb = boto3.resource(
            "dynamodb",
            region_name=self.backend_config.get("region", "us-east-1")
        )

        table = dynamodb.Table(dynamodb_table)
        key = self.backend_config["key"]

        table.delete_item(Key={"LockID": key})

    def _force_unlock_azure(self) -> None:
        """Force unlock Azure state."""
        container = self.backend_config["container_name"]
        blob_name = f"{self.backend_config['key']}.lock"

        blob_client = self._client.get_blob_client(
            container=container,
            blob=blob_name
        )

        if blob_client.exists():
            blob_client.delete_blob()

    def _force_unlock_gcs(self) -> None:
        """Force unlock GCS state."""
        bucket_name = self.backend_config["bucket"]
        prefix = self.backend_config.get("prefix", "")
        lock_blob = f"{prefix}/default.tflock" if prefix else "default.tflock"

        bucket = self._client.bucket(bucket_name)
        blob = bucket.blob(lock_blob)

        if blob.exists():
            blob.delete()
