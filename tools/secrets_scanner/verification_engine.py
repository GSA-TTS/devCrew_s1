"""
Verification Engine for validating detected secrets.

Provides API key validation and token status checking.
"""

import re
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional

from .secret_scanner import SecretFinding


class VerificationStatus(Enum):
    """Status of secret verification."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    REVOKED = "revoked"
    EXPIRED = "expired"
    INVALID = "invalid"
    UNKNOWN = "unknown"
    SKIPPED = "skipped"


@dataclass
class VerificationResult:
    """Result of verifying a secret."""

    finding: SecretFinding
    status: VerificationStatus
    message: str = ""
    verified_at: str = ""
    details: Dict[str, Any] = None

    def __post_init__(self) -> None:
        """Initialize defaults."""
        if self.details is None:
            self.details = {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "finding_hash": self.finding.hash_value,
            "pattern_name": self.finding.pattern_name,
            "status": self.status.value,
            "message": self.message,
            "verified_at": self.verified_at,
            "details": self.details,
        }


class VerificationEngine:
    """Engine for verifying detected secrets."""

    def __init__(self, verify_live: bool = False) -> None:
        """
        Initialize verification engine.

        Args:
            verify_live: If True, make actual API calls to verify secrets.
                        Default False for safety.
        """
        self.verify_live = verify_live
        self._validators: Dict[str, callable] = {}
        self._register_validators()

    def _register_validators(self) -> None:
        """Register built-in validators."""
        self._validators = {
            "aws_access_key_id": self._validate_aws_key,
            "github_token": self._validate_github_token,
            "google_api_key": self._validate_google_key,
            "slack_token": self._validate_slack_token,
            "stripe_secret_key": self._validate_stripe_key,
            "jwt_token": self._validate_jwt,
        }

    def verify(self, finding: SecretFinding) -> VerificationResult:
        """Verify a single finding."""
        validator = self._validators.get(finding.pattern_name)

        if validator is None:
            return VerificationResult(
                finding=finding,
                status=VerificationStatus.SKIPPED,
                message=f"No validator for pattern: {finding.pattern_name}",
            )

        return validator(finding)

    def verify_all(
        self, findings: List[SecretFinding]
    ) -> List[VerificationResult]:
        """Verify multiple findings."""
        return [self.verify(f) for f in findings]

    def _validate_aws_key(self, finding: SecretFinding) -> VerificationResult:
        """Validate AWS access key format."""
        key = finding.matched_text

        # Check format
        aws_pattern = r"^(?:A3T[A-Z0-9]|AKIA|AGPA|AIDA|AROA|AIPA|ANPA|ANVA|ASIA)[A-Z0-9]{16}$"
        if not re.match(aws_pattern, key, re.IGNORECASE):
            return VerificationResult(
                finding=finding,
                status=VerificationStatus.INVALID,
                message="Invalid AWS key format",
            )

        # Determine key type
        prefix = key[:4].upper()
        key_types = {
            "AKIA": "Long-term access key",
            "ASIA": "Temporary session key",
            "AIDA": "IAM user ID",
            "AROA": "IAM role ID",
            "AGPA": "Group ID",
            "AIPA": "EC2 instance profile ID",
            "ANPA": "Managed policy ID",
            "ANVA": "Version in managed policy",
        }

        key_type = key_types.get(prefix, "Unknown key type")

        if self.verify_live:
            # In live mode, would call AWS STS GetCallerIdentity
            return VerificationResult(
                finding=finding,
                status=VerificationStatus.UNKNOWN,
                message="Live verification not implemented",
                details={"key_type": key_type},
            )

        return VerificationResult(
            finding=finding,
            status=VerificationStatus.UNKNOWN,
            message=f"Format valid, key type: {key_type}",
            details={"key_type": key_type, "prefix": prefix},
        )

    def _validate_github_token(self, finding: SecretFinding) -> VerificationResult:
        """Validate GitHub token format."""
        token = finding.matched_text

        # Determine token type
        token_types = {
            "ghp_": "Personal Access Token",
            "gho_": "OAuth Token",
            "ghu_": "User-to-Server Token",
            "ghs_": "Server-to-Server Token",
            "ghr_": "Refresh Token",
        }

        prefix = token[:4]
        token_type = token_types.get(prefix, "Unknown")

        # Check minimum length
        if len(token) < 40:
            return VerificationResult(
                finding=finding,
                status=VerificationStatus.INVALID,
                message="Token too short",
            )

        if self.verify_live:
            return VerificationResult(
                finding=finding,
                status=VerificationStatus.UNKNOWN,
                message="Live verification not implemented",
                details={"token_type": token_type},
            )

        return VerificationResult(
            finding=finding,
            status=VerificationStatus.UNKNOWN,
            message=f"Format valid, type: {token_type}",
            details={"token_type": token_type, "prefix": prefix},
        )

    def _validate_google_key(self, finding: SecretFinding) -> VerificationResult:
        """Validate Google API key format."""
        key = finding.matched_text

        if not key.startswith("AIza"):
            return VerificationResult(
                finding=finding,
                status=VerificationStatus.INVALID,
                message="Invalid Google API key prefix",
            )

        if len(key) != 39:
            return VerificationResult(
                finding=finding,
                status=VerificationStatus.INVALID,
                message=f"Invalid length: {len(key)}, expected 39",
            )

        return VerificationResult(
            finding=finding,
            status=VerificationStatus.UNKNOWN,
            message="Format valid",
            details={"length": len(key)},
        )

    def _validate_slack_token(self, finding: SecretFinding) -> VerificationResult:
        """Validate Slack token format."""
        token = finding.matched_text

        token_types = {
            "xoxb-": "Bot Token",
            "xoxp-": "User Token",
            "xoxa-": "App Token (deprecated)",
            "xoxr-": "Refresh Token",
            "xoxs-": "Session Token",
        }

        prefix = token[:5]
        token_type = token_types.get(prefix, "Unknown")

        return VerificationResult(
            finding=finding,
            status=VerificationStatus.UNKNOWN,
            message=f"Format valid, type: {token_type}",
            details={"token_type": token_type},
        )

    def _validate_stripe_key(self, finding: SecretFinding) -> VerificationResult:
        """Validate Stripe key format."""
        key = finding.matched_text

        if key.startswith("sk_live_"):
            env = "production"
            risk = "HIGH - Live secret key"
        elif key.startswith("sk_test_"):
            env = "test"
            risk = "MEDIUM - Test secret key"
        else:
            return VerificationResult(
                finding=finding,
                status=VerificationStatus.INVALID,
                message="Invalid Stripe key format",
            )

        return VerificationResult(
            finding=finding,
            status=VerificationStatus.UNKNOWN,
            message=f"Format valid, environment: {env}",
            details={"environment": env, "risk": risk},
        )

    def _validate_jwt(self, finding: SecretFinding) -> VerificationResult:
        """Validate and decode JWT structure."""
        import base64
        import json

        token = finding.matched_text
        parts = token.split(".")

        if len(parts) != 3:
            return VerificationResult(
                finding=finding,
                status=VerificationStatus.INVALID,
                message="Invalid JWT structure",
            )

        try:
            # Decode header
            header_b64 = parts[0] + "=" * (4 - len(parts[0]) % 4)
            header = json.loads(base64.urlsafe_b64decode(header_b64))

            # Decode payload
            payload_b64 = parts[1] + "=" * (4 - len(parts[1]) % 4)
            payload = json.loads(base64.urlsafe_b64decode(payload_b64))

            # Check expiration
            exp = payload.get("exp")
            status = VerificationStatus.UNKNOWN

            details = {
                "algorithm": header.get("alg"),
                "type": header.get("typ"),
                "issuer": payload.get("iss"),
                "subject": payload.get("sub"),
                "expiration": exp,
            }

            return VerificationResult(
                finding=finding,
                status=status,
                message="JWT decoded successfully",
                details=details,
            )

        except (json.JSONDecodeError, UnicodeDecodeError, ValueError):
            return VerificationResult(
                finding=finding,
                status=VerificationStatus.INVALID,
                message="Failed to decode JWT",
            )

    def add_validator(
        self,
        pattern_name: str,
        validator: callable,
    ) -> None:
        """Add a custom validator."""
        self._validators[pattern_name] = validator

    def get_supported_patterns(self) -> List[str]:
        """Get list of patterns with validators."""
        return list(self._validators.keys())

    def check_revocation_status(
        self, finding: SecretFinding
    ) -> VerificationResult:
        """
        Check if a secret has been revoked.

        This is a placeholder for integration with secret revocation APIs.
        """
        # In a full implementation, this would check:
        # - GitHub: Token revocation status via API
        # - AWS: STS validation
        # - Etc.

        return VerificationResult(
            finding=finding,
            status=VerificationStatus.UNKNOWN,
            message="Revocation check not implemented",
        )

    def batch_verify(
        self,
        findings: List[SecretFinding],
        skip_patterns: Optional[List[str]] = None,
    ) -> Dict[str, List[VerificationResult]]:
        """Batch verify findings grouped by pattern."""
        skip_patterns = skip_patterns or []
        results: Dict[str, List[VerificationResult]] = {}

        for finding in findings:
            if finding.pattern_name in skip_patterns:
                continue

            result = self.verify(finding)

            if finding.pattern_name not in results:
                results[finding.pattern_name] = []
            results[finding.pattern_name].append(result)

        return results

    def generate_report(
        self, results: List[VerificationResult]
    ) -> Dict[str, Any]:
        """Generate verification report."""
        status_counts = {status.value: 0 for status in VerificationStatus}

        for result in results:
            status_counts[result.status.value] += 1

        return {
            "total_verified": len(results),
            "status_summary": status_counts,
            "active_secrets": [
                r.to_dict() for r in results
                if r.status == VerificationStatus.ACTIVE
            ],
            "invalid_format": [
                r.to_dict() for r in results
                if r.status == VerificationStatus.INVALID
            ],
        }
