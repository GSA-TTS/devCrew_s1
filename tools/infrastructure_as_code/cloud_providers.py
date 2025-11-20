"""
Multi-cloud provider support for AWS, Azure, and GCP.

This module provides unified interfaces for interacting with different
cloud providers, handling credentials, regions, and provider-specific
configurations for Terraform operations.
"""

import logging
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Optional, Any, List
from pathlib import Path


logger = logging.getLogger(__name__)


class CloudProviderError(Exception):
    """Base exception for cloud provider operations."""
    pass


class CredentialsError(CloudProviderError):
    """Exception raised when credentials are invalid or missing."""
    pass


@dataclass
class ProviderConfig:
    """Base configuration for cloud providers."""
    name: str
    region: str
    credentials: Dict[str, str]
    tags: Optional[Dict[str, str]] = None


class CloudProvider(ABC):
    """
    Abstract base class for cloud providers.

    Defines the interface that all cloud provider implementations must follow.
    """

    def __init__(self, config: ProviderConfig):
        """
        Initialize cloud provider.

        Args:
            config: Provider configuration
        """
        self.config = config
        self.validate_credentials()

    @abstractmethod
    def validate_credentials(self) -> bool:
        """
        Validate provider credentials.

        Returns:
            True if credentials are valid

        Raises:
            CredentialsError: If credentials are invalid
        """
        pass

    @abstractmethod
    def get_terraform_backend_config(self) -> Dict[str, str]:
        """
        Get Terraform backend configuration for this provider.

        Returns:
            Backend configuration dictionary
        """
        pass

    @abstractmethod
    def get_terraform_provider_block(self) -> str:
        """
        Generate Terraform provider configuration block.

        Returns:
            Terraform provider block as string
        """
        pass

    @abstractmethod
    def list_regions(self) -> List[str]:
        """
        List available regions for this provider.

        Returns:
            List of region identifiers
        """
        pass


class AWSProvider(CloudProvider):
    """
    AWS cloud provider implementation.

    Handles AWS-specific configuration, credentials, and Terraform integration.
    """

    def __init__(self, config: ProviderConfig):
        """Initialize AWS provider."""
        super().__init__(config)
        self._client = None

    def validate_credentials(self) -> bool:
        """
        Validate AWS credentials.

        Returns:
            True if credentials are valid

        Raises:
            CredentialsError: If credentials are invalid or missing
        """
        try:
            import boto3
            from botocore.exceptions import ClientError, NoCredentialsError

            # Check for credentials in config or environment
            access_key = self.config.credentials.get("access_key_id") or \
                os.environ.get("AWS_ACCESS_KEY_ID")
            secret_key = self.config.credentials.get("secret_access_key") or \
                os.environ.get("AWS_SECRET_ACCESS_KEY")

            if access_key and secret_key:
                session = boto3.Session(
                    aws_access_key_id=access_key,
                    aws_secret_access_key=secret_key,
                    region_name=self.config.region
                )
            else:
                # Use default credential chain
                session = boto3.Session(region_name=self.config.region)

            # Test credentials by making a simple API call
            sts = session.client("sts")
            sts.get_caller_identity()

            self._client = session
            logger.info("AWS credentials validated successfully")
            return True

        except ImportError:
            raise CredentialsError(
                "boto3 library not installed. Install with: pip install boto3"
            )
        except NoCredentialsError:
            raise CredentialsError(
                "No AWS credentials found. Set AWS_ACCESS_KEY_ID and "
                "AWS_SECRET_ACCESS_KEY environment variables or configure "
                "AWS credentials file."
            )
        except ClientError as e:
            raise CredentialsError(f"AWS credential validation failed: {e}")

    def get_terraform_backend_config(self) -> Dict[str, str]:
        """
        Get Terraform S3 backend configuration.

        Returns:
            Backend configuration for S3
        """
        bucket = self.config.credentials.get(
            "backend_bucket",
            f"terraform-state-{self.config.credentials.get('account_id', 'default')}"
        )
        key = self.config.credentials.get("backend_key", "terraform.tfstate")
        dynamodb_table = self.config.credentials.get(
            "backend_dynamodb_table",
            "terraform-state-lock"
        )

        backend_config = {
            "bucket": bucket,
            "key": key,
            "region": self.config.region,
            "encrypt": "true",
            "dynamodb_table": dynamodb_table,
        }

        # Add optional configurations
        if "backend_kms_key_id" in self.config.credentials:
            backend_config["kms_key_id"] = \
                self.config.credentials["backend_kms_key_id"]

        return backend_config

    def get_terraform_provider_block(self) -> str:
        """
        Generate Terraform AWS provider block.

        Returns:
            Terraform provider configuration
        """
        provider_block = f"""
terraform {{
  required_providers {{
    aws = {{
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }}
  }}
  backend "s3" {{}}
}}

provider "aws" {{
  region = "{self.config.region}"
"""

        # Add optional profile
        if "profile" in self.config.credentials:
            provider_block += f'  profile = "{self.config.credentials["profile"]}"\n'

        # Add default tags
        if self.config.tags:
            provider_block += "  default_tags {\n    tags = {\n"
            for key, value in self.config.tags.items():
                provider_block += f'      {key} = "{value}"\n'
            provider_block += "    }\n  }\n"

        provider_block += "}\n"

        return provider_block

    def list_regions(self) -> List[str]:
        """
        List available AWS regions.

        Returns:
            List of AWS region names
        """
        try:
            import boto3

            ec2 = self._client.client("ec2") if self._client else \
                boto3.client("ec2", region_name=self.config.region)

            response = ec2.describe_regions()
            regions = [region["RegionName"] for region in response["Regions"]]

            logger.info(f"Found {len(regions)} AWS regions")
            return sorted(regions)

        except Exception as e:
            logger.error(f"Failed to list AWS regions: {e}")
            # Return common regions as fallback
            return [
                "us-east-1", "us-east-2", "us-west-1", "us-west-2",
                "eu-west-1", "eu-central-1", "ap-southeast-1", "ap-northeast-1"
            ]


class AzureProvider(CloudProvider):
    """
    Azure cloud provider implementation.

    Handles Azure-specific configuration, credentials, and Terraform integration.
    """

    def validate_credentials(self) -> bool:
        """
        Validate Azure credentials.

        Returns:
            True if credentials are valid

        Raises:
            CredentialsError: If credentials are invalid or missing
        """
        try:
            from azure.identity import DefaultAzureCredential
            from azure.mgmt.resource import ResourceManagementClient

            # Check for credentials in config or environment
            subscription_id = self.config.credentials.get("subscription_id") or \
                os.environ.get("AZURE_SUBSCRIPTION_ID")

            if not subscription_id:
                raise CredentialsError(
                    "Azure subscription ID not found. Set AZURE_SUBSCRIPTION_ID "
                    "environment variable or provide in configuration."
                )

            # Use DefaultAzureCredential which supports multiple auth methods
            credential = DefaultAzureCredential()

            # Test credentials
            client = ResourceManagementClient(credential, subscription_id)
            list(client.resource_groups.list())

            logger.info("Azure credentials validated successfully")
            return True

        except ImportError:
            raise CredentialsError(
                "Azure SDK not installed. Install with: "
                "pip install azure-identity azure-mgmt-resource"
            )
        except Exception as e:
            raise CredentialsError(f"Azure credential validation failed: {e}")

    def get_terraform_backend_config(self) -> Dict[str, str]:
        """
        Get Terraform Azure Storage backend configuration.

        Returns:
            Backend configuration for Azure Storage
        """
        backend_config = {
            "storage_account_name": self.config.credentials.get(
                "backend_storage_account",
                "tfstate"
            ),
            "container_name": self.config.credentials.get(
                "backend_container",
                "terraform-state"
            ),
            "key": self.config.credentials.get(
                "backend_key",
                "terraform.tfstate"
            ),
        }

        # Add optional configurations
        if "backend_resource_group" in self.config.credentials:
            backend_config["resource_group_name"] = \
                self.config.credentials["backend_resource_group"]

        if "backend_access_key" in self.config.credentials:
            backend_config["access_key"] = \
                self.config.credentials["backend_access_key"]

        return backend_config

    def get_terraform_provider_block(self) -> str:
        """
        Generate Terraform Azure provider block.

        Returns:
            Terraform provider configuration
        """
        subscription_id = self.config.credentials.get("subscription_id") or \
            os.environ.get("AZURE_SUBSCRIPTION_ID", "YOUR_SUBSCRIPTION_ID")

        provider_block = f"""
terraform {{
  required_providers {{
    azurerm = {{
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }}
  }}
  backend "azurerm" {{}}
}}

provider "azurerm" {{
  features {{}}
  subscription_id = "{subscription_id}"
}}
"""

        return provider_block

    def list_regions(self) -> List[str]:
        """
        List available Azure regions.

        Returns:
            List of Azure region names
        """
        try:
            from azure.identity import DefaultAzureCredential
            from azure.mgmt.resource import SubscriptionClient

            credential = DefaultAzureCredential()
            subscription_id = self.config.credentials.get("subscription_id") or \
                os.environ.get("AZURE_SUBSCRIPTION_ID")

            client = SubscriptionClient(credential)
            locations = client.subscriptions.list_locations(subscription_id)

            regions = [loc.name for loc in locations]
            logger.info(f"Found {len(regions)} Azure regions")
            return sorted(regions)

        except Exception as e:
            logger.error(f"Failed to list Azure regions: {e}")
            # Return common regions as fallback
            return [
                "eastus", "eastus2", "westus", "westus2", "centralus",
                "northeurope", "westeurope", "southeastasia", "eastasia"
            ]


class GCPProvider(CloudProvider):
    """
    Google Cloud Platform provider implementation.

    Handles GCP-specific configuration, credentials, and Terraform integration.
    """

    def validate_credentials(self) -> bool:
        """
        Validate GCP credentials.

        Returns:
            True if credentials are valid

        Raises:
            CredentialsError: If credentials are invalid or missing
        """
        try:
            from google.cloud import storage
            from google.auth import default
            from google.auth.exceptions import DefaultCredentialsError

            # Check for credentials
            project_id = self.config.credentials.get("project_id") or \
                os.environ.get("GOOGLE_CLOUD_PROJECT")

            credentials_file = self.config.credentials.get("credentials_file") or \
                os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")

            if credentials_file and not Path(credentials_file).exists():
                raise CredentialsError(
                    f"GCP credentials file not found: {credentials_file}"
                )

            # Test credentials
            credentials, project = default()

            if not project_id:
                project_id = project

            if not project_id:
                raise CredentialsError(
                    "GCP project ID not found. Set GOOGLE_CLOUD_PROJECT "
                    "environment variable or provide in configuration."
                )

            # Test API access
            client = storage.Client(credentials=credentials, project=project_id)
            list(client.list_buckets(max_results=1))

            logger.info("GCP credentials validated successfully")
            return True

        except ImportError:
            raise CredentialsError(
                "Google Cloud SDK not installed. Install with: "
                "pip install google-cloud-storage"
            )
        except DefaultCredentialsError:
            raise CredentialsError(
                "No GCP credentials found. Set GOOGLE_APPLICATION_CREDENTIALS "
                "environment variable or run 'gcloud auth application-default login'"
            )
        except Exception as e:
            raise CredentialsError(f"GCP credential validation failed: {e}")

    def get_terraform_backend_config(self) -> Dict[str, str]:
        """
        Get Terraform GCS backend configuration.

        Returns:
            Backend configuration for Google Cloud Storage
        """
        backend_config = {
            "bucket": self.config.credentials.get(
                "backend_bucket",
                "terraform-state"
            ),
            "prefix": self.config.credentials.get(
                "backend_prefix",
                "terraform/state"
            ),
        }

        return backend_config

    def get_terraform_provider_block(self) -> str:
        """
        Generate Terraform GCP provider block.

        Returns:
            Terraform provider configuration
        """
        project_id = self.config.credentials.get("project_id") or \
            os.environ.get("GOOGLE_CLOUD_PROJECT", "YOUR_PROJECT_ID")

        provider_block = f"""
terraform {{
  required_providers {{
    google = {{
      source  = "hashicorp/google"
      version = "~> 5.0"
    }}
  }}
  backend "gcs" {{}}
}}

provider "google" {{
  project = "{project_id}"
  region  = "{self.config.region}"
}}
"""

        return provider_block

    def list_regions(self) -> List[str]:
        """
        List available GCP regions.

        Returns:
            List of GCP region names
        """
        try:
            from google.cloud import compute_v1

            project_id = self.config.credentials.get("project_id") or \
                os.environ.get("GOOGLE_CLOUD_PROJECT")

            client = compute_v1.RegionsClient()
            request = compute_v1.ListRegionsRequest(project=project_id)

            regions = [region.name for region in client.list(request=request)]
            logger.info(f"Found {len(regions)} GCP regions")
            return sorted(regions)

        except Exception as e:
            logger.error(f"Failed to list GCP regions: {e}")
            # Return common regions as fallback
            return [
                "us-central1", "us-east1", "us-west1", "us-west2",
                "europe-west1", "europe-west2", "asia-east1", "asia-southeast1"
            ]


class ProviderFactory:
    """Factory class for creating cloud provider instances."""

    _providers = {
        "aws": AWSProvider,
        "azure": AzureProvider,
        "gcp": GCPProvider,
    }

    @classmethod
    def create_provider(cls, config: ProviderConfig) -> CloudProvider:
        """
        Create a cloud provider instance.

        Args:
            config: Provider configuration

        Returns:
            CloudProvider instance

        Raises:
            CloudProviderError: If provider is not supported
        """
        provider_name = config.name.lower()

        if provider_name not in cls._providers:
            raise CloudProviderError(
                f"Unsupported provider: {config.name}. "
                f"Supported providers: {', '.join(cls._providers.keys())}"
            )

        provider_class = cls._providers[provider_name]
        return provider_class(config)

    @classmethod
    def supported_providers(cls) -> List[str]:
        """
        Get list of supported provider names.

        Returns:
            List of provider names
        """
        return list(cls._providers.keys())
