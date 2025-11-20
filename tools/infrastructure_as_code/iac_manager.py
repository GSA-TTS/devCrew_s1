"""
Main CLI interface for Infrastructure as Code management.

This module provides a command-line interface for all IaC operations
including provisioning, validation, drift detection, and cost estimation.
"""

import argparse
import logging
import sys
import yaml
from pathlib import Path
from typing import Optional, Dict, Any
from decimal import Decimal

from issue_38_terraform_wrapper import TerraformWrapper, TerraformError
from issue_38_cloud_providers import ProviderFactory, ProviderConfig, CloudProviderError
from issue_38_state_manager import StateManager, StateError
from issue_38_validator import TerraformValidator, ValidationError, SeverityLevel
from issue_38_drift_detector import DriftDetector, DriftError
from issue_38_cost_estimator import CostEstimator, CostEstimationError


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class IaCManager:
    """
    Main Infrastructure as Code manager.

    Orchestrates all IaC operations and provides a unified CLI interface.
    """

    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize IaC manager.

        Args:
            config_file: Path to configuration file
        """
        self.config = self._load_config(config_file)
        self.terraform = None
        self.state_manager = None
        self.validator = None
        self.drift_detector = None
        self.cost_estimator = None

    def _load_config(self, config_file: Optional[str]) -> Dict[str, Any]:
        """
        Load configuration from file.

        Args:
            config_file: Path to configuration file

        Returns:
            Configuration dictionary
        """
        default_config = {
            "terraform": {
                "binary": "terraform",
                "working_dir": ".",
                "max_retries": 3,
                "retry_delay": 5
            },
            "provider": {
                "name": "aws",
                "region": "us-east-1",
                "credentials": {}
            },
            "validation": {
                "enable_checkov": True,
                "enable_tfsec": True,
                "severity_threshold": "MEDIUM"
            },
            "cost_estimation": {
                "enabled": True,
                "budget_limit": 1000.0
            }
        }

        if config_file and Path(config_file).exists():
            try:
                with open(config_file) as f:
                    file_config = yaml.safe_load(f)
                    # Merge with defaults
                    default_config.update(file_config or {})
                    logger.info(f"Loaded configuration from {config_file}")
            except Exception as e:
                logger.warning(f"Failed to load config file: {e}")

        return default_config

    def initialize(self, working_dir: str) -> None:
        """
        Initialize all components.

        Args:
            working_dir: Directory containing Terraform configurations
        """
        # Initialize Terraform wrapper
        terraform_config = self.config.get("terraform", {})
        self.terraform = TerraformWrapper(
            working_dir=working_dir,
            terraform_bin=terraform_config.get("binary", "terraform"),
            max_retries=terraform_config.get("max_retries", 3),
            retry_delay=terraform_config.get("retry_delay", 5)
        )

        # Initialize state manager if backend configured
        backend_config = self.config.get("backend")
        if backend_config:
            backend_type = backend_config.get("type", "local")
            if backend_type != "local":
                self.state_manager = StateManager(
                    backend_type=backend_type,
                    backend_config=backend_config
                )

        # Initialize validator
        validation_config = self.config.get("validation", {})
        self.validator = TerraformValidator(
            working_dir=working_dir,
            enable_checkov=validation_config.get("enable_checkov", True),
            enable_tfsec=validation_config.get("enable_tfsec", True)
        )

        # Initialize drift detector
        if self.state_manager:
            self.drift_detector = DriftDetector(
                terraform_wrapper=self.terraform,
                state_manager=self.state_manager
            )
        else:
            self.drift_detector = DriftDetector(
                terraform_wrapper=self.terraform,
                state_manager=None
            )

        # Initialize cost estimator
        provider_name = self.config.get("provider", {}).get("name", "aws")
        self.cost_estimator = CostEstimator(
            terraform_wrapper=self.terraform,
            provider=provider_name
        )

        logger.info("IaC Manager initialized successfully")

    def provision(
        self,
        auto_approve: bool = False,
        var_file: Optional[str] = None
    ) -> bool:
        """
        Provision infrastructure.

        Args:
            auto_approve: Skip interactive approval
            var_file: Path to variable file

        Returns:
            True if successful
        """
        try:
            logger.info("=" * 80)
            logger.info("PROVISIONING INFRASTRUCTURE")
            logger.info("=" * 80)

            # Initialize Terraform
            logger.info("Running terraform init...")
            self.terraform.init(upgrade=True)

            # Validate configuration
            logger.info("Validating Terraform configuration...")
            self.terraform.validate()

            # Run security validation
            logger.info("Running security validation...")
            validation_config = self.config.get("validation", {})
            severity = SeverityLevel[
                validation_config.get("severity_threshold", "MEDIUM")
            ]
            validation_report = self.validator.validate(
                severity_threshold=severity
            )

            if validation_report.failed > 0:
                logger.warning(
                    f"Validation found {validation_report.failed} issues"
                )
                print(self.validator.generate_report(
                    validation_report,
                    output_format="text"
                ))

                if validation_report.summary.get("critical", 0) > 0:
                    logger.error("Critical security issues found. Aborting.")
                    return False

                if not auto_approve:
                    response = input("Continue despite validation issues? (yes/no): ")
                    if response.lower() != "yes":
                        logger.info("Provisioning aborted by user")
                        return False

            # Generate cost estimate
            if self.config.get("cost_estimation", {}).get("enabled", True):
                logger.info("Generating cost estimate...")
                cost_estimate = self.cost_estimator.estimate_costs()
                print(self.cost_estimator.generate_cost_report(
                    cost_estimate,
                    output_format="text"
                ))

                # Check budget
                budget_limit = Decimal(
                    str(self.config.get("cost_estimation", {}).get("budget_limit", 1000.0))
                )
                budget_check = self.cost_estimator.check_budget_alert(
                    cost_estimate,
                    budget_limit
                )

                if budget_check["exceeds_budget"]:
                    logger.warning(budget_check["message"])
                    if not auto_approve:
                        response = input("Continue despite budget overage? (yes/no): ")
                        if response.lower() != "yes":
                            logger.info("Provisioning aborted by user")
                            return False

            # Run terraform plan
            logger.info("Running terraform plan...")
            self.terraform.plan(var_file=var_file, out="tfplan")

            if not auto_approve:
                response = input("Apply this plan? (yes/no): ")
                if response.lower() != "yes":
                    logger.info("Provisioning aborted by user")
                    return False

            # Apply the plan
            logger.info("Running terraform apply...")
            result = self.terraform.apply(plan_file="tfplan", auto_approve=True)

            if result.success:
                logger.info("✓ Infrastructure provisioned successfully")
                return True
            else:
                logger.error("✗ Provisioning failed")
                return False

        except (TerraformError, ValidationError, CostEstimationError) as e:
            logger.error(f"Provisioning failed: {e}")
            return False

    def validate_config(
        self,
        output_format: str = "text",
        output_file: Optional[str] = None
    ) -> bool:
        """
        Validate Terraform configuration.

        Args:
            output_format: Report format (text, json, html)
            output_file: Optional file to write report to

        Returns:
            True if validation passed
        """
        try:
            logger.info("=" * 80)
            logger.info("VALIDATING CONFIGURATION")
            logger.info("=" * 80)

            # Terraform validate
            logger.info("Running terraform validate...")
            self.terraform.validate()

            # Security validation
            logger.info("Running security validation...")
            validation_config = self.config.get("validation", {})
            severity = SeverityLevel[
                validation_config.get("severity_threshold", "MEDIUM")
            ]

            validation_report = self.validator.validate(
                severity_threshold=severity
            )

            # Generate report
            report = self.validator.generate_report(
                validation_report,
                output_format=output_format,
                output_file=output_file
            )

            if output_format == "text":
                print(report)

            if validation_report.failed == 0:
                logger.info("✓ Validation passed")
                return True
            else:
                logger.warning(f"✗ Validation found {validation_report.failed} issues")
                return False

        except (TerraformError, ValidationError) as e:
            logger.error(f"Validation failed: {e}")
            return False

    def detect_drift(
        self,
        output_format: str = "text",
        output_file: Optional[str] = None,
        auto_remediate: bool = False
    ) -> bool:
        """
        Detect configuration drift.

        Args:
            output_format: Report format (text, json, html)
            output_file: Optional file to write report to
            auto_remediate: Automatically remediate drift

        Returns:
            True if no drift detected
        """
        try:
            logger.info("=" * 80)
            logger.info("DETECTING CONFIGURATION DRIFT")
            logger.info("=" * 80)

            # Detect drift
            drift_report = self.drift_detector.detect_drift()

            # Generate report
            report = self.drift_detector.generate_drift_report(
                drift_report,
                output_format=output_format,
                output_file=output_file
            )

            if output_format == "text":
                print(report)

            # Show remediation recommendations
            if drift_report.drifted_resources > 0:
                logger.info("\nRemediation Recommendations:")
                recommendations = self.drift_detector.get_remediation_recommendations(
                    drift_report
                )
                for rec in recommendations:
                    print(f"\n  Resource: {rec['resource']}")
                    print(f"  Action: {rec['action']}")
                    print(f"  Command: {rec['command']}")
                    print(f"  Description: {rec['description']}")

                # Auto-remediate if requested
                if auto_remediate:
                    logger.warning("Starting auto-remediation...")
                    results = self.drift_detector.auto_remediate(
                        drift_report,
                        auto_approve=True
                    )
                    logger.info(f"Remediated: {len(results['remediated'])} resources")
                    logger.info(f"Failed: {len(results['failed'])} resources")
                    logger.info(f"Skipped: {len(results['skipped'])} resources")

            if drift_report.drifted_resources == 0:
                logger.info("✓ No drift detected")
                return True
            else:
                logger.warning(f"✗ {drift_report.drifted_resources} resources drifted")
                return False

        except DriftError as e:
            logger.error(f"Drift detection failed: {e}")
            return False

    def estimate_cost(
        self,
        output_format: str = "text",
        output_file: Optional[str] = None
    ) -> bool:
        """
        Estimate infrastructure costs.

        Args:
            output_format: Report format (text, json, html)
            output_file: Optional file to write report to

        Returns:
            True if successful
        """
        try:
            logger.info("=" * 80)
            logger.info("ESTIMATING INFRASTRUCTURE COSTS")
            logger.info("=" * 80)

            # Generate cost estimate
            cost_estimate = self.cost_estimator.estimate_costs()

            # Generate report
            report = self.cost_estimator.generate_cost_report(
                cost_estimate,
                output_format=output_format,
                output_file=output_file
            )

            if output_format == "text":
                print(report)

            # Check budget
            if self.config.get("cost_estimation", {}).get("enabled", True):
                budget_limit = Decimal(
                    str(self.config.get("cost_estimation", {}).get("budget_limit", 1000.0))
                )
                budget_check = self.cost_estimator.check_budget_alert(
                    cost_estimate,
                    budget_limit
                )

                print(f"\nBudget Check: {budget_check['message']}")

            logger.info("✓ Cost estimation complete")
            return True

        except CostEstimationError as e:
            logger.error(f"Cost estimation failed: {e}")
            return False

    def destroy(
        self,
        auto_approve: bool = False,
        var_file: Optional[str] = None
    ) -> bool:
        """
        Destroy infrastructure.

        Args:
            auto_approve: Skip interactive approval
            var_file: Path to variable file

        Returns:
            True if successful
        """
        try:
            logger.info("=" * 80)
            logger.info("DESTROYING INFRASTRUCTURE")
            logger.info("=" * 80)

            if not auto_approve:
                logger.warning("⚠ WARNING: This will destroy all managed infrastructure!")
                response = input("Are you absolutely sure? Type 'destroy' to confirm: ")
                if response != "destroy":
                    logger.info("Destroy aborted by user")
                    return False

            # Backup state before destroy
            if self.state_manager:
                logger.info("Backing up state...")
                backup = self.state_manager.backup_state()
                logger.info(f"State backed up: {backup.path}")

            # Run destroy
            logger.info("Running terraform destroy...")
            result = self.terraform.destroy(
                var_file=var_file,
                auto_approve=auto_approve or True
            )

            if result.success:
                logger.info("✓ Infrastructure destroyed successfully")
                return True
            else:
                logger.error("✗ Destroy failed")
                return False

        except (TerraformError, StateError) as e:
            logger.error(f"Destroy failed: {e}")
            return False


def main():
    """Main entry point for CLI."""
    parser = argparse.ArgumentParser(
        description="Infrastructure as Code Provisioning & Management Platform",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        "-c", "--config",
        help="Configuration file path",
        default="issue_38_config.yaml"
    )

    parser.add_argument(
        "-d", "--directory",
        help="Terraform working directory",
        default="."
    )

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Provision command
    provision_parser = subparsers.add_parser(
        "provision",
        help="Provision infrastructure"
    )
    provision_parser.add_argument(
        "--auto-approve",
        action="store_true",
        help="Skip interactive approval"
    )
    provision_parser.add_argument(
        "--var-file",
        help="Path to variable file"
    )

    # Validate command
    validate_parser = subparsers.add_parser(
        "validate",
        help="Validate Terraform configuration"
    )
    validate_parser.add_argument(
        "--format",
        choices=["text", "json", "html"],
        default="text",
        help="Output format"
    )
    validate_parser.add_argument(
        "--output",
        help="Output file path"
    )

    # Drift detection command
    drift_parser = subparsers.add_parser(
        "detect-drift",
        help="Detect configuration drift"
    )
    drift_parser.add_argument(
        "--format",
        choices=["text", "json", "html"],
        default="text",
        help="Output format"
    )
    drift_parser.add_argument(
        "--output",
        help="Output file path"
    )
    drift_parser.add_argument(
        "--auto-remediate",
        action="store_true",
        help="Automatically remediate drift"
    )

    # Cost estimation command
    cost_parser = subparsers.add_parser(
        "estimate-cost",
        help="Estimate infrastructure costs"
    )
    cost_parser.add_argument(
        "--format",
        choices=["text", "json", "html"],
        default="text",
        help="Output format"
    )
    cost_parser.add_argument(
        "--output",
        help="Output file path"
    )

    # Destroy command
    destroy_parser = subparsers.add_parser(
        "destroy",
        help="Destroy infrastructure"
    )
    destroy_parser.add_argument(
        "--auto-approve",
        action="store_true",
        help="Skip interactive approval"
    )
    destroy_parser.add_argument(
        "--var-file",
        help="Path to variable file"
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    # Initialize manager
    manager = IaCManager(config_file=args.config)
    manager.initialize(working_dir=args.directory)

    # Execute command
    try:
        if args.command == "provision":
            success = manager.provision(
                auto_approve=args.auto_approve,
                var_file=args.var_file
            )
        elif args.command == "validate":
            success = manager.validate_config(
                output_format=args.format,
                output_file=args.output
            )
        elif args.command == "detect-drift":
            success = manager.detect_drift(
                output_format=args.format,
                output_file=args.output,
                auto_remediate=args.auto_remediate
            )
        elif args.command == "estimate-cost":
            success = manager.estimate_cost(
                output_format=args.format,
                output_file=args.output
            )
        elif args.command == "destroy":
            success = manager.destroy(
                auto_approve=args.auto_approve,
                var_file=args.var_file
            )
        else:
            logger.error(f"Unknown command: {args.command}")
            return 1

        return 0 if success else 1

    except KeyboardInterrupt:
        logger.info("\nOperation cancelled by user")
        return 130
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
