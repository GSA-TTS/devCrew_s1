"""
Pattern Manager for secret detection patterns.

Provides 50+ built-in patterns for common secrets including AWS, Google,
GitHub, Slack, and private keys.
"""

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Pattern


class PatternSeverity(Enum):
    """Severity levels for secret patterns."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class SecretPattern:
    """Definition of a secret detection pattern."""

    name: str
    pattern: str
    severity: PatternSeverity
    description: str
    category: str
    keywords: List[str] = field(default_factory=list)
    entropy_threshold: Optional[float] = None
    compiled: Optional[Pattern] = field(default=None, repr=False)

    def __post_init__(self) -> None:
        """Compile the regex pattern."""
        self.compiled = re.compile(self.pattern, re.IGNORECASE | re.MULTILINE)


class PatternManager:
    """Manages secret detection patterns."""

    def __init__(self) -> None:
        """Initialize with built-in patterns."""
        self._patterns: Dict[str, SecretPattern] = {}
        self._custom_patterns: Dict[str, SecretPattern] = {}
        self._load_builtin_patterns()

    def _load_builtin_patterns(self) -> None:
        """Load all built-in secret patterns."""
        builtin = [
            # AWS Patterns (1-10)
            SecretPattern(
                name="aws_access_key_id",
                pattern=r"(?:A3T[A-Z0-9]|AKIA|AGPA|AIDA|AROA|AIPA|ANPA|ANVA|ASIA)[A-Z0-9]{16}",
                severity=PatternSeverity.CRITICAL,
                description="AWS Access Key ID",
                category="aws",
                keywords=["aws", "access", "key"],
            ),
            SecretPattern(
                name="aws_secret_access_key",
                pattern=r"(?i)aws[_\-\.]?secret[_\-\.]?access[_\-\.]?key['\"]?\s*[:=]\s*['\"]?([A-Za-z0-9/+=]{40})",
                severity=PatternSeverity.CRITICAL,
                description="AWS Secret Access Key",
                category="aws",
                keywords=["aws", "secret"],
            ),
            SecretPattern(
                name="aws_mws_auth_token",
                pattern=r"amzn\.mws\.[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
                severity=PatternSeverity.HIGH,
                description="AWS MWS Auth Token",
                category="aws",
                keywords=["amazon", "mws"],
            ),
            SecretPattern(
                name="aws_session_token",
                pattern=r"(?i)aws[_\-\.]?session[_\-\.]?token['\"]?\s*[:=]\s*['\"]?([A-Za-z0-9/+=]{100,})",
                severity=PatternSeverity.CRITICAL,
                description="AWS Session Token",
                category="aws",
                keywords=["aws", "session"],
            ),
            SecretPattern(
                name="aws_account_id",
                pattern=r"(?i)aws[_\-\.]?account[_\-\.]?id['\"]?\s*[:=]\s*['\"]?(\d{12})",
                severity=PatternSeverity.MEDIUM,
                description="AWS Account ID",
                category="aws",
                keywords=["aws", "account"],
            ),
            # GitHub Patterns (11-15)
            SecretPattern(
                name="github_token",
                pattern=r"gh[pousr]_[A-Za-z0-9_]{36,255}",
                severity=PatternSeverity.CRITICAL,
                description="GitHub Token (PAT, OAuth, etc.)",
                category="github",
                keywords=["github", "token"],
            ),
            SecretPattern(
                name="github_fine_grained_token",
                pattern=r"github_pat_[A-Za-z0-9_]{22}_[A-Za-z0-9]{59}",
                severity=PatternSeverity.CRITICAL,
                description="GitHub Fine-Grained Personal Access Token",
                category="github",
                keywords=["github", "pat"],
            ),
            SecretPattern(
                name="github_app_token",
                pattern=r"ghu_[A-Za-z0-9]{36}",
                severity=PatternSeverity.HIGH,
                description="GitHub App User-to-Server Token",
                category="github",
                keywords=["github", "app"],
            ),
            SecretPattern(
                name="github_refresh_token",
                pattern=r"ghr_[A-Za-z0-9]{36,255}",
                severity=PatternSeverity.HIGH,
                description="GitHub Refresh Token",
                category="github",
                keywords=["github", "refresh"],
            ),
            SecretPattern(
                name="github_oauth_secret",
                pattern=r"(?i)github[_\-\.]?client[_\-\.]?secret['\"]?\s*[:=]\s*['\"]?([a-f0-9]{40})",
                severity=PatternSeverity.CRITICAL,
                description="GitHub OAuth Client Secret",
                category="github",
                keywords=["github", "oauth"],
            ),
            # Google/GCP Patterns (16-22)
            SecretPattern(
                name="google_api_key",
                pattern=r"AIza[0-9A-Za-z\-_]{35}",
                severity=PatternSeverity.HIGH,
                description="Google API Key",
                category="google",
                keywords=["google", "api"],
            ),
            SecretPattern(
                name="google_oauth_client_id",
                pattern=r"[0-9]+-[a-z0-9_]{32}\.apps\.googleusercontent\.com",
                severity=PatternSeverity.MEDIUM,
                description="Google OAuth Client ID",
                category="google",
                keywords=["google", "oauth"],
            ),
            SecretPattern(
                name="google_oauth_secret",
                pattern=r"GOCSPX-[A-Za-z0-9\-_]{28}",
                severity=PatternSeverity.HIGH,
                description="Google OAuth Client Secret",
                category="google",
                keywords=["google", "oauth"],
            ),
            SecretPattern(
                name="google_service_account",
                pattern=r"\"type\":\s*\"service_account\"",
                severity=PatternSeverity.CRITICAL,
                description="Google Service Account JSON",
                category="google",
                keywords=["google", "service"],
            ),
            SecretPattern(
                name="gcp_api_key",
                pattern=r"(?i)gcp[_\-\.]?api[_\-\.]?key['\"]?\s*[:=]\s*['\"]?([A-Za-z0-9\-_]{39})",
                severity=PatternSeverity.HIGH,
                description="GCP API Key",
                category="google",
                keywords=["gcp", "api"],
            ),
            SecretPattern(
                name="firebase_api_key",
                pattern=r"(?i)firebase[_\-\.]?api[_\-\.]?key['\"]?\s*[:=]\s*['\"]?([A-Za-z0-9\-_]{39})",
                severity=PatternSeverity.HIGH,
                description="Firebase API Key",
                category="google",
                keywords=["firebase", "api"],
            ),
            SecretPattern(
                name="google_cloud_private_key",
                pattern=r"-----BEGIN RSA PRIVATE KEY-----",
                severity=PatternSeverity.CRITICAL,
                description="Google Cloud Private Key (RSA)",
                category="google",
                keywords=["private", "key", "rsa"],
            ),
            # Slack Patterns (23-27)
            SecretPattern(
                name="slack_token",
                pattern=r"xox[baprs]-[0-9]{10,13}-[0-9]{10,13}[a-zA-Z0-9-]*",
                severity=PatternSeverity.HIGH,
                description="Slack Token",
                category="slack",
                keywords=["slack", "token"],
            ),
            SecretPattern(
                name="slack_webhook",
                pattern=r"https://hooks\.slack\.com/services/T[a-zA-Z0-9_]{8,}/B[a-zA-Z0-9_]{8,}/[a-zA-Z0-9_]{24}",
                severity=PatternSeverity.HIGH,
                description="Slack Webhook URL",
                category="slack",
                keywords=["slack", "webhook"],
            ),
            SecretPattern(
                name="slack_bot_token",
                pattern=r"xoxb-[0-9]{11}-[0-9]{11}-[a-zA-Z0-9]{24}",
                severity=PatternSeverity.HIGH,
                description="Slack Bot Token",
                category="slack",
                keywords=["slack", "bot"],
            ),
            SecretPattern(
                name="slack_user_token",
                pattern=r"xoxp-[0-9]{11}-[0-9]{11}-[0-9]{11}-[a-f0-9]{32}",
                severity=PatternSeverity.HIGH,
                description="Slack User Token",
                category="slack",
                keywords=["slack", "user"],
            ),
            SecretPattern(
                name="slack_app_token",
                pattern=r"xapp-[0-9]-[A-Z0-9]+-[0-9]+-[a-z0-9]+",
                severity=PatternSeverity.HIGH,
                description="Slack App-Level Token",
                category="slack",
                keywords=["slack", "app"],
            ),
            # Private Keys (28-35)
            SecretPattern(
                name="private_key_rsa",
                pattern=r"-----BEGIN RSA PRIVATE KEY-----",
                severity=PatternSeverity.CRITICAL,
                description="RSA Private Key",
                category="keys",
                keywords=["private", "key", "rsa"],
            ),
            SecretPattern(
                name="private_key_openssh",
                pattern=r"-----BEGIN OPENSSH PRIVATE KEY-----",
                severity=PatternSeverity.CRITICAL,
                description="OpenSSH Private Key",
                category="keys",
                keywords=["private", "key", "openssh"],
            ),
            SecretPattern(
                name="private_key_dsa",
                pattern=r"-----BEGIN DSA PRIVATE KEY-----",
                severity=PatternSeverity.CRITICAL,
                description="DSA Private Key",
                category="keys",
                keywords=["private", "key", "dsa"],
            ),
            SecretPattern(
                name="private_key_ec",
                pattern=r"-----BEGIN EC PRIVATE KEY-----",
                severity=PatternSeverity.CRITICAL,
                description="EC Private Key",
                category="keys",
                keywords=["private", "key", "ec"],
            ),
            SecretPattern(
                name="private_key_pgp",
                pattern=r"-----BEGIN PGP PRIVATE KEY BLOCK-----",
                severity=PatternSeverity.CRITICAL,
                description="PGP Private Key",
                category="keys",
                keywords=["private", "key", "pgp"],
            ),
            SecretPattern(
                name="private_key_encrypted",
                pattern=r"-----BEGIN ENCRYPTED PRIVATE KEY-----",
                severity=PatternSeverity.HIGH,
                description="Encrypted Private Key",
                category="keys",
                keywords=["private", "key", "encrypted"],
            ),
            SecretPattern(
                name="certificate",
                pattern=r"-----BEGIN CERTIFICATE-----",
                severity=PatternSeverity.LOW,
                description="Certificate (may contain sensitive info)",
                category="keys",
                keywords=["certificate"],
            ),
            SecretPattern(
                name="pkcs8_private_key",
                pattern=r"-----BEGIN PRIVATE KEY-----",
                severity=PatternSeverity.CRITICAL,
                description="PKCS8 Private Key",
                category="keys",
                keywords=["private", "key", "pkcs8"],
            ),
            # Database Patterns (36-42)
            SecretPattern(
                name="postgres_uri",
                pattern=r"postgres(?:ql)?://[^:]+:[^@]+@[^/]+/[^\s]+",
                severity=PatternSeverity.CRITICAL,
                description="PostgreSQL Connection URI",
                category="database",
                keywords=["postgres", "database"],
            ),
            SecretPattern(
                name="mysql_uri",
                pattern=r"mysql://[^:]+:[^@]+@[^/]+/[^\s]+",
                severity=PatternSeverity.CRITICAL,
                description="MySQL Connection URI",
                category="database",
                keywords=["mysql", "database"],
            ),
            SecretPattern(
                name="mongodb_uri",
                pattern=r"mongodb(?:\+srv)?://[^:]+:[^@]+@[^\s]+",
                severity=PatternSeverity.CRITICAL,
                description="MongoDB Connection URI",
                category="database",
                keywords=["mongodb", "database"],
            ),
            SecretPattern(
                name="redis_uri",
                pattern=r"redis://[^:]*:[^@]+@[^\s]+",
                severity=PatternSeverity.HIGH,
                description="Redis Connection URI",
                category="database",
                keywords=["redis", "database"],
            ),
            SecretPattern(
                name="jdbc_connection",
                pattern=r"jdbc:[a-z]+://[^:]+:[^@]+@[^\s]+",
                severity=PatternSeverity.HIGH,
                description="JDBC Connection String",
                category="database",
                keywords=["jdbc", "database"],
            ),
            SecretPattern(
                name="db_password",
                pattern=r"(?i)(?:db|database)[_\-\.]?password['\"]?\s*[:=]\s*['\"]?([^'\"\s]{8,})",
                severity=PatternSeverity.HIGH,
                description="Database Password",
                category="database",
                keywords=["database", "password"],
            ),
            SecretPattern(
                name="connection_string",
                pattern=r"(?i)connection[_\-\.]?string['\"]?\s*[:=]\s*['\"]?([^'\"\n]{20,})",
                severity=PatternSeverity.HIGH,
                description="Generic Connection String",
                category="database",
                keywords=["connection", "string"],
            ),
            # API Keys & Tokens (43-55)
            SecretPattern(
                name="stripe_secret_key",
                pattern=r"sk_live_[0-9a-zA-Z]{24,}",
                severity=PatternSeverity.CRITICAL,
                description="Stripe Secret Key (Live)",
                category="payment",
                keywords=["stripe", "secret"],
            ),
            SecretPattern(
                name="stripe_test_key",
                pattern=r"sk_test_[0-9a-zA-Z]{24,}",
                severity=PatternSeverity.MEDIUM,
                description="Stripe Secret Key (Test)",
                category="payment",
                keywords=["stripe", "test"],
            ),
            SecretPattern(
                name="stripe_publishable_key",
                pattern=r"pk_(?:live|test)_[0-9a-zA-Z]{24,}",
                severity=PatternSeverity.LOW,
                description="Stripe Publishable Key",
                category="payment",
                keywords=["stripe", "publishable"],
            ),
            SecretPattern(
                name="paypal_client_secret",
                pattern=r"(?i)paypal[_\-\.]?(?:client[_\-\.]?)?secret['\"]?\s*[:=]\s*['\"]?([A-Za-z0-9\-_]{40,})",
                severity=PatternSeverity.CRITICAL,
                description="PayPal Client Secret",
                category="payment",
                keywords=["paypal", "secret"],
            ),
            SecretPattern(
                name="square_access_token",
                pattern=r"sq0atp-[0-9A-Za-z\-_]{22}",
                severity=PatternSeverity.CRITICAL,
                description="Square Access Token",
                category="payment",
                keywords=["square", "token"],
            ),
            SecretPattern(
                name="twilio_api_key",
                pattern=r"SK[0-9a-fA-F]{32}",
                severity=PatternSeverity.HIGH,
                description="Twilio API Key",
                category="communication",
                keywords=["twilio", "api"],
            ),
            SecretPattern(
                name="sendgrid_api_key",
                pattern=r"SG\.[a-zA-Z0-9_-]{22}\.[a-zA-Z0-9_-]{43}",
                severity=PatternSeverity.HIGH,
                description="SendGrid API Key",
                category="communication",
                keywords=["sendgrid", "api"],
            ),
            SecretPattern(
                name="mailchimp_api_key",
                pattern=r"[a-f0-9]{32}-us[0-9]{1,2}",
                severity=PatternSeverity.HIGH,
                description="Mailchimp API Key",
                category="communication",
                keywords=["mailchimp", "api"],
            ),
            SecretPattern(
                name="npm_token",
                pattern=r"npm_[A-Za-z0-9]{36}",
                severity=PatternSeverity.HIGH,
                description="NPM Access Token",
                category="package_registry",
                keywords=["npm", "token"],
            ),
            SecretPattern(
                name="pypi_token",
                pattern=r"pypi-[A-Za-z0-9_-]{100,}",
                severity=PatternSeverity.HIGH,
                description="PyPI API Token",
                category="package_registry",
                keywords=["pypi", "token"],
            ),
            SecretPattern(
                name="heroku_api_key",
                pattern=r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}",
                severity=PatternSeverity.MEDIUM,
                description="Heroku API Key (UUID format)",
                category="cloud",
                keywords=["heroku", "api"],
                entropy_threshold=3.5,
            ),
            SecretPattern(
                name="azure_client_secret",
                pattern=r"(?i)azure[_\-\.]?client[_\-\.]?secret['\"]?\s*[:=]\s*['\"]?([A-Za-z0-9~._-]{34,})",
                severity=PatternSeverity.CRITICAL,
                description="Azure Client Secret",
                category="cloud",
                keywords=["azure", "secret"],
            ),
            SecretPattern(
                name="digitalocean_token",
                pattern=r"dop_v1_[a-f0-9]{64}",
                severity=PatternSeverity.HIGH,
                description="DigitalOcean Personal Access Token",
                category="cloud",
                keywords=["digitalocean", "token"],
            ),
            # Generic Patterns (56-60)
            SecretPattern(
                name="generic_api_key",
                pattern=r"(?i)api[_\-\.]?key['\"]?\s*[:=]\s*['\"]?([a-zA-Z0-9_\-]{20,})",
                severity=PatternSeverity.MEDIUM,
                description="Generic API Key",
                category="generic",
                keywords=["api", "key"],
                entropy_threshold=3.5,
            ),
            SecretPattern(
                name="generic_secret",
                pattern=r"(?i)(?:secret|token|password|passwd|pwd)['\"]?\s*[:=]\s*['\"]?([^'\"\s]{8,})",
                severity=PatternSeverity.MEDIUM,
                description="Generic Secret/Token/Password",
                category="generic",
                keywords=["secret", "token", "password"],
                entropy_threshold=3.0,
            ),
            SecretPattern(
                name="bearer_token",
                pattern=r"(?i)bearer\s+[a-zA-Z0-9_\-\.=]+",
                severity=PatternSeverity.MEDIUM,
                description="Bearer Token",
                category="generic",
                keywords=["bearer", "token"],
            ),
            SecretPattern(
                name="basic_auth",
                pattern=r"(?i)basic\s+[a-zA-Z0-9+/=]{20,}",
                severity=PatternSeverity.MEDIUM,
                description="Basic Auth Credentials",
                category="generic",
                keywords=["basic", "auth"],
            ),
            SecretPattern(
                name="jwt_token",
                pattern=r"eyJ[A-Za-z0-9_-]*\.eyJ[A-Za-z0-9_-]*\.[A-Za-z0-9_-]*",
                severity=PatternSeverity.MEDIUM,
                description="JWT Token",
                category="generic",
                keywords=["jwt", "token"],
            ),
        ]

        for pattern in builtin:
            self._patterns[pattern.name] = pattern

    def get_all_patterns(self) -> List[SecretPattern]:
        """Get all patterns including custom ones."""
        all_patterns = list(self._patterns.values())
        all_patterns.extend(self._custom_patterns.values())
        return all_patterns

    def get_pattern(self, name: str) -> Optional[SecretPattern]:
        """Get a pattern by name."""
        return self._patterns.get(name) or self._custom_patterns.get(name)

    def get_patterns_by_category(self, category: str) -> List[SecretPattern]:
        """Get all patterns in a category."""
        return [p for p in self.get_all_patterns() if p.category == category]

    def get_patterns_by_severity(
        self, severity: PatternSeverity
    ) -> List[SecretPattern]:
        """Get all patterns with a given severity."""
        return [p for p in self.get_all_patterns() if p.severity == severity]

    def add_custom_pattern(self, pattern: SecretPattern) -> None:
        """Add a custom pattern."""
        self._custom_patterns[pattern.name] = pattern

    def remove_custom_pattern(self, name: str) -> bool:
        """Remove a custom pattern."""
        if name in self._custom_patterns:
            del self._custom_patterns[name]
            return True
        return False

    def get_categories(self) -> List[str]:
        """Get all unique categories."""
        return list({p.category for p in self.get_all_patterns()})

    def pattern_count(self) -> int:
        """Get total number of patterns."""
        return len(self._patterns) + len(self._custom_patterns)

    def export_patterns(self) -> List[Dict]:
        """Export all patterns as dictionaries."""
        return [
            {
                "name": p.name,
                "pattern": p.pattern,
                "severity": p.severity.value,
                "description": p.description,
                "category": p.category,
                "keywords": p.keywords,
                "entropy_threshold": p.entropy_threshold,
            }
            for p in self.get_all_patterns()
        ]

    def import_patterns(self, patterns: List[Dict]) -> int:
        """Import patterns from dictionaries."""
        count = 0
        for p in patterns:
            pattern = SecretPattern(
                name=p["name"],
                pattern=p["pattern"],
                severity=PatternSeverity(p["severity"]),
                description=p["description"],
                category=p["category"],
                keywords=p.get("keywords", []),
                entropy_threshold=p.get("entropy_threshold"),
            )
            self.add_custom_pattern(pattern)
            count += 1
        return count
