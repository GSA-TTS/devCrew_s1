"""Secrets management with Vault and AWS Secrets Manager integration."""

import os
import re
from abc import ABC, abstractmethod
from copy import deepcopy
from typing import Any, Dict, List, Optional


class SecretsBackend(ABC):
    """Abstract base class for secrets backends."""

    @abstractmethod
    def get_secret(self, path: str) -> Optional[str]:
        """Retrieve a secret by path.

        Args:
            path: Path to the secret.

        Returns:
            Secret value or None if not found.
        """
        pass

    @abstractmethod
    def list_secrets(self, path: str) -> List[str]:
        """List secrets at a path.

        Args:
            path: Path to list.

        Returns:
            List of secret names.
        """
        pass


class VaultBackend(SecretsBackend):
    """HashiCorp Vault secrets backend."""

    def __init__(
        self,
        url: Optional[str] = None,
        token: Optional[str] = None,
        namespace: Optional[str] = None,
    ) -> None:
        """Initialize Vault backend.

        Args:
            url: Vault server URL. Defaults to VAULT_ADDR env var.
            token: Vault token. Defaults to VAULT_TOKEN env var.
            namespace: Vault namespace. Defaults to VAULT_NAMESPACE env var.
        """
        self._url = url or os.environ.get("VAULT_ADDR", "http://localhost:8200")
        self._token = token or os.environ.get("VAULT_TOKEN", "")
        self._namespace = namespace or os.environ.get("VAULT_NAMESPACE")
        self._client: Any = None

    def _get_client(self) -> Any:
        """Get or create Vault client."""
        if self._client is None:
            try:
                import hvac

                self._client = hvac.Client(
                    url=self._url,
                    token=self._token,
                    namespace=self._namespace,
                )
            except ImportError:
                raise ImportError("hvac package required for Vault integration")
        return self._client

    def get_secret(self, path: str) -> Optional[str]:
        """Retrieve a secret from Vault.

        Args:
            path: Secret path in format 'mount/path#key'.

        Returns:
            Secret value or None.
        """
        try:
            if "#" in path:
                secret_path, key = path.rsplit("#", 1)
            else:
                secret_path = path
                key = "value"

            parts = secret_path.split("/", 1)
            mount = parts[0] if len(parts) > 1 else "secret"
            secret_name = parts[1] if len(parts) > 1 else parts[0]

            client = self._get_client()
            response = client.secrets.kv.v2.read_secret_version(
                path=secret_name,
                mount_point=mount,
            )
            data = response.get("data", {}).get("data", {})
            return data.get(key)
        except Exception:
            return None

    def list_secrets(self, path: str) -> List[str]:
        """List secrets at a Vault path.

        Args:
            path: Path to list.

        Returns:
            List of secret names.
        """
        try:
            parts = path.split("/", 1)
            mount = parts[0] if len(parts) > 1 else "secret"
            list_path = parts[1] if len(parts) > 1 else ""

            client = self._get_client()
            response = client.secrets.kv.v2.list_secrets(
                path=list_path,
                mount_point=mount,
            )
            return response.get("data", {}).get("keys", [])
        except Exception:
            return []


class AWSSecretsBackend(SecretsBackend):
    """AWS Secrets Manager backend."""

    def __init__(
        self,
        region_name: Optional[str] = None,
    ) -> None:
        """Initialize AWS Secrets Manager backend.

        Args:
            region_name: AWS region. Defaults to AWS_DEFAULT_REGION env var.
        """
        self._region = region_name or os.environ.get("AWS_DEFAULT_REGION", "us-east-1")
        self._client: Any = None

    def _get_client(self) -> Any:
        """Get or create AWS Secrets Manager client."""
        if self._client is None:
            try:
                import boto3

                self._client = boto3.client(
                    "secretsmanager",
                    region_name=self._region,
                )
            except ImportError:
                raise ImportError("boto3 package required for AWS integration")
        return self._client

    def get_secret(self, path: str) -> Optional[str]:
        """Retrieve a secret from AWS Secrets Manager.

        Args:
            path: Secret name, optionally with #key suffix.

        Returns:
            Secret value or None.
        """
        try:
            import json

            if "#" in path:
                secret_name, key = path.rsplit("#", 1)
            else:
                secret_name = path
                key = None

            client = self._get_client()
            response = client.get_secret_value(SecretId=secret_name)

            secret_string = response.get("SecretString", "")
            if key:
                data = json.loads(secret_string)
                return data.get(key)
            return secret_string
        except Exception:
            return None

    def list_secrets(self, path: str) -> List[str]:
        """List secrets in AWS Secrets Manager.

        Args:
            path: Prefix filter for secrets.

        Returns:
            List of secret names.
        """
        try:
            client = self._get_client()
            paginator = client.get_paginator("list_secrets")
            secrets = []

            for page in paginator.paginate():
                for secret in page.get("SecretList", []):
                    name = secret.get("Name", "")
                    if name.startswith(path):
                        secrets.append(name)

            return secrets
        except Exception:
            return []


class EnvBackend(SecretsBackend):
    """Environment variable secrets backend."""

    def __init__(self, prefix: str = "") -> None:
        """Initialize environment variable backend.

        Args:
            prefix: Prefix for environment variables.
        """
        self._prefix = prefix

    def get_secret(self, path: str) -> Optional[str]:
        """Retrieve a secret from environment variables.

        Args:
            path: Environment variable name (without prefix).

        Returns:
            Environment variable value or None.
        """
        var_name = f"{self._prefix}{path}" if self._prefix else path
        return os.environ.get(var_name)

    def list_secrets(self, path: str) -> List[str]:
        """List environment variables with given prefix.

        Args:
            path: Prefix to filter by.

        Returns:
            List of matching variable names.
        """
        full_prefix = f"{self._prefix}{path}" if self._prefix else path
        return [k for k in os.environ if k.startswith(full_prefix)]


class SecretsManager:
    """Manager for secrets with multiple backend support."""

    def __init__(self) -> None:
        """Initialize the secrets manager."""
        self._backends: Dict[str, SecretsBackend] = {}
        self._default_backend: Optional[str] = None

    def register_backend(
        self,
        name: str,
        backend: SecretsBackend,
        default: bool = False,
    ) -> None:
        """Register a secrets backend.

        Args:
            name: Name for the backend.
            backend: Backend instance.
            default: Set as default backend.
        """
        self._backends[name] = backend
        if default or self._default_backend is None:
            self._default_backend = name

    def get_secret(
        self,
        path: str,
        backend: Optional[str] = None,
    ) -> Optional[str]:
        """Get a secret from the specified backend.

        Args:
            path: Path to the secret.
            backend: Backend name. Uses default if not specified.

        Returns:
            Secret value or None.

        Raises:
            KeyError: If backend is not registered.
        """
        backend_name = backend or self._default_backend
        if backend_name is None or backend_name not in self._backends:
            raise KeyError(f"Backend not found: {backend_name}")
        return self._backends[backend_name].get_secret(path)

    def substitute_secrets(
        self,
        config: Dict[str, Any],
        pattern: str = r"\$\{secret:([^}]+)\}",
        backend: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Substitute secret placeholders in configuration.

        Args:
            config: Configuration dictionary.
            pattern: Regex pattern for secret placeholders.
            backend: Backend to use for secrets.

        Returns:
            Configuration with secrets substituted.
        """
        result = deepcopy(config)
        regex = re.compile(pattern)

        def substitute(value: Any) -> Any:
            if isinstance(value, str):
                matches = regex.findall(value)
                for match in matches:
                    secret_value = self.get_secret(match, backend)
                    if secret_value is not None:
                        placeholder = f"${{secret:{match}}}"
                        if value == placeholder:
                            return secret_value
                        value = value.replace(placeholder, secret_value)
                return value
            elif isinstance(value, dict):
                return {k: substitute(v) for k, v in value.items()}
            elif isinstance(value, list):
                return [substitute(item) for item in value]
            return value

        return substitute(result)

    def mask_secrets(
        self,
        config: Dict[str, Any],
        secret_paths: List[str],
        mask: str = "***MASKED***",
    ) -> Dict[str, Any]:
        """Mask secret values in configuration for safe display.

        Args:
            config: Configuration dictionary.
            secret_paths: List of paths to mask (dot notation).
            mask: Mask string to use.

        Returns:
            Configuration with masked secrets.
        """
        result = deepcopy(config)

        for secret_path in secret_paths:
            parts = secret_path.split(".")
            current = result
            for i, part in enumerate(parts[:-1]):
                if isinstance(current, dict) and part in current:
                    current = current[part]
                else:
                    break
            else:
                last_part = parts[-1]
                if isinstance(current, dict) and last_part in current:
                    current[last_part] = mask

        return result
