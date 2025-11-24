"""
Cloud Infrastructure Security Scanner.

Comprehensive cloud security scanner supporting AWS, Azure, and GCP with
multi-service vulnerability detection, misconfiguration analysis, IAM policy
auditing, and network security validation. Provides detailed security findings
with remediation guidance for cloud infrastructure hardening.
"""

import json
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, validator

# AWS SDK
try:
    import boto3
    from botocore.exceptions import (
        ClientError,
        NoCredentialsError,
        PartialCredentialsError,
    )

    AWS_AVAILABLE = True
except ImportError:
    AWS_AVAILABLE = False

# Azure SDK
try:
    from azure.core.exceptions import (
        AzureError,
        ClientAuthenticationError,
    )
    from azure.identity import DefaultAzureCredential
    from azure.mgmt.compute import ComputeManagementClient
    from azure.mgmt.network import NetworkManagementClient
    from azure.mgmt.resource import SubscriptionClient
    from azure.mgmt.storage import StorageManagementClient

    AZURE_AVAILABLE = True
except ImportError:
    AZURE_AVAILABLE = False

# GCP SDK
try:
    from google.api_core.exceptions import GoogleAPIError
    from google.cloud import compute_v1, iam, resource_manager, storage

    GCP_AVAILABLE = True
except ImportError:
    GCP_AVAILABLE = False


# Configure logging
logger = logging.getLogger(__name__)


# Custom Exceptions
class CloudScanError(Exception):
    """Base exception for cloud scanning errors."""

    pass


class CredentialsError(CloudScanError):
    """Exception raised for credential validation failures."""

    pass


class ServiceUnavailableError(CloudScanError):
    """Exception raised when cloud service is unavailable."""

    pass


class PermissionDeniedError(CloudScanError):
    """Exception raised when API permissions are insufficient."""

    pass


# Enumerations
class CloudProvider(str, Enum):
    """Supported cloud providers."""

    AWS = "aws"
    AZURE = "azure"
    GCP = "gcp"
    MULTI = "multi"


class ServiceType(str, Enum):
    """Cloud service types for scanning."""

    # AWS Services
    S3 = "s3"
    EC2 = "ec2"
    IAM = "iam"
    RDS = "rds"
    VPC = "vpc"
    LAMBDA = "lambda"
    SECURITY_GROUPS = "security_groups"

    # Azure Services
    STORAGE = "storage"
    VMS = "vms"
    KEY_VAULT = "key_vault"
    NSG = "nsg"

    # GCP Services
    CLOUD_STORAGE = "cloud_storage"
    COMPUTE = "compute"
    GCP_IAM = "gcp_iam"
    GCP_VPC = "gcp_vpc"

    # Generic
    NETWORK = "network"


class SeverityLevel(str, Enum):
    """Security finding severity levels."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


# Pydantic Models
class AWSCredentials(BaseModel):
    """AWS authentication credentials."""

    access_key_id: Optional[str] = Field(None, description="AWS access key ID")
    secret_access_key: Optional[str] = Field(
        None, description="AWS secret access key"
    )  # noqa: E501
    session_token: Optional[str] = Field(
        None, description="AWS session token for temporary credentials"
    )
    profile: Optional[str] = Field(
        "default", description="AWS CLI profile name"
    )  # noqa: E501

    class Config:
        """Pydantic configuration."""

        frozen = False


class AzureCredentials(BaseModel):
    """Azure authentication credentials."""

    tenant_id: Optional[str] = Field(None, description="Azure tenant ID")
    client_id: Optional[str] = Field(None, description="Azure client ID")
    client_secret: Optional[str] = Field(
        None, description="Azure client secret"
    )  # noqa: E501
    subscription_id: str = Field(..., description="Azure subscription ID")

    class Config:
        """Pydantic configuration."""

        frozen = False


class GCPCredentials(BaseModel):
    """GCP authentication credentials."""

    project_id: str = Field(..., description="GCP project ID")
    credentials_file: Optional[Path] = Field(
        None, description="Path to service account key file"
    )
    service_account_key: Optional[Dict[str, Any]] = Field(
        None, description="Service account key JSON"
    )

    class Config:
        """Pydantic configuration."""

        frozen = False


class CloudConfig(BaseModel):
    """Cloud scanner configuration."""

    provider: CloudProvider = Field(..., description="Cloud provider to scan")
    profile: Optional[str] = Field(None, description="Cloud profile name")
    region: Optional[str] = Field(None, description="Cloud region to scan")
    services: List[ServiceType] = Field(
        default_factory=list, description="Services to scan"
    )
    frameworks: List[str] = Field(
        default_factory=list,
        description="Compliance frameworks to validate against",
    )
    aws_credentials: Optional[AWSCredentials] = Field(
        None, description="AWS credentials"
    )
    azure_credentials: Optional[AzureCredentials] = Field(
        None, description="Azure credentials"
    )
    gcp_credentials: Optional[GCPCredentials] = Field(
        None, description="GCP credentials"
    )
    scan_timeout: int = Field(
        300, description="Timeout for scan operations in seconds"
    )  # noqa: E501
    max_resources_per_service: int = Field(
        1000, description="Maximum resources to scan per service"
    )

    @validator("services", pre=True)
    def validate_services(cls, v: Any) -> List[ServiceType]:
        """Validate service types."""
        if not v:
            return []
        if isinstance(v, str):
            v = [v]
        return [ServiceType(s) if isinstance(s, str) else s for s in v]

    class Config:
        """Pydantic configuration."""

        frozen = False


class CloudFinding(BaseModel):
    """Cloud security finding."""

    service: ServiceType = Field(..., description="Cloud service type")
    resource_id: str = Field(..., description="Resource identifier")
    resource_type: str = Field(..., description="Resource type")
    title: str = Field(..., description="Finding title")
    severity: SeverityLevel = Field(..., description="Finding severity")
    description: str = Field(..., description="Finding description")
    risk: str = Field(..., description="Security risk explanation")
    remediation: str = Field(..., description="Remediation guidance")
    tags: Dict[str, str] = Field(
        default_factory=dict, description="Resource tags"
    )  # noqa: E501
    region: Optional[str] = Field(None, description="Cloud region")
    account_id: Optional[str] = Field(None, description="Account/Project ID")
    compliance_frameworks: List[str] = Field(
        default_factory=list, description="Related compliance frameworks"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )

    class Config:
        """Pydantic configuration."""

        frozen = False


class CloudResult(BaseModel):
    """Cloud scan results."""

    findings: List[CloudFinding] = Field(
        default_factory=list, description="Security findings"
    )
    total_resources: int = Field(0, description="Total resources scanned")
    total_findings: int = Field(0, description="Total findings count")
    critical_count: int = Field(0, description="Critical findings count")
    high_count: int = Field(0, description="High findings count")
    medium_count: int = Field(0, description="Medium findings count")
    low_count: int = Field(0, description="Low findings count")
    service_results: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict, description="Per-service results"
    )
    scan_time: float = Field(0.0, description="Scan duration in seconds")
    timestamp: datetime = Field(
        default_factory=datetime.now, description="Scan timestamp"
    )
    provider: CloudProvider = Field(..., description="Cloud provider")
    region: Optional[str] = Field(None, description="Scanned region")

    class Config:
        """Pydantic configuration."""

        frozen = False


@dataclass
class CloudScanner:
    """
    Cloud Infrastructure Security Scanner.

    Comprehensive security scanner for AWS, Azure, and GCP infrastructure
    with misconfiguration detection, IAM analysis, and network security
    validation.
    """

    config: CloudConfig
    _aws_session: Optional[Any] = field(default=None, init=False)
    _azure_credential: Optional[Any] = field(default=None, init=False)
    _gcp_clients: Dict[str, Any] = field(default_factory=dict, init=False)

    def __post_init__(self) -> None:
        """Initialize cloud scanner and validate configuration."""
        logger.info(
            f"Initializing CloudScanner for provider: "
            f"{self.config.provider}"  # noqa: E501
        )

        # Validate provider availability
        if self.config.provider == CloudProvider.AWS and not AWS_AVAILABLE:
            raise CloudScanError("AWS SDK (boto3) not available")
        if self.config.provider == CloudProvider.AZURE and not AZURE_AVAILABLE:
            raise CloudScanError("Azure SDK not available")
        if self.config.provider == CloudProvider.GCP and not GCP_AVAILABLE:
            raise CloudScanError("GCP SDK not available")

        # Initialize clients
        self._initialize_clients()

    def _initialize_clients(self) -> None:
        """Initialize cloud provider clients."""
        try:
            if self.config.provider in (
                CloudProvider.AWS,
                CloudProvider.MULTI,
            ):
                self._initialize_aws_client()

            if self.config.provider in (
                CloudProvider.AZURE,
                CloudProvider.MULTI,
            ):
                self._initialize_azure_client()

            if self.config.provider in (
                CloudProvider.GCP,
                CloudProvider.MULTI,
            ):
                self._initialize_gcp_client()

        except Exception as e:
            raise CloudScanError(f"Failed to initialize clients: {e}") from e

    def _initialize_aws_client(self) -> None:
        """Initialize AWS client session."""
        if not AWS_AVAILABLE:
            logger.warning("AWS SDK not available, skipping initialization")
            return

        try:
            creds = self.config.aws_credentials
            if creds and creds.access_key_id and creds.secret_access_key:
                self._aws_session = boto3.Session(
                    aws_access_key_id=creds.access_key_id,
                    aws_secret_access_key=creds.secret_access_key,
                    aws_session_token=creds.session_token,
                    region_name=self.config.region or "us-east-1",
                )
            elif creds and creds.profile:
                self._aws_session = boto3.Session(
                    profile_name=creds.profile,
                    region_name=self.config.region or "us-east-1",
                )
            else:
                self._aws_session = boto3.Session(
                    region_name=self.config.region or "us-east-1"
                )

            # Validate credentials
            sts = self._aws_session.client("sts")
            sts.get_caller_identity()
            logger.info("AWS client initialized successfully")

        except (NoCredentialsError, PartialCredentialsError) as e:
            raise CredentialsError(f"Invalid AWS credentials: {e}") from e
        except ClientError as e:
            raise CredentialsError(f"AWS authentication failed: {e}") from e

    def _initialize_azure_client(self) -> None:
        """Initialize Azure client credential."""
        if not AZURE_AVAILABLE:
            logger.warning("Azure SDK not available, skipping initialization")
            return

        try:
            creds = self.config.azure_credentials
            if (
                creds and creds.tenant_id and creds.client_id and creds.client_secret  # noqa: E501
            ):  # noqa: E501
                from azure.identity import ClientSecretCredential

                self._azure_credential = ClientSecretCredential(
                    tenant_id=creds.tenant_id,
                    client_id=creds.client_id,
                    client_secret=creds.client_secret,
                )
            else:
                self._azure_credential = DefaultAzureCredential()

            # Validate credentials
            if creds:
                subscription_client = SubscriptionClient(
                    self._azure_credential
                )  # noqa: E501
                list(subscription_client.subscriptions.list())
            logger.info("Azure client initialized successfully")

        except ClientAuthenticationError as e:
            raise CredentialsError(f"Invalid Azure credentials: {e}") from e
        except AzureError as e:
            raise CredentialsError(f"Azure authentication failed: {e}") from e

    def _initialize_gcp_client(self) -> None:
        """Initialize GCP client."""
        if not GCP_AVAILABLE:
            logger.warning("GCP SDK not available, skipping initialization")
            return

        try:
            creds = self.config.gcp_credentials
            if not creds:
                raise CredentialsError("GCP credentials not provided")

            # Set credentials file if provided
            if creds.credentials_file:
                import os

                os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(
                    creds.credentials_file
                )

            # Initialize clients
            self._gcp_clients["storage"] = storage.Client(
                project=creds.project_id
            )  # noqa: E501
            self._gcp_clients["compute"] = compute_v1.InstancesClient()
            self._gcp_clients["iam"] = iam.IAMClient()
            self._gcp_clients["resource_manager"] = (
                resource_manager.ProjectsClient()
            )  # noqa: E501

            logger.info("GCP client initialized successfully")

        except GoogleAPIError as e:
            raise CredentialsError(f"GCP authentication failed: {e}") from e

    def _validate_credentials(self, provider: CloudProvider) -> bool:
        """
        Validate cloud provider credentials.

        Args:
            provider: Cloud provider to validate

        Returns:
            True if credentials are valid

        Raises:
            CredentialsError: If credentials are invalid
        """
        try:
            if provider == CloudProvider.AWS:
                if not self._aws_session:
                    raise CredentialsError("AWS session not initialized")
                sts = self._aws_session.client("sts")
                sts.get_caller_identity()
                return True

            elif provider == CloudProvider.AZURE:
                if not self._azure_credential:
                    raise CredentialsError("Azure credential not initialized")
                if self.config.azure_credentials:
                    subscription_client = SubscriptionClient(
                        self._azure_credential
                    )  # noqa: E501
                    list(subscription_client.subscriptions.list())
                return True

            elif provider == CloudProvider.GCP:
                if not self._gcp_clients:
                    raise CredentialsError("GCP clients not initialized")
                # Test connection
                storage_client = self._gcp_clients.get("storage")
                if storage_client:
                    list(storage_client.list_buckets(max_results=1))
                return True

        except Exception as e:
            raise CredentialsError(
                f"Credential validation failed for {provider}: {e}"
            ) from e

        return False

    def scan_aws(
        self, services: Optional[List[ServiceType]] = None
    ) -> CloudResult:  # noqa: E501
        """
        Scan AWS infrastructure for security issues.

        Args:
            services: List of AWS services to scan

        Returns:
            CloudResult with findings

        Raises:
            CloudScanError: If scan fails
        """
        if not AWS_AVAILABLE:
            raise CloudScanError("AWS SDK not available")

        logger.info("Starting AWS security scan")
        start_time = time.time()

        # Validate credentials
        self._validate_credentials(CloudProvider.AWS)

        # Determine services to scan
        scan_services = (
            services
            or self.config.services
            or [
                ServiceType.S3,
                ServiceType.EC2,
                ServiceType.IAM,
                ServiceType.SECURITY_GROUPS,
            ]
        )

        all_findings: List[CloudFinding] = []
        service_results: Dict[str, Dict[str, Any]] = {}
        total_resources = 0

        # Scan each service
        for service in scan_services:
            try:
                logger.info(f"Scanning AWS service: {service}")
                findings: List[CloudFinding] = []

                if service == ServiceType.S3:
                    findings = self._scan_aws_s3()
                elif service == ServiceType.EC2:
                    findings = self._scan_aws_ec2()
                elif service == ServiceType.IAM:
                    findings = self._scan_aws_iam()
                elif service == ServiceType.SECURITY_GROUPS:
                    findings = self._scan_aws_security_groups()
                elif service == ServiceType.RDS:
                    findings = self._scan_aws_rds()
                elif service == ServiceType.VPC:
                    findings = self._scan_aws_vpc()
                elif service == ServiceType.LAMBDA:
                    findings = self._scan_aws_lambda()

                all_findings.extend(findings)
                service_results[service.value] = {
                    "findings_count": len(findings),
                    "resources_scanned": sum(
                        1 for f in findings if f.resource_id
                    ),  # noqa: E501
                }
                total_resources += service_results[service.value][
                    "resources_scanned"
                ]  # noqa: E501

            except Exception as e:
                logger.error(f"Error scanning {service}: {e}")
                service_results[service.value] = {"error": str(e)}

        # Calculate severity counts
        severity_counts = self._calculate_severity_counts(all_findings)

        scan_time = time.time() - start_time

        return CloudResult(
            findings=all_findings,
            total_resources=total_resources,
            total_findings=len(all_findings),
            critical_count=severity_counts[SeverityLevel.CRITICAL],
            high_count=severity_counts[SeverityLevel.HIGH],
            medium_count=severity_counts[SeverityLevel.MEDIUM],
            low_count=severity_counts[SeverityLevel.LOW],
            service_results=service_results,
            scan_time=scan_time,
            provider=CloudProvider.AWS,
            region=self.config.region,
        )

    def _scan_aws_s3(self) -> List[CloudFinding]:
        """Audit AWS S3 buckets for security issues."""
        findings: List[CloudFinding] = []

        try:
            s3_client = self._aws_session.client("s3")  # type: ignore
            response = s3_client.list_buckets()

            for bucket in response.get("Buckets", []):
                bucket_name = bucket["Name"]

                # Check public access
                public_finding = self._check_public_s3_bucket(
                    bucket_name, s3_client
                )  # noqa: E501
                if public_finding:
                    findings.append(public_finding)

                # Check encryption
                encryption_finding = self._check_s3_encryption(
                    bucket_name, s3_client
                )  # noqa: E501
                if encryption_finding:
                    findings.append(encryption_finding)

                # Check versioning
                versioning_finding = self._check_s3_versioning(
                    bucket_name, s3_client
                )  # noqa: E501
                if versioning_finding:
                    findings.append(versioning_finding)

                # Check logging
                logging_finding = self._check_s3_logging(
                    bucket_name, s3_client
                )  # noqa: E501
                if logging_finding:
                    findings.append(logging_finding)

        except ClientError as e:
            logger.error(f"Error scanning S3: {e}")
            raise ServiceUnavailableError(f"S3 scan failed: {e}") from e

        return findings

    def _check_public_s3_bucket(
        self, bucket_name: str, s3_client: Any
    ) -> Optional[CloudFinding]:
        """Check if S3 bucket allows public access."""
        try:
            # Check bucket ACL
            acl = s3_client.get_bucket_acl(Bucket=bucket_name)
            for grant in acl.get("Grants", []):
                grantee = grant.get("Grantee", {})
                if grantee.get("Type") == "Group" and grantee.get("URI") in [
                    "http://acs.amazonaws.com/groups/global/AllUsers",
                    "http://acs.amazonaws.com/groups/global/AuthenticatedUsers",  # noqa: E501
                ]:
                    return CloudFinding(
                        service=ServiceType.S3,
                        resource_id=bucket_name,
                        resource_type="S3 Bucket",
                        title="Public S3 Bucket",
                        severity=SeverityLevel.CRITICAL,
                        description=f"Bucket '{bucket_name}' allows public access via ACL",  # noqa: E501
                        risk="Sensitive data may be exposed to unauthorized users",  # noqa: E501
                        remediation="Remove public access grants from bucket ACL and enable Block Public Access",  # noqa: E501
                        compliance_frameworks=[
                            "CIS AWS",
                            "NIST 800-53",
                            "PCI DSS",
                        ],
                    )

            # Check bucket policy
            try:
                policy = s3_client.get_bucket_policy(Bucket=bucket_name)
                policy_doc = json.loads(policy["Policy"])
                for statement in policy_doc.get("Statement", []):
                    principal = statement.get("Principal", {})
                    if principal == "*" or principal.get("AWS") == "*":
                        return CloudFinding(
                            service=ServiceType.S3,
                            resource_id=bucket_name,
                            resource_type="S3 Bucket",
                            title="Public S3 Bucket Policy",
                            severity=SeverityLevel.CRITICAL,
                            description=f"Bucket '{bucket_name}' has public policy",  # noqa: E501
                            risk="Bucket contents accessible to anonymous users",  # noqa: E501
                            remediation="Restrict bucket policy to specific principals and enable Block Public Access",  # noqa: E501
                            compliance_frameworks=[
                                "CIS AWS",
                                "NIST 800-53",
                            ],
                        )
            except ClientError as e:
                if e.response["Error"]["Code"] != "NoSuchBucketPolicy":
                    logger.debug(f"Error checking bucket policy: {e}")

        except ClientError as e:
            logger.debug(
                f"Error checking public access for {bucket_name}: {e}"
            )  # noqa: E501

        return None

    def _check_s3_encryption(
        self, bucket_name: str, s3_client: Any
    ) -> Optional[CloudFinding]:
        """Check if S3 bucket has encryption enabled."""
        try:
            s3_client.get_bucket_encryption(Bucket=bucket_name)
        except ClientError as e:
            if (
                e.response["Error"]["Code"]
                == "ServerSideEncryptionConfigurationNotFoundError"
            ):
                return CloudFinding(
                    service=ServiceType.S3,
                    resource_id=bucket_name,
                    resource_type="S3 Bucket",
                    title="S3 Bucket Encryption Disabled",
                    severity=SeverityLevel.HIGH,
                    description=f"Bucket '{bucket_name}' does not have default encryption enabled",  # noqa: E501
                    risk="Data stored in bucket is not encrypted at rest",
                    remediation="Enable default encryption using AES-256 or AWS KMS",  # noqa: E501
                    compliance_frameworks=[
                        "CIS AWS",
                        "HIPAA",
                        "PCI DSS",
                    ],
                )
        return None

    def _check_s3_versioning(
        self, bucket_name: str, s3_client: Any
    ) -> Optional[CloudFinding]:
        """Check if S3 bucket has versioning enabled."""
        try:
            response = s3_client.get_bucket_versioning(Bucket=bucket_name)
            if response.get("Status") != "Enabled":
                return CloudFinding(
                    service=ServiceType.S3,
                    resource_id=bucket_name,
                    resource_type="S3 Bucket",
                    title="S3 Bucket Versioning Disabled",
                    severity=SeverityLevel.MEDIUM,
                    description=f"Bucket '{bucket_name}' does not have versioning enabled",  # noqa: E501
                    risk=(
                        "Cannot recover from accidental deletion or " "modification"  # noqa: E501
                    ),  # noqa: E501
                    remediation="Enable versioning to protect against data loss",  # noqa: E501
                    compliance_frameworks=["CIS AWS"],
                )
        except ClientError as e:
            logger.debug(f"Error checking versioning for {bucket_name}: {e}")

        return None

    def _check_s3_logging(
        self, bucket_name: str, s3_client: Any
    ) -> Optional[CloudFinding]:
        """Check if S3 bucket has access logging enabled."""
        try:
            response = s3_client.get_bucket_logging(Bucket=bucket_name)
            if "LoggingEnabled" not in response:
                return CloudFinding(
                    service=ServiceType.S3,
                    resource_id=bucket_name,
                    resource_type="S3 Bucket",
                    title="S3 Bucket Logging Disabled",
                    severity=SeverityLevel.LOW,
                    description=f"Bucket '{bucket_name}' does not have access logging enabled",  # noqa: E501
                    risk="Cannot audit or track bucket access",
                    remediation="Enable server access logging to track requests",  # noqa: E501
                    compliance_frameworks=["CIS AWS", "NIST 800-53"],
                )
        except ClientError as e:
            logger.debug(f"Error checking logging for {bucket_name}: {e}")

        return None

    def _scan_aws_ec2(self) -> List[CloudFinding]:
        """Audit AWS EC2 instances for security issues."""
        findings: List[CloudFinding] = []

        try:
            ec2_client = self._aws_session.client("ec2")  # type: ignore
            response = ec2_client.describe_instances()

            for reservation in response.get("Reservations", []):
                for instance in reservation.get("Instances", []):
                    instance_id = instance["InstanceId"]

                    # Check public IP
                    if instance.get("PublicIpAddress"):
                        findings.append(
                            CloudFinding(
                                service=ServiceType.EC2,
                                resource_id=instance_id,
                                resource_type="EC2 Instance",
                                title="EC2 Instance with Public IP",
                                severity=SeverityLevel.MEDIUM,
                                description=f"Instance '{instance_id}' has public IP address",  # noqa: E501
                                risk="Instance directly accessible from internet",  # noqa: E501
                                remediation="Place instance in private subnet behind load balancer or NAT gateway",  # noqa: E501
                                compliance_frameworks=["CIS AWS"],
                            )
                        )

                    # Check IMDSv2
                    metadata_options = instance.get("MetadataOptions", {})
                    if metadata_options.get("HttpTokens") != "required":
                        findings.append(
                            CloudFinding(
                                service=ServiceType.EC2,
                                resource_id=instance_id,
                                resource_type="EC2 Instance",
                                title="IMDSv2 Not Enforced",
                                severity=SeverityLevel.HIGH,
                                description=f"Instance '{instance_id}' not enforcing IMDSv2",  # noqa: E501
                                risk=(
                                    "Vulnerable to SSRF attacks accessing "
                                    "metadata"  # noqa: E501
                                ),
                                remediation=(
                                    "Enable IMDSv2 by requiring tokens"
                                ),  # noqa: E501
                                compliance_frameworks=["CIS AWS"],
                            )
                        )

                    # Check monitoring
                    if (
                        not instance.get("Monitoring", {}).get("State") == "enabled"  # noqa: E501
                    ):  # noqa: E501
                        findings.append(
                            CloudFinding(
                                service=ServiceType.EC2,
                                resource_id=instance_id,
                                resource_type="EC2 Instance",
                                title="EC2 Detailed Monitoring Disabled",
                                severity=SeverityLevel.LOW,
                                description=f"Instance '{instance_id}' does not have detailed monitoring",  # noqa: E501
                                risk="Limited visibility into instance metrics",  # noqa: E501
                                remediation=(
                                    "Enable detailed monitoring for better "
                                    "observability"
                                ),
                                compliance_frameworks=["CIS AWS"],
                            )
                        )

        except ClientError as e:
            logger.error(f"Error scanning EC2: {e}")
            raise ServiceUnavailableError(f"EC2 scan failed: {e}") from e

        return findings

    def _scan_aws_iam(self) -> List[CloudFinding]:
        """Audit AWS IAM policies and users."""
        findings: List[CloudFinding] = []

        try:
            iam_client = self._aws_session.client("iam")  # type: ignore

            # Check for root account usage
            credential_report = iam_client.generate_credential_report()
            if credential_report["State"] == "COMPLETE":
                report = iam_client.get_credential_report()
                report_content = report["Content"].decode("utf-8")

                for line in report_content.split("\n")[1:]:
                    if line.startswith("<root_account>"):
                        parts = line.split(",")
                        if len(parts) > 4 and parts[4] != "N/A":
                            findings.append(
                                CloudFinding(
                                    service=ServiceType.IAM,
                                    resource_id="root",
                                    resource_type="IAM User",
                                    title="Root Account Access Keys",
                                    severity=SeverityLevel.CRITICAL,
                                    description="Root account has active access keys",  # noqa: E501
                                    risk="Compromise of root credentials allows full account access",  # noqa: E501
                                    remediation="Delete root access keys and use IAM users with MFA",  # noqa: E501
                                    compliance_frameworks=[
                                        "CIS AWS",
                                        "NIST 800-53",
                                    ],
                                )
                            )

            # Check users without MFA
            users = iam_client.list_users()
            for user in users.get("Users", []):
                user_name = user["UserName"]
                mfa_devices = iam_client.list_mfa_devices(UserName=user_name)

                if not mfa_devices.get("MFADevices"):
                    findings.append(
                        CloudFinding(
                            service=ServiceType.IAM,
                            resource_id=user_name,
                            resource_type="IAM User",
                            title="IAM User Without MFA",
                            severity=SeverityLevel.HIGH,
                            description=f"User '{user_name}' does not have MFA enabled",  # noqa: E501
                            risk="Account vulnerable to credential compromise",
                            remediation="Enable MFA for all IAM users",
                            compliance_frameworks=["CIS AWS"],
                        )
                    )

            # Check overly permissive policies
            policies = iam_client.list_policies(Scope="Local")
            for policy in policies.get("Policies", []):
                policy_arn = policy["Arn"]
                policy_name = policy["PolicyName"]

                # Get policy document
                policy_version = iam_client.get_policy_version(
                    PolicyArn=policy_arn,
                    VersionId=policy["DefaultVersionId"],
                )

                policy_doc = policy_version["PolicyVersion"]["Document"]
                for statement in policy_doc.get("Statement", []):
                    if (
                        statement.get("Effect") == "Allow"
                        and statement.get("Action") == "*"
                        and statement.get("Resource") == "*"
                    ):
                        findings.append(
                            CloudFinding(
                                service=ServiceType.IAM,
                                resource_id=policy_arn,
                                resource_type="IAM Policy",
                                title="Overly Permissive IAM Policy",
                                severity=SeverityLevel.CRITICAL,
                                description=f"Policy '{policy_name}' grants full administrative access",  # noqa: E501
                                risk="Excessive permissions increase blast radius of compromise",  # noqa: E501
                                remediation="Apply principle of least privilege and restrict actions",  # noqa: E501
                                compliance_frameworks=[
                                    "CIS AWS",
                                    "NIST 800-53",
                                ],
                            )
                        )

        except ClientError as e:
            logger.error(f"Error scanning IAM: {e}")
            raise ServiceUnavailableError(f"IAM scan failed: {e}") from e

        return findings

    def _scan_aws_security_groups(self) -> List[CloudFinding]:
        """Audit AWS security groups for open access."""
        findings: List[CloudFinding] = []

        try:
            ec2_client = self._aws_session.client("ec2")  # type: ignore
            response = ec2_client.describe_security_groups()

            for sg in response.get("SecurityGroups", []):
                sg_id = sg["GroupId"]
                sg_name = sg["GroupName"]

                # Check inbound rules
                for rule in sg.get("IpPermissions", []):
                    for ip_range in rule.get("IpRanges", []):
                        if ip_range.get("CidrIp") == "0.0.0.0/0":
                            from_port = rule.get("FromPort", "All")
                            to_port = rule.get("ToPort", "All")

                            severity = SeverityLevel.CRITICAL
                            if from_port in [80, 443]:
                                severity = SeverityLevel.MEDIUM

                            findings.append(
                                CloudFinding(
                                    service=ServiceType.SECURITY_GROUPS,
                                    resource_id=sg_id,
                                    resource_type="Security Group",
                                    title="Security Group Allows Public Access",  # noqa: E501
                                    severity=severity,
                                    description=f"Security group '{sg_name}' allows inbound traffic from 0.0.0.0/0 on ports {from_port}-{to_port}",  # noqa: E501
                                    risk="Resources accessible from any internet address",  # noqa: E501
                                    remediation="Restrict access to specific IP addresses or ranges",  # noqa: E501
                                    compliance_frameworks=["CIS AWS"],
                                    metadata={
                                        "from_port": from_port,
                                        "to_port": to_port,
                                    },
                                )
                            )

        except ClientError as e:
            logger.error(f"Error scanning security groups: {e}")
            raise ServiceUnavailableError(
                f"Security group scan failed: {e}"
            ) from e  # noqa: E501

        return findings

    def _scan_aws_rds(self) -> List[CloudFinding]:
        """Audit AWS RDS instances for security issues."""
        findings: List[CloudFinding] = []

        try:
            rds_client = self._aws_session.client("rds")  # type: ignore
            response = rds_client.describe_db_instances()

            for instance in response.get("DBInstances", []):
                instance_id = instance["DBInstanceIdentifier"]

                # Check public access
                if instance.get("PubliclyAccessible"):
                    findings.append(
                        CloudFinding(
                            service=ServiceType.RDS,
                            resource_id=instance_id,
                            resource_type="RDS Instance",
                            title="Publicly Accessible RDS Instance",
                            severity=SeverityLevel.CRITICAL,
                            description=f"RDS instance '{instance_id}' is publicly accessible",  # noqa: E501
                            risk="Database exposed to internet attacks",
                            remediation="Disable public accessibility and use VPN or bastion host",  # noqa: E501
                            compliance_frameworks=["CIS AWS", "PCI DSS"],
                        )
                    )

                # Check encryption
                if not instance.get("StorageEncrypted"):
                    findings.append(
                        CloudFinding(
                            service=ServiceType.RDS,
                            resource_id=instance_id,
                            resource_type="RDS Instance",
                            title="RDS Storage Not Encrypted",
                            severity=SeverityLevel.HIGH,
                            description=f"RDS instance '{instance_id}' does not have storage encryption",  # noqa: E501
                            risk="Database contents vulnerable to physical theft",  # noqa: E501
                            remediation="Enable storage encryption using KMS keys",  # noqa: E501
                            compliance_frameworks=[
                                "CIS AWS",
                                "HIPAA",
                                "PCI DSS",
                            ],
                        )
                    )

                # Check backup retention
                if instance.get("BackupRetentionPeriod", 0) < 7:
                    findings.append(
                        CloudFinding(
                            service=ServiceType.RDS,
                            resource_id=instance_id,
                            resource_type="RDS Instance",
                            title="Insufficient RDS Backup Retention",
                            severity=SeverityLevel.MEDIUM,
                            description=f"RDS instance '{instance_id}' has backup retention less than 7 days",  # noqa: E501
                            risk="Limited recovery options for data loss",
                            remediation="Set backup retention period to at least 7 days",  # noqa: E501
                            compliance_frameworks=["CIS AWS"],
                        )
                    )

        except ClientError as e:
            logger.error(f"Error scanning RDS: {e}")
            raise ServiceUnavailableError(f"RDS scan failed: {e}") from e

        return findings

    def _scan_aws_vpc(self) -> List[CloudFinding]:
        """Audit AWS VPC configuration."""
        findings: List[CloudFinding] = []

        try:
            ec2_client = self._aws_session.client("ec2")  # type: ignore

            # Check VPC flow logs
            vpcs = ec2_client.describe_vpcs()
            for vpc in vpcs.get("Vpcs", []):
                vpc_id = vpc["VpcId"]

                flow_logs = ec2_client.describe_flow_logs(
                    Filters=[{"Name": "resource-id", "Values": [vpc_id]}]
                )

                if not flow_logs.get("FlowLogs"):
                    findings.append(
                        CloudFinding(
                            service=ServiceType.VPC,
                            resource_id=vpc_id,
                            resource_type="VPC",
                            title="VPC Flow Logs Disabled",
                            severity=SeverityLevel.MEDIUM,
                            description=f"VPC '{vpc_id}' does not have flow logs enabled",  # noqa: E501
                            risk="Cannot monitor or audit network traffic",
                            remediation="Enable VPC flow logs for network monitoring",  # noqa: E501
                            compliance_frameworks=["CIS AWS", "NIST 800-53"],
                        )
                    )

        except ClientError as e:
            logger.error(f"Error scanning VPC: {e}")
            raise ServiceUnavailableError(f"VPC scan failed: {e}") from e

        return findings

    def _scan_aws_lambda(self) -> List[CloudFinding]:
        """Audit AWS Lambda functions for security issues."""
        findings: List[CloudFinding] = []

        try:
            lambda_client = self._aws_session.client("lambda")  # type: ignore
            response = lambda_client.list_functions()

            for function in response.get("Functions", []):
                function_name = function["FunctionName"]

                # Check environment variables encryption
                env_vars = function.get("Environment", {})
                if env_vars.get("Variables") and not env_vars.get("KMSKeyArn"):
                    findings.append(
                        CloudFinding(
                            service=ServiceType.LAMBDA,
                            resource_id=function_name,
                            resource_type="Lambda Function",
                            title="Lambda Environment Variables Not Encrypted",  # noqa: E501
                            severity=SeverityLevel.MEDIUM,
                            description=f"Function '{function_name}' has unencrypted environment variables",  # noqa: E501
                            risk="Sensitive data in environment variables may be exposed",  # noqa: E501
                            remediation="Enable KMS encryption for environment variables",  # noqa: E501
                            compliance_frameworks=["CIS AWS"],
                        )
                    )

                # Check tracing
                if function.get("TracingConfig", {}).get("Mode") != "Active":
                    findings.append(
                        CloudFinding(
                            service=ServiceType.LAMBDA,
                            resource_id=function_name,
                            resource_type="Lambda Function",
                            title="Lambda X-Ray Tracing Disabled",
                            severity=SeverityLevel.LOW,
                            description=f"Function '{function_name}' does not have X-Ray tracing enabled",  # noqa: E501
                            risk="Limited visibility into function execution",
                            remediation="Enable AWS X-Ray tracing for observability",  # noqa: E501
                            compliance_frameworks=["CIS AWS"],
                        )
                    )

        except ClientError as e:
            logger.error(f"Error scanning Lambda: {e}")
            raise ServiceUnavailableError(f"Lambda scan failed: {e}") from e

        return findings

    def _check_open_security_group(
        self, sg: Dict[str, Any]
    ) -> Optional[CloudFinding]:  # noqa: E501
        """
        Check if security group has open access (0.0.0.0/0).

        Args:
            sg: Security group dictionary

        Returns:
            CloudFinding if security group is open, None otherwise
        """
        sg_id = sg["GroupId"]
        sg_name = sg["GroupName"]

        # Check inbound rules
        for rule in sg.get("IpPermissions", []):
            for ip_range in rule.get("IpRanges", []):
                if ip_range.get("CidrIp") == "0.0.0.0/0":
                    from_port = rule.get("FromPort", "All")
                    to_port = rule.get("ToPort", "All")

                    severity = SeverityLevel.CRITICAL
                    if from_port in [80, 443]:
                        severity = SeverityLevel.MEDIUM

                    return CloudFinding(
                        service=ServiceType.SECURITY_GROUPS,
                        resource_id=sg_id,
                        resource_type="Security Group",
                        title="Security Group Allows Public Access",
                        severity=severity,
                        description=f"Security group '{sg_name}' allows inbound traffic from 0.0.0.0/0 on ports {from_port}-{to_port}",  # noqa: E501
                        risk="Resources accessible from any internet address",
                        remediation="Restrict access to specific IP addresses or ranges",  # noqa: E501
                        compliance_frameworks=["CIS AWS"],
                        metadata={"from_port": from_port, "to_port": to_port},
                    )

        return None

    def scan_azure(
        self, services: Optional[List[ServiceType]] = None
    ) -> CloudResult:  # noqa: E501
        """
        Scan Azure infrastructure for security issues.

        Args:
            services: List of Azure services to scan

        Returns:
            CloudResult with findings

        Raises:
            CloudScanError: If scan fails
        """
        if not AZURE_AVAILABLE:
            raise CloudScanError("Azure SDK not available")

        logger.info("Starting Azure security scan")
        start_time = time.time()

        # Validate credentials
        self._validate_credentials(CloudProvider.AZURE)

        # Determine services to scan
        scan_services = (
            services
            or self.config.services
            or [
                ServiceType.STORAGE,
                ServiceType.VMS,
                ServiceType.NSG,
            ]
        )

        all_findings: List[CloudFinding] = []
        service_results: Dict[str, Dict[str, Any]] = {}
        total_resources = 0

        # Scan each service
        for service in scan_services:
            try:
                logger.info(f"Scanning Azure service: {service}")
                findings: List[CloudFinding] = []

                if service == ServiceType.STORAGE:
                    findings = self._scan_azure_storage()
                elif service == ServiceType.VMS:
                    findings = self._scan_azure_vms()
                elif service == ServiceType.NSG:
                    findings = self._scan_azure_nsg()

                all_findings.extend(findings)
                service_results[service.value] = {
                    "findings_count": len(findings),
                    "resources_scanned": sum(
                        1 for f in findings if f.resource_id
                    ),  # noqa: E501
                }
                total_resources += service_results[service.value][
                    "resources_scanned"
                ]  # noqa: E501

            except Exception as e:
                logger.error(f"Error scanning {service}: {e}")
                service_results[service.value] = {"error": str(e)}

        # Calculate severity counts
        severity_counts = self._calculate_severity_counts(all_findings)

        scan_time = time.time() - start_time

        return CloudResult(
            findings=all_findings,
            total_resources=total_resources,
            total_findings=len(all_findings),
            critical_count=severity_counts[SeverityLevel.CRITICAL],
            high_count=severity_counts[SeverityLevel.HIGH],
            medium_count=severity_counts[SeverityLevel.MEDIUM],
            low_count=severity_counts[SeverityLevel.LOW],
            service_results=service_results,
            scan_time=scan_time,
            provider=CloudProvider.AZURE,
            region=self.config.region,
        )

    def _scan_azure_storage(self) -> List[CloudFinding]:
        """Audit Azure Storage accounts for security issues."""
        findings: List[CloudFinding] = []

        try:
            if not self.config.azure_credentials:
                raise CredentialsError("Azure credentials not configured")

            subscription_id = self.config.azure_credentials.subscription_id
            storage_client = StorageManagementClient(
                self._azure_credential, subscription_id
            )

            accounts = storage_client.storage_accounts.list()

            for account in accounts:
                account_name = account.name

                # Check HTTPS enforcement
                if not account.enable_https_traffic_only:
                    findings.append(
                        CloudFinding(
                            service=ServiceType.STORAGE,
                            resource_id=account_name,
                            resource_type="Storage Account",
                            title="Storage Account Allows HTTP",
                            severity=SeverityLevel.HIGH,
                            description=f"Storage account '{account_name}' allows HTTP traffic",  # noqa: E501
                            risk="Data transmitted over unencrypted connections",  # noqa: E501
                            remediation="Enable 'Secure transfer required' setting",  # noqa: E501
                            compliance_frameworks=["CIS Azure"],
                        )
                    )

                # Check encryption
                if not account.encryption.services.blob.enabled:
                    findings.append(
                        CloudFinding(
                            service=ServiceType.STORAGE,
                            resource_id=account_name,
                            resource_type="Storage Account",
                            title="Storage Encryption Disabled",
                            severity=SeverityLevel.HIGH,
                            description=f"Storage account '{account_name}' does not have blob encryption",  # noqa: E501
                            risk="Data at rest is not encrypted",
                            remediation="Enable storage service encryption",
                            compliance_frameworks=["CIS Azure", "HIPAA"],
                        )
                    )

                # Check public access
                if account.allow_blob_public_access:
                    findings.append(
                        CloudFinding(
                            service=ServiceType.STORAGE,
                            resource_id=account_name,
                            resource_type="Storage Account",
                            title="Storage Allows Public Access",
                            severity=SeverityLevel.CRITICAL,
                            description=f"Storage account '{account_name}' allows public blob access",  # noqa: E501
                            risk="Storage containers may be publicly accessible",  # noqa: E501
                            remediation="Disable 'Allow Blob public access' setting",  # noqa: E501
                            compliance_frameworks=["CIS Azure"],
                        )
                    )

        except AzureError as e:
            logger.error(f"Error scanning Azure storage: {e}")
            raise ServiceUnavailableError(
                f"Azure storage scan failed: {e}"
            ) from e  # noqa: E501

        return findings

    def _scan_azure_vms(self) -> List[CloudFinding]:
        """Audit Azure VMs for security issues."""
        findings: List[CloudFinding] = []

        try:
            if not self.config.azure_credentials:
                raise CredentialsError("Azure credentials not configured")

            subscription_id = self.config.azure_credentials.subscription_id
            compute_client = ComputeManagementClient(
                self._azure_credential, subscription_id
            )

            vms = compute_client.virtual_machines.list_all()

            for vm in vms:
                vm_name = vm.name

                # Check disk encryption
                if (
                    vm.storage_profile.os_disk.encryption_settings
                    and not vm.storage_profile.os_disk.encryption_settings.enabled  # noqa: E501
                ):
                    findings.append(
                        CloudFinding(
                            service=ServiceType.VMS,
                            resource_id=vm_name,
                            resource_type="Virtual Machine",
                            title="VM Disk Not Encrypted",
                            severity=SeverityLevel.HIGH,
                            description=f"VM '{vm_name}' does not have disk encryption enabled",  # noqa: E501
                            risk="VM disk contents vulnerable to theft",
                            remediation="Enable Azure Disk Encryption",
                            compliance_frameworks=["CIS Azure", "HIPAA"],
                        )
                    )

        except AzureError as e:
            logger.error(f"Error scanning Azure VMs: {e}")
            raise ServiceUnavailableError(f"Azure VM scan failed: {e}") from e

        return findings

    def _scan_azure_nsg(self) -> List[CloudFinding]:
        """Audit Azure Network Security Groups."""
        findings: List[CloudFinding] = []

        try:
            if not self.config.azure_credentials:
                raise CredentialsError("Azure credentials not configured")

            subscription_id = self.config.azure_credentials.subscription_id
            network_client = NetworkManagementClient(
                self._azure_credential, subscription_id
            )

            nsgs = network_client.network_security_groups.list_all()

            for nsg in nsgs:
                nsg_name = nsg.name

                for rule in nsg.security_rules:
                    if (
                        rule.direction == "Inbound"
                        and rule.access == "Allow"
                        and rule.source_address_prefix == "*"
                    ):
                        findings.append(
                            CloudFinding(
                                service=ServiceType.NSG,
                                resource_id=nsg_name,
                                resource_type="Network Security Group",
                                title="NSG Allows Public Inbound Access",
                                severity=SeverityLevel.HIGH,
                                description=f"NSG '{nsg_name}' rule '{rule.name}' allows inbound from any source",  # noqa: E501
                                risk="Resources exposed to internet attacks",
                                remediation="Restrict source address to specific IPs or ranges",  # noqa: E501
                                compliance_frameworks=["CIS Azure"],
                                metadata={"rule_name": rule.name},
                            )
                        )

        except AzureError as e:
            logger.error(f"Error scanning Azure NSGs: {e}")
            raise ServiceUnavailableError(f"Azure NSG scan failed: {e}") from e

        return findings

    def scan_gcp(
        self, services: Optional[List[ServiceType]] = None
    ) -> CloudResult:  # noqa: E501
        """
        Scan GCP infrastructure for security issues.

        Args:
            services: List of GCP services to scan

        Returns:
            CloudResult with findings

        Raises:
            CloudScanError: If scan fails
        """
        if not GCP_AVAILABLE:
            raise CloudScanError("GCP SDK not available")

        logger.info("Starting GCP security scan")
        start_time = time.time()

        # Validate credentials
        self._validate_credentials(CloudProvider.GCP)

        # Determine services to scan
        scan_services = (
            services
            or self.config.services
            or [
                ServiceType.CLOUD_STORAGE,
                ServiceType.COMPUTE,
                ServiceType.GCP_IAM,
            ]
        )

        all_findings: List[CloudFinding] = []
        service_results: Dict[str, Dict[str, Any]] = {}
        total_resources = 0

        # Scan each service
        for service in scan_services:
            try:
                logger.info(f"Scanning GCP service: {service}")
                findings: List[CloudFinding] = []

                if service == ServiceType.CLOUD_STORAGE:
                    findings = self._scan_gcp_storage()
                elif service == ServiceType.COMPUTE:
                    findings = self._scan_gcp_compute()
                elif service == ServiceType.GCP_IAM:
                    findings = self._scan_gcp_iam()

                all_findings.extend(findings)
                service_results[service.value] = {
                    "findings_count": len(findings),
                    "resources_scanned": sum(
                        1 for f in findings if f.resource_id
                    ),  # noqa: E501
                }
                total_resources += service_results[service.value][
                    "resources_scanned"
                ]  # noqa: E501

            except Exception as e:
                logger.error(f"Error scanning {service}: {e}")
                service_results[service.value] = {"error": str(e)}

        # Calculate severity counts
        severity_counts = self._calculate_severity_counts(all_findings)

        scan_time = time.time() - start_time

        return CloudResult(
            findings=all_findings,
            total_resources=total_resources,
            total_findings=len(all_findings),
            critical_count=severity_counts[SeverityLevel.CRITICAL],
            high_count=severity_counts[SeverityLevel.HIGH],
            medium_count=severity_counts[SeverityLevel.MEDIUM],
            low_count=severity_counts[SeverityLevel.LOW],
            service_results=service_results,
            scan_time=scan_time,
            provider=CloudProvider.GCP,
            region=self.config.region,
        )

    def _scan_gcp_storage(self) -> List[CloudFinding]:
        """Audit GCP Cloud Storage buckets."""
        findings: List[CloudFinding] = []

        try:
            storage_client = self._gcp_clients["storage"]
            buckets = storage_client.list_buckets()

            for bucket in buckets:
                bucket_name = bucket.name

                # Check public access
                policy = bucket.get_iam_policy()
                for binding in policy.bindings:
                    if "allUsers" in binding.get(
                        "members", []
                    ) or "allAuthenticatedUsers" in binding.get(
                        "members", []
                    ):  # noqa: E501
                        findings.append(
                            CloudFinding(
                                service=ServiceType.CLOUD_STORAGE,
                                resource_id=bucket_name,
                                resource_type="GCS Bucket",
                                title="Public GCS Bucket",
                                severity=SeverityLevel.CRITICAL,
                                description=f"Bucket '{bucket_name}' is publicly accessible",  # noqa: E501
                                risk="Bucket contents accessible to anonymous users",  # noqa: E501
                                remediation="Remove allUsers and allAuthenticatedUsers from IAM policy",  # noqa: E501
                                compliance_frameworks=["CIS GCP"],
                            )
                        )

                # Check uniform bucket-level access
                if (
                    not bucket.iam_configuration.uniform_bucket_level_access_enabled  # noqa: E501
                ):  # noqa: E501
                    findings.append(
                        CloudFinding(
                            service=ServiceType.CLOUD_STORAGE,
                            resource_id=bucket_name,
                            resource_type="GCS Bucket",
                            title="Uniform Bucket Access Disabled",
                            severity=SeverityLevel.MEDIUM,
                            description=f"Bucket '{bucket_name}' does not have uniform bucket-level access",  # noqa: E501
                            risk="Inconsistent access control with ACLs",
                            remediation="Enable uniform bucket-level access",
                            compliance_frameworks=["CIS GCP"],
                        )
                    )

                # Check versioning
                if not bucket.versioning_enabled:
                    findings.append(
                        CloudFinding(
                            service=ServiceType.CLOUD_STORAGE,
                            resource_id=bucket_name,
                            resource_type="GCS Bucket",
                            title="GCS Versioning Disabled",
                            severity=SeverityLevel.MEDIUM,
                            description=f"Bucket '{bucket_name}' does not have versioning enabled",  # noqa: E501
                            risk="Cannot recover from accidental deletion",
                            remediation="Enable object versioning",
                            compliance_frameworks=["CIS GCP"],
                        )
                    )

        except GoogleAPIError as e:
            logger.error(f"Error scanning GCP storage: {e}")
            raise ServiceUnavailableError(
                f"GCP storage scan failed: {e}"
            ) from e  # noqa: E501

        return findings

    def _scan_gcp_compute(self) -> List[CloudFinding]:
        """Audit GCP Compute Engine instances."""
        findings: List[CloudFinding] = []

        try:
            if not self.config.gcp_credentials:
                raise CredentialsError("GCP credentials not configured")

            project = self.config.gcp_credentials.project_id
            compute_client = self._gcp_clients["compute"]

            # List instances across all zones
            aggregated_list = compute_client.aggregated_list(project=project)

            for zone, response in aggregated_list:
                if hasattr(response, "instances"):
                    for instance in response.instances:
                        instance_name = instance.name

                        # Check external IP
                        for interface in instance.network_interfaces:
                            if interface.access_configs:
                                findings.append(
                                    CloudFinding(
                                        service=ServiceType.COMPUTE,
                                        resource_id=instance_name,
                                        resource_type="Compute Instance",
                                        title="Instance with External IP",
                                        severity=SeverityLevel.MEDIUM,
                                        description=f"Instance '{instance_name}' has external IP address",  # noqa: E501
                                        risk="Instance directly accessible from internet",  # noqa: E501
                                        remediation="Remove external IP and use Cloud NAT",  # noqa: E501
                                        compliance_frameworks=["CIS GCP"],
                                    )
                                )

                        # Check disk encryption
                        for disk in instance.disks:
                            if not disk.disk_encryption_key:
                                findings.append(
                                    CloudFinding(
                                        service=ServiceType.COMPUTE,
                                        resource_id=instance_name,
                                        resource_type="Compute Instance",
                                        title="Disk Not Encrypted with CMEK",
                                        severity=SeverityLevel.MEDIUM,
                                        description=f"Instance '{instance_name}' disk not encrypted with customer-managed key",  # noqa: E501
                                        risk="Limited control over encryption keys",  # noqa: E501
                                        remediation="Use customer-managed encryption keys",  # noqa: E501
                                        compliance_frameworks=["CIS GCP"],
                                    )
                                )

        except GoogleAPIError as e:
            logger.error(f"Error scanning GCP compute: {e}")
            raise ServiceUnavailableError(
                f"GCP compute scan failed: {e}"
            ) from e  # noqa: E501

        return findings

    def _scan_gcp_iam(self) -> List[CloudFinding]:
        """Audit GCP IAM policies."""
        findings: List[CloudFinding] = []

        try:
            if not self.config.gcp_credentials:
                raise CredentialsError("GCP credentials not configured")

            project = self.config.gcp_credentials.project_id
            resource_client = self._gcp_clients["resource_manager"]

            # Get project IAM policy
            policy_request = resource_manager.GetIamPolicyRequest(
                resource=f"projects/{project}"
            )
            policy = resource_client.get_iam_policy(request=policy_request)

            # Check for overly permissive bindings
            for binding in policy.bindings:
                if (
                    "allUsers" in binding.members
                    or "allAuthenticatedUsers" in binding.members
                ):
                    findings.append(
                        CloudFinding(
                            service=ServiceType.GCP_IAM,
                            resource_id=project,
                            resource_type="Project",
                            title="Public IAM Binding",
                            severity=SeverityLevel.CRITICAL,
                            description=f"Project has public IAM binding for role '{binding.role}'",  # noqa: E501
                            risk="Unauthorized access to project resources",
                            remediation="Remove public members from IAM bindings",  # noqa: E501
                            compliance_frameworks=["CIS GCP"],
                        )
                    )

                # Check for owner role
                if binding.role == "roles/owner":
                    findings.append(
                        CloudFinding(
                            service=ServiceType.GCP_IAM,
                            resource_id=project,
                            resource_type="Project",
                            title="Excessive Owner Role Assignment",
                            severity=SeverityLevel.HIGH,
                            description=f"Project has {len(binding.members)} principals with Owner role",  # noqa: E501
                            risk="Excessive permissions increase security risk",  # noqa: E501
                            remediation=(
                                "Use more granular roles instead of Owner"
                            ),  # noqa: E501
                            compliance_frameworks=["CIS GCP"],
                        )
                    )

        except GoogleAPIError as e:
            logger.error(f"Error scanning GCP IAM: {e}")
            raise ServiceUnavailableError(f"GCP IAM scan failed: {e}") from e

        return findings

    def scan_all(
        self, services: Optional[List[ServiceType]] = None
    ) -> CloudResult:  # noqa: E501
        """
        Scan all configured cloud providers.

        Args:
            services: List of services to scan across providers

        Returns:
            Combined CloudResult with findings from all providers

        Raises:
            CloudScanError: If scan fails
        """
        logger.info("Starting multi-cloud security scan")
        start_time = time.time()

        all_findings: List[CloudFinding] = []
        service_results: Dict[str, Dict[str, Any]] = {}
        total_resources = 0

        # Scan AWS
        if self.config.provider in (CloudProvider.AWS, CloudProvider.MULTI):
            try:
                aws_result = self.scan_aws(services)
                all_findings.extend(aws_result.findings)
                total_resources += aws_result.total_resources
                service_results["aws"] = aws_result.service_results
            except Exception as e:
                logger.error(f"AWS scan failed: {e}")
                service_results["aws"] = {"error": str(e)}

        # Scan Azure
        if self.config.provider in (
            CloudProvider.AZURE,
            CloudProvider.MULTI,
        ):
            try:
                azure_result = self.scan_azure(services)
                all_findings.extend(azure_result.findings)
                total_resources += azure_result.total_resources
                service_results["azure"] = azure_result.service_results
            except Exception as e:
                logger.error(f"Azure scan failed: {e}")
                service_results["azure"] = {"error": str(e)}

        # Scan GCP
        if self.config.provider in (CloudProvider.GCP, CloudProvider.MULTI):
            try:
                gcp_result = self.scan_gcp(services)
                all_findings.extend(gcp_result.findings)
                total_resources += gcp_result.total_resources
                service_results["gcp"] = gcp_result.service_results
            except Exception as e:
                logger.error(f"GCP scan failed: {e}")
                service_results["gcp"] = {"error": str(e)}

        # Calculate severity counts
        severity_counts = self._calculate_severity_counts(all_findings)

        scan_time = time.time() - start_time

        return CloudResult(
            findings=all_findings,
            total_resources=total_resources,
            total_findings=len(all_findings),
            critical_count=severity_counts[SeverityLevel.CRITICAL],
            high_count=severity_counts[SeverityLevel.HIGH],
            medium_count=severity_counts[SeverityLevel.MEDIUM],
            low_count=severity_counts[SeverityLevel.LOW],
            service_results=service_results,
            scan_time=scan_time,
            provider=CloudProvider.MULTI,
        )

    def _calculate_severity_counts(
        self, findings: List[CloudFinding]
    ) -> Dict[SeverityLevel, int]:
        """Calculate counts by severity level."""
        counts = {
            SeverityLevel.CRITICAL: 0,
            SeverityLevel.HIGH: 0,
            SeverityLevel.MEDIUM: 0,
            SeverityLevel.LOW: 0,
            SeverityLevel.INFO: 0,
        }

        for finding in findings:
            counts[finding.severity] += 1

        return counts

    def export_findings(self, result: CloudResult, output_file: Path) -> None:
        """
        Export scan findings to JSON file.

        Args:
            result: Cloud scan result
            output_file: Path to output file
        """
        output_data = {
            "scan_metadata": {
                "provider": result.provider.value,
                "region": result.region,
                "timestamp": result.timestamp.isoformat(),
                "scan_time": result.scan_time,
            },
            "summary": {
                "total_resources": result.total_resources,
                "total_findings": result.total_findings,
                "critical_count": result.critical_count,
                "high_count": result.high_count,
                "medium_count": result.medium_count,
                "low_count": result.low_count,
            },
            "findings": [
                {
                    "service": f.service.value,
                    "resource_id": f.resource_id,
                    "resource_type": f.resource_type,
                    "title": f.title,
                    "severity": f.severity.value,
                    "description": f.description,
                    "risk": f.risk,
                    "remediation": f.remediation,
                    "compliance_frameworks": f.compliance_frameworks,
                    "metadata": f.metadata,
                }
                for f in result.findings
            ],
            "service_results": result.service_results,
        }

        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=2, default=str)

        logger.info(f"Findings exported to {output_file}")
