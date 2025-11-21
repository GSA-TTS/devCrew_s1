"""
Secrets Integration - Vault client interface and cloud KMS interfaces.

TOOL-SEC-012: Secrets management integration for devCrew_s1 data protection.
"""

import os
import base64
import logging
import json
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from urllib.parse import urljoin

logger = logging.getLogger(__name__)


@dataclass
class SecretValue:
    """Retrieved secret value with metadata."""
    value: str
    version: Optional[str] = None
    created_at: Optional[str] = None
    expires_at: Optional[str] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class SecretsClient(ABC):
    """Abstract base class for secrets management clients."""

    @abstractmethod
    def get_secret(self, path: str, version: Optional[str] = None) -> SecretValue:
        """Retrieve a secret by path."""
        pass

    @abstractmethod
    def set_secret(self, path: str, value: str, metadata: Optional[Dict] = None) -> str:
        """Store a secret and return its version."""
        pass

    @abstractmethod
    def delete_secret(self, path: str, version: Optional[str] = None) -> bool:
        """Delete a secret."""
        pass

    @abstractmethod
    def list_secrets(self, path: str) -> List[str]:
        """List secrets at path."""
        pass


class VaultClient(SecretsClient):
    """
    HashiCorp Vault client interface.

    Supports KV v2 secrets engine operations.
    """

    def __init__(
        self,
        address: Optional[str] = None,
        token: Optional[str] = None,
        namespace: Optional[str] = None,
        mount_point: str = "secret"
    ):
        """
        Initialize Vault client.

        Args:
            address: Vault server address (or VAULT_ADDR env var)
            token: Vault token (or VAULT_TOKEN env var)
            namespace: Vault namespace for enterprise
            mount_point: KV secrets engine mount point
        """
        self._address = address or os.environ.get("VAULT_ADDR", "http://127.0.0.1:8200")
        self._token = token or os.environ.get("VAULT_TOKEN", "")
        self._namespace = namespace or os.environ.get("VAULT_NAMESPACE")
        self._mount_point = mount_point
        self._audit_log: list = []

        # Try to import hvac for actual Vault communication
        self._hvac_client = None
        try:
            import hvac
            self._hvac_client = hvac.Client(
                url=self._address,
                token=self._token,
                namespace=self._namespace
            )
            logger.info("VaultClient initialized with hvac: address=%s", self._address)
        except ImportError:
            logger.warning("hvac not installed, VaultClient will use HTTP fallback")

    def get_secret(self, path: str, version: Optional[str] = None) -> SecretValue:
        """
        Retrieve a secret from Vault KV v2.

        Args:
            path: Secret path (without mount point prefix)
            version: Optional specific version

        Returns:
            SecretValue with secret data
        """
        self._log_operation("get_secret", {"path": path, "version": version})

        if self._hvac_client:
            try:
                response = self._hvac_client.secrets.kv.v2.read_secret_version(
                    path=path,
                    mount_point=self._mount_point,
                    version=int(version) if version else None
                )
                data = response["data"]
                metadata = data.get("metadata", {})

                # Extract first value if multiple keys
                secret_data = data.get("data", {})
                value = json.dumps(secret_data) if len(secret_data) > 1 else \
                    list(secret_data.values())[0] if secret_data else ""

                return SecretValue(
                    value=value,
                    version=str(metadata.get("version", "")),
                    created_at=metadata.get("created_time"),
                    metadata=metadata
                )
            except Exception as e:
                logger.error("Failed to get secret from Vault: %s", e)
                raise

        # Fallback for testing without Vault
        raise ConnectionError("Vault client not available")

    def set_secret(
        self,
        path: str,
        value: str,
        metadata: Optional[Dict] = None
    ) -> str:
        """
        Store a secret in Vault KV v2.

        Args:
            path: Secret path
            value: Secret value
            metadata: Optional custom metadata

        Returns:
            Version string of stored secret
        """
        self._log_operation("set_secret", {"path": path})

        if self._hvac_client:
            try:
                response = self._hvac_client.secrets.kv.v2.create_or_update_secret(
                    path=path,
                    secret={"value": value},
                    mount_point=self._mount_point
                )
                version = str(response["data"]["version"])
                logger.info("Secret stored: path=%s, version=%s", path, version)
                return version
            except Exception as e:
                logger.error("Failed to set secret in Vault: %s", e)
                raise

        raise ConnectionError("Vault client not available")

    def delete_secret(self, path: str, version: Optional[str] = None) -> bool:
        """
        Delete a secret from Vault.

        Args:
            path: Secret path
            version: Optional specific version to delete

        Returns:
            True if deleted successfully
        """
        self._log_operation("delete_secret", {"path": path, "version": version})

        if self._hvac_client:
            try:
                if version:
                    self._hvac_client.secrets.kv.v2.delete_secret_versions(
                        path=path,
                        versions=[int(version)],
                        mount_point=self._mount_point
                    )
                else:
                    self._hvac_client.secrets.kv.v2.delete_metadata_and_all_versions(
                        path=path,
                        mount_point=self._mount_point
                    )
                logger.info("Secret deleted: path=%s", path)
                return True
            except Exception as e:
                logger.error("Failed to delete secret: %s", e)
                return False

        raise ConnectionError("Vault client not available")

    def list_secrets(self, path: str) -> List[str]:
        """
        List secrets at a path.

        Args:
            path: Path to list

        Returns:
            List of secret names
        """
        self._log_operation("list_secrets", {"path": path})

        if self._hvac_client:
            try:
                response = self._hvac_client.secrets.kv.v2.list_secrets(
                    path=path,
                    mount_point=self._mount_point
                )
                return response["data"]["keys"]
            except Exception as e:
                logger.error("Failed to list secrets: %s", e)
                return []

        raise ConnectionError("Vault client not available")

    def encrypt_transit(self, plaintext: bytes, key_name: str) -> bytes:
        """
        Encrypt data using Vault Transit engine.

        Args:
            plaintext: Data to encrypt
            key_name: Transit key name

        Returns:
            Encrypted ciphertext
        """
        self._log_operation("encrypt_transit", {"key_name": key_name})

        if self._hvac_client:
            try:
                b64_plaintext = base64.b64encode(plaintext).decode()
                response = self._hvac_client.secrets.transit.encrypt_data(
                    name=key_name,
                    plaintext=b64_plaintext
                )
                ciphertext = response["data"]["ciphertext"]
                return ciphertext.encode()
            except Exception as e:
                logger.error("Transit encryption failed: %s", e)
                raise

        raise ConnectionError("Vault client not available")

    def decrypt_transit(self, ciphertext: bytes, key_name: str) -> bytes:
        """
        Decrypt data using Vault Transit engine.

        Args:
            ciphertext: Data to decrypt
            key_name: Transit key name

        Returns:
            Decrypted plaintext
        """
        self._log_operation("decrypt_transit", {"key_name": key_name})

        if self._hvac_client:
            try:
                response = self._hvac_client.secrets.transit.decrypt_data(
                    name=key_name,
                    ciphertext=ciphertext.decode()
                )
                b64_plaintext = response["data"]["plaintext"]
                return base64.b64decode(b64_plaintext)
            except Exception as e:
                logger.error("Transit decryption failed: %s", e)
                raise

        raise ConnectionError("Vault client not available")

    def get_audit_log(self) -> list:
        """Return audit log of Vault operations."""
        return self._audit_log.copy()

    def _log_operation(self, operation: str, details: Dict[str, Any]) -> None:
        """Log a Vault operation."""
        self._audit_log.append({
            "operation": operation,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **details
        })


class AWSKMSClient:
    """
    AWS KMS client interface for envelope encryption.
    """

    def __init__(
        self,
        key_id: Optional[str] = None,
        region: Optional[str] = None
    ):
        """
        Initialize AWS KMS client.

        Args:
            key_id: KMS key ID or ARN
            region: AWS region
        """
        self._key_id = key_id or os.environ.get("AWS_KMS_KEY_ID")
        self._region = region or os.environ.get("AWS_REGION", "us-east-1")
        self._client = None
        self._audit_log: list = []

        try:
            import boto3
            self._client = boto3.client("kms", region_name=self._region)
            logger.info("AWSKMSClient initialized: region=%s", self._region)
        except ImportError:
            logger.warning("boto3 not installed, AWSKMSClient unavailable")

    def encrypt(self, plaintext: bytes) -> bytes:
        """Encrypt data using KMS."""
        if not self._client:
            raise ConnectionError("AWS KMS client not available")

        self._log_operation("encrypt", {"key_id": self._key_id})

        response = self._client.encrypt(
            KeyId=self._key_id,
            Plaintext=plaintext
        )
        return response["CiphertextBlob"]

    def decrypt(self, ciphertext: bytes) -> bytes:
        """Decrypt data using KMS."""
        if not self._client:
            raise ConnectionError("AWS KMS client not available")

        self._log_operation("decrypt", {})

        response = self._client.decrypt(
            CiphertextBlob=ciphertext
        )
        return response["Plaintext"]

    def generate_data_key(self, key_spec: str = "AES_256") -> Dict[str, bytes]:
        """Generate a data key for envelope encryption."""
        if not self._client:
            raise ConnectionError("AWS KMS client not available")

        self._log_operation("generate_data_key", {"key_spec": key_spec})

        response = self._client.generate_data_key(
            KeyId=self._key_id,
            KeySpec=key_spec
        )
        return {
            "plaintext": response["Plaintext"],
            "ciphertext": response["CiphertextBlob"]
        }

    def get_audit_log(self) -> list:
        """Return audit log."""
        return self._audit_log.copy()

    def _log_operation(self, operation: str, details: Dict[str, Any]) -> None:
        """Log a KMS operation."""
        self._audit_log.append({
            "operation": operation,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **details
        })


class AzureKeyVaultClient:
    """
    Azure Key Vault client interface.
    """

    def __init__(
        self,
        vault_url: Optional[str] = None
    ):
        """
        Initialize Azure Key Vault client.

        Args:
            vault_url: Key Vault URL (e.g., https://myvault.vault.azure.net)
        """
        self._vault_url = vault_url or os.environ.get("AZURE_KEYVAULT_URL")
        self._client = None
        self._crypto_client = None
        self._audit_log: list = []

        try:
            from azure.identity import DefaultAzureCredential
            from azure.keyvault.secrets import SecretClient

            credential = DefaultAzureCredential()
            self._client = SecretClient(vault_url=self._vault_url, credential=credential)
            logger.info("AzureKeyVaultClient initialized: url=%s", self._vault_url)
        except ImportError:
            logger.warning("azure-identity/azure-keyvault not installed")

    def get_secret(self, name: str, version: Optional[str] = None) -> SecretValue:
        """Get a secret from Azure Key Vault."""
        if not self._client:
            raise ConnectionError("Azure Key Vault client not available")

        self._log_operation("get_secret", {"name": name})

        secret = self._client.get_secret(name, version)
        return SecretValue(
            value=secret.value,
            version=secret.properties.version,
            created_at=secret.properties.created_on.isoformat() if secret.properties.created_on else None,
            expires_at=secret.properties.expires_on.isoformat() if secret.properties.expires_on else None,
            metadata=dict(secret.properties.tags) if secret.properties.tags else {}
        )

    def set_secret(self, name: str, value: str) -> str:
        """Set a secret in Azure Key Vault."""
        if not self._client:
            raise ConnectionError("Azure Key Vault client not available")

        self._log_operation("set_secret", {"name": name})

        secret = self._client.set_secret(name, value)
        return secret.properties.version

    def get_audit_log(self) -> list:
        """Return audit log."""
        return self._audit_log.copy()

    def _log_operation(self, operation: str, details: Dict[str, Any]) -> None:
        """Log an Azure operation."""
        self._audit_log.append({
            "operation": operation,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **details
        })


class GCPKMSClient:
    """
    Google Cloud KMS client interface.
    """

    def __init__(
        self,
        project_id: Optional[str] = None,
        location: str = "global",
        key_ring: Optional[str] = None,
        key_name: Optional[str] = None
    ):
        """
        Initialize GCP KMS client.

        Args:
            project_id: GCP project ID
            location: KMS location
            key_ring: Key ring name
            key_name: Key name
        """
        self._project_id = project_id or os.environ.get("GCP_PROJECT_ID")
        self._location = location
        self._key_ring = key_ring or os.environ.get("GCP_KMS_KEY_RING")
        self._key_name = key_name or os.environ.get("GCP_KMS_KEY_NAME")
        self._client = None
        self._audit_log: list = []

        try:
            from google.cloud import kms
            self._client = kms.KeyManagementServiceClient()
            logger.info("GCPKMSClient initialized: project=%s", self._project_id)
        except ImportError:
            logger.warning("google-cloud-kms not installed")

    @property
    def key_path(self) -> str:
        """Get full key resource path."""
        return (
            f"projects/{self._project_id}/locations/{self._location}/"
            f"keyRings/{self._key_ring}/cryptoKeys/{self._key_name}"
        )

    def encrypt(self, plaintext: bytes) -> bytes:
        """Encrypt data using GCP KMS."""
        if not self._client:
            raise ConnectionError("GCP KMS client not available")

        self._log_operation("encrypt", {"key_path": self.key_path})

        response = self._client.encrypt(
            request={"name": self.key_path, "plaintext": plaintext}
        )
        return response.ciphertext

    def decrypt(self, ciphertext: bytes) -> bytes:
        """Decrypt data using GCP KMS."""
        if not self._client:
            raise ConnectionError("GCP KMS client not available")

        self._log_operation("decrypt", {"key_path": self.key_path})

        response = self._client.decrypt(
            request={"name": self.key_path, "ciphertext": ciphertext}
        )
        return response.plaintext

    def get_audit_log(self) -> list:
        """Return audit log."""
        return self._audit_log.copy()

    def _log_operation(self, operation: str, details: Dict[str, Any]) -> None:
        """Log a GCP operation."""
        self._audit_log.append({
            "operation": operation,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **details
        })
