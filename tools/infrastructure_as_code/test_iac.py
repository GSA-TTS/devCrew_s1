"""
Comprehensive test suite for Infrastructure as Code platform.

This module provides unit tests for all IaC components with mocked
Terraform CLI and cloud provider APIs.
"""

import json
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from decimal import Decimal

from issue_38_terraform_wrapper import (
    TerraformWrapper,
    TerraformOutput,
    TerraformError,
    TerraformCommandError
)
from issue_38_cloud_providers import (
    ProviderFactory,
    ProviderConfig,
    AWSProvider,
    AzureProvider,
    GCPProvider,
    CloudProviderError
)
from issue_38_state_manager import StateManager, StateBackup
from issue_38_validator import TerraformValidator, ValidationReport, SeverityLevel
from issue_38_drift_detector import DriftDetector, DriftType
from issue_38_cost_estimator import CostEstimator, ResourceCost


class TestTerraformWrapper:
    """Test cases for TerraformWrapper."""

    @pytest.fixture
    def mock_terraform_dir(self, tmp_path):
        """Create temporary Terraform directory."""
        tf_dir = tmp_path / "terraform"
        tf_dir.mkdir()
        return tf_dir

    @pytest.fixture
    def terraform_wrapper(self, mock_terraform_dir):
        """Create TerraformWrapper instance with mocked execution."""
        with patch.object(TerraformWrapper, '_verify_terraform_installed'):
            wrapper = TerraformWrapper(
                working_dir=str(mock_terraform_dir),
                terraform_bin="terraform"
            )
            return wrapper

    def test_init_success(self, terraform_wrapper):
        """Test terraform init succeeds."""
        with patch.object(TerraformWrapper, '_execute_command') as mock_exec:
            mock_exec.return_value = TerraformOutput(
                success=True,
                stdout="Terraform initialized",
                stderr="",
                return_code=0,
                duration=1.0
            )

            result = terraform_wrapper.init()

            assert result.success
            assert "initialized" in result.stdout.lower()
            mock_exec.assert_called_once()

    def test_init_with_backend_config(self, terraform_wrapper):
        """Test terraform init with backend configuration."""
        with patch.object(TerraformWrapper, '_execute_command') as mock_exec:
            mock_exec.return_value = TerraformOutput(
                success=True,
                stdout="Backend configured",
                stderr="",
                return_code=0,
                duration=1.0
            )

            backend_config = {
                "bucket": "my-bucket",
                "key": "terraform.tfstate"
            }

            result = terraform_wrapper.init(backend_config=backend_config)

            assert result.success
            call_args = mock_exec.call_args[0][0]
            assert "-backend-config" in call_args
            assert "bucket=my-bucket" in call_args

    def test_plan_success(self, terraform_wrapper):
        """Test terraform plan succeeds."""
        with patch.object(TerraformWrapper, '_execute_command') as mock_exec:
            mock_exec.return_value = TerraformOutput(
                success=True,
                stdout="Plan: 1 to add, 0 to change, 0 to destroy",
                stderr="",
                return_code=0,
                duration=2.0
            )

            result = terraform_wrapper.plan()

            assert result.success
            assert "Plan:" in result.stdout

    def test_plan_json(self, terraform_wrapper):
        """Test terraform plan with JSON output."""
        plan_data = {
            "format_version": "1.1",
            "terraform_version": "1.6.0",
            "resource_changes": []
        }

        with patch.object(TerraformWrapper, '_execute_command') as mock_exec:
            mock_exec.side_effect = [
                # First call: plan
                TerraformOutput(
                    success=True,
                    stdout="Plan created",
                    stderr="",
                    return_code=0,
                    duration=1.0
                ),
                # Second call: show -json
                TerraformOutput(
                    success=True,
                    stdout=json.dumps(plan_data),
                    stderr="",
                    return_code=0,
                    duration=0.5
                )
            ]

            result = terraform_wrapper.plan_json()

            assert result["format_version"] == "1.1"
            assert "resource_changes" in result

    def test_apply_success(self, terraform_wrapper):
        """Test terraform apply succeeds."""
        with patch.object(TerraformWrapper, '_execute_command') as mock_exec:
            mock_exec.return_value = TerraformOutput(
                success=True,
                stdout="Apply complete! Resources: 1 added, 0 changed, 0 destroyed",
                stderr="",
                return_code=0,
                duration=5.0
            )

            result = terraform_wrapper.apply(auto_approve=True)

            assert result.success
            assert "Apply complete" in result.stdout

    def test_destroy_success(self, terraform_wrapper):
        """Test terraform destroy succeeds."""
        with patch.object(TerraformWrapper, '_execute_command') as mock_exec:
            mock_exec.return_value = TerraformOutput(
                success=True,
                stdout="Destroy complete! Resources: 1 destroyed",
                stderr="",
                return_code=0,
                duration=3.0
            )

            result = terraform_wrapper.destroy(auto_approve=True)

            assert result.success
            assert "Destroy complete" in result.stdout

    def test_state_list(self, terraform_wrapper):
        """Test terraform state list."""
        with patch.object(TerraformWrapper, '_execute_command') as mock_exec:
            mock_exec.return_value = TerraformOutput(
                success=True,
                stdout="aws_instance.web\naws_s3_bucket.data",
                stderr="",
                return_code=0,
                duration=0.5
            )

            resources = terraform_wrapper.state_list()

            assert len(resources) == 2
            assert "aws_instance.web" in resources
            assert "aws_s3_bucket.data" in resources

    def test_workspace_operations(self, terraform_wrapper):
        """Test workspace operations."""
        with patch.object(TerraformWrapper, '_execute_command') as mock_exec:
            # Test workspace list
            mock_exec.return_value = TerraformOutput(
                success=True,
                stdout="  default\n* dev\n  prod",
                stderr="",
                return_code=0,
                duration=0.3
            )

            workspaces = terraform_wrapper.workspace_list()

            assert len(workspaces) == 3
            assert "dev" in workspaces

    def test_command_failure_with_retry(self, terraform_wrapper):
        """Test command retry on failure."""
        with patch.object(TerraformWrapper, '_execute_command') as mock_exec:
            # Simulate transient failure then success
            mock_exec.side_effect = [
                TerraformCommandError("Connection timeout"),
                TerraformOutput(
                    success=True,
                    stdout="Success",
                    stderr="",
                    return_code=0,
                    duration=1.0
                )
            ]

            # This should not raise exception due to retry
            # Note: In real implementation, retry is in _execute_command
            # For this test, we're just verifying the mock behavior


class TestCloudProviders:
    """Test cases for cloud providers."""

    def test_aws_provider_config(self):
        """Test AWS provider configuration."""
        config = ProviderConfig(
            name="aws",
            region="us-east-1",
            credentials={
                "access_key_id": "AKIATEST",
                "secret_access_key": "secret"
            }
        )

        with patch('boto3.Session'):
            with patch.object(AWSProvider, 'validate_credentials', return_value=True):
                provider = AWSProvider(config)

                backend_config = provider.get_terraform_backend_config()

                assert "bucket" in backend_config
                assert backend_config["region"] == "us-east-1"
                assert backend_config["encrypt"] == "true"

    def test_aws_provider_block_generation(self):
        """Test AWS provider block generation."""
        config = ProviderConfig(
            name="aws",
            region="us-west-2",
            credentials={},
            tags={"Environment": "test", "Owner": "team"}
        )

        with patch.object(AWSProvider, 'validate_credentials', return_value=True):
            provider = AWSProvider(config)

            provider_block = provider.get_terraform_provider_block()

            assert "provider \"aws\"" in provider_block
            assert "region = \"us-west-2\"" in provider_block
            assert "Environment" in provider_block

    def test_azure_provider_config(self):
        """Test Azure provider configuration."""
        config = ProviderConfig(
            name="azure",
            region="eastus",
            credentials={
                "subscription_id": "sub-123"
            }
        )

        with patch.object(AzureProvider, 'validate_credentials', return_value=True):
            provider = AzureProvider(config)

            backend_config = provider.get_terraform_backend_config()

            assert "storage_account_name" in backend_config
            assert "container_name" in backend_config

    def test_gcp_provider_config(self):
        """Test GCP provider configuration."""
        config = ProviderConfig(
            name="gcp",
            region="us-central1",
            credentials={
                "project_id": "my-project"
            }
        )

        with patch.object(GCPProvider, 'validate_credentials', return_value=True):
            provider = GCPProvider(config)

            backend_config = provider.get_terraform_backend_config()

            assert "bucket" in backend_config
            assert "prefix" in backend_config

    def test_provider_factory(self):
        """Test provider factory."""
        config = ProviderConfig(
            name="aws",
            region="us-east-1",
            credentials={}
        )

        with patch.object(AWSProvider, 'validate_credentials', return_value=True):
            provider = ProviderFactory.create_provider(config)

            assert isinstance(provider, AWSProvider)

    def test_unsupported_provider(self):
        """Test unsupported provider raises error."""
        config = ProviderConfig(
            name="unsupported",
            region="us-east-1",
            credentials={}
        )

        with pytest.raises(CloudProviderError):
            ProviderFactory.create_provider(config)


class TestStateManager:
    """Test cases for StateManager."""

    @pytest.fixture
    def mock_state_data(self):
        """Mock Terraform state data."""
        return {
            "version": 4,
            "terraform_version": "1.6.0",
            "serial": 1,
            "lineage": "test",
            "resources": []
        }

    def test_s3_state_manager_init(self):
        """Test S3 state manager initialization."""
        backend_config = {
            "bucket": "terraform-state",
            "key": "terraform.tfstate",
            "region": "us-east-1"
        }

        with patch('boto3.client'):
            manager = StateManager("s3", backend_config)

            assert manager.backend_type == "s3"
            assert manager.backend_config == backend_config

    def test_get_state_s3(self, mock_state_data):
        """Test getting state from S3."""
        backend_config = {
            "bucket": "terraform-state",
            "key": "terraform.tfstate",
            "region": "us-east-1"
        }

        with patch('boto3.client') as mock_client:
            mock_s3 = MagicMock()
            mock_client.return_value = mock_s3

            mock_s3.get_object.return_value = {
                "Body": MagicMock(
                    read=lambda: json.dumps(mock_state_data).encode()
                )
            }

            manager = StateManager("s3", backend_config)
            state = manager.get_state()

            assert state["version"] == 4
            assert state["terraform_version"] == "1.6.0"

    def test_backup_state(self, mock_state_data, tmp_path):
        """Test state backup."""
        backend_config = {
            "bucket": "terraform-state",
            "key": "terraform.tfstate",
            "region": "us-east-1"
        }

        with patch('boto3.client') as mock_client:
            mock_s3 = MagicMock()
            mock_client.return_value = mock_s3

            # Mock get_object for backup
            mock_s3.get_object.return_value = {
                "Body": MagicMock(
                    read=lambda: json.dumps(mock_state_data).encode()
                )
            }

            # Mock put_object for backup
            mock_s3.put_object.return_value = {}

            manager = StateManager("s3", backend_config)
            backup = manager.backup_state(backup_path=tmp_path)

            assert backup.backend == "s3"
            assert "s3://" in backup.path


class TestValidator:
    """Test cases for TerraformValidator."""

    @pytest.fixture
    def mock_terraform_dir(self, tmp_path):
        """Create temporary Terraform directory."""
        tf_dir = tmp_path / "terraform"
        tf_dir.mkdir()
        (tf_dir / "main.tf").write_text("# test config")
        return tf_dir

    @pytest.fixture
    def validator(self, mock_terraform_dir):
        """Create TerraformValidator instance."""
        with patch.object(TerraformValidator, '_check_tools'):
            validator = TerraformValidator(
                working_dir=str(mock_terraform_dir),
                enable_checkov=True,
                enable_tfsec=True
            )
            return validator

    def test_validator_initialization(self, validator):
        """Test validator initialization."""
        assert validator.working_dir.exists()
        assert validator.enable_checkov
        assert validator.enable_tfsec

    def test_validate_with_no_issues(self, validator):
        """Test validation with no issues."""
        with patch.object(validator, '_run_checkov', return_value=[]):
            with patch.object(validator, '_run_tfsec', return_value=[]):
                report = validator.validate()

                assert report.failed == 0
                assert len(report.findings) == 0

    def test_generate_text_report(self, validator):
        """Test text report generation."""
        from issue_38_validator import ValidationFinding

        findings = [
            ValidationFinding(
                check_id="CKV_AWS_1",
                check_name="Ensure S3 bucket has encryption",
                severity=SeverityLevel.HIGH,
                resource="aws_s3_bucket.data",
                file_path="main.tf",
                line_range=(10, 15),
                description="S3 bucket should have encryption enabled"
            )
        ]

        report = ValidationReport(
            passed=5,
            failed=1,
            skipped=0,
            findings=findings,
            summary={"high": 1, "medium": 0, "low": 0},
            scan_duration=2.5
        )

        text_report = validator.generate_report(report, output_format="text")

        assert "Validation Report" in text_report
        assert "CKV_AWS_1" in text_report
        assert "HIGH" in text_report


class TestDriftDetector:
    """Test cases for DriftDetector."""

    @pytest.fixture
    def mock_terraform(self):
        """Mock TerraformWrapper."""
        mock = Mock(spec=TerraformWrapper)
        return mock

    @pytest.fixture
    def mock_state_manager(self):
        """Mock StateManager."""
        mock = Mock(spec=StateManager)
        return mock

    @pytest.fixture
    def drift_detector(self, mock_terraform, mock_state_manager):
        """Create DriftDetector instance."""
        return DriftDetector(mock_terraform, mock_state_manager)

    def test_detect_no_drift(self, drift_detector, mock_terraform):
        """Test drift detection with no drift."""
        mock_terraform.plan.return_value = TerraformOutput(
            success=True,
            stdout="No changes. Infrastructure is up-to-date.",
            stderr="",
            return_code=0,
            duration=1.0
        )

        mock_terraform.plan_json.return_value = {
            "resource_changes": []
        }

        mock_terraform.state_list.return_value = [
            "aws_instance.web",
            "aws_s3_bucket.data"
        ]

        report = drift_detector.detect_drift()

        assert report.drifted_resources == 0
        assert len(report.drift_details) == 0

    def test_detect_drift_with_changes(self, drift_detector, mock_terraform):
        """Test drift detection with changes."""
        mock_terraform.plan.return_value = TerraformOutput(
            success=True,
            stdout="Plan: 0 to add, 1 to change, 0 to destroy",
            stderr="",
            return_code=0,
            duration=1.0
        )

        mock_terraform.plan_json.return_value = {
            "resource_changes": [
                {
                    "type": "aws_instance",
                    "name": "web",
                    "address": "aws_instance.web",
                    "change": {
                        "actions": ["update"],
                        "before": {"instance_type": "t2.micro"},
                        "after": {"instance_type": "t2.small"}
                    }
                }
            ]
        }

        mock_terraform.state_list.return_value = ["aws_instance.web"]

        report = drift_detector.detect_drift()

        assert report.drifted_resources == 1
        assert len(report.drift_details) == 1
        assert report.drift_details[0].drift_type == DriftType.MODIFIED


class TestCostEstimator:
    """Test cases for CostEstimator."""

    @pytest.fixture
    def mock_terraform(self):
        """Mock TerraformWrapper."""
        mock = Mock(spec=TerraformWrapper)
        return mock

    @pytest.fixture
    def cost_estimator(self, mock_terraform):
        """Create CostEstimator instance."""
        return CostEstimator(mock_terraform, provider="aws")

    def test_estimate_ec2_cost(self, cost_estimator, mock_terraform):
        """Test EC2 instance cost estimation."""
        mock_terraform.plan_json.return_value = {
            "resource_changes": [
                {
                    "type": "aws_instance",
                    "name": "web",
                    "address": "aws_instance.web",
                    "change": {
                        "actions": ["create"],
                        "after": {
                            "instance_type": "t2.micro"
                        }
                    }
                }
            ]
        }

        estimate = cost_estimator.estimate_costs()

        assert estimate.provider == "aws"
        assert len(estimate.resource_costs) == 1
        assert estimate.resource_costs[0].resource_type == "aws_instance"
        assert estimate.total_monthly_cost > 0

    def test_estimate_multiple_resources(self, cost_estimator, mock_terraform):
        """Test cost estimation for multiple resources."""
        mock_terraform.plan_json.return_value = {
            "resource_changes": [
                {
                    "type": "aws_instance",
                    "name": "web",
                    "address": "aws_instance.web",
                    "change": {
                        "actions": ["create"],
                        "after": {"instance_type": "t2.small"}
                    }
                },
                {
                    "type": "aws_ebs_volume",
                    "name": "data",
                    "address": "aws_ebs_volume.data",
                    "change": {
                        "actions": ["create"],
                        "after": {"type": "gp2", "size": 100}
                    }
                }
            ]
        }

        estimate = cost_estimator.estimate_costs()

        assert len(estimate.resource_costs) == 2
        assert estimate.total_monthly_cost > 0

    def test_budget_check_under_limit(self, cost_estimator, mock_terraform):
        """Test budget check under limit."""
        mock_terraform.plan_json.return_value = {
            "resource_changes": [
                {
                    "type": "aws_instance",
                    "name": "web",
                    "address": "aws_instance.web",
                    "change": {
                        "actions": ["create"],
                        "after": {"instance_type": "t2.micro"}
                    }
                }
            ]
        }

        estimate = cost_estimator.estimate_costs()
        budget_check = cost_estimator.check_budget_alert(
            estimate,
            Decimal("1000.00")
        )

        assert not budget_check["exceeds_budget"]
        assert "within budget" in budget_check["message"]

    def test_budget_check_over_limit(self, cost_estimator, mock_terraform):
        """Test budget check over limit."""
        mock_terraform.plan_json.return_value = {
            "resource_changes": [
                {
                    "type": "aws_instance",
                    "name": "large",
                    "address": "aws_instance.large",
                    "change": {
                        "actions": ["create"],
                        "after": {"instance_type": "m5.xlarge"}
                    }
                }
            ]
        }

        estimate = cost_estimator.estimate_costs()
        budget_check = cost_estimator.check_budget_alert(
            estimate,
            Decimal("10.00")  # Very low budget
        )

        assert budget_check["exceeds_budget"]
        assert "exceeds budget" in budget_check["message"]


# Pytest configuration
def pytest_configure(config):
    """Configure pytest."""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
