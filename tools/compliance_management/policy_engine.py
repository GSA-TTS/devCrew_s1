"""
Policy Engine for OPA integration and policy evaluation.

Provides Rego policy compilation, caching, and evaluation capabilities.
Part of devCrew_s1 TOOL-SEC-011 compliance management platform.
"""

import hashlib
import json
import re
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional


class PolicyDecision(Enum):
    """Policy evaluation decision types."""

    ALLOW = "allow"
    DENY = "deny"
    PARTIAL = "partial"
    ERROR = "error"


@dataclass
class PolicyResult:
    """Result of a policy evaluation."""

    decision: PolicyDecision
    policy_name: str
    violations: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    evaluation_time_ms: float = 0.0
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary."""
        return {
            "decision": self.decision.value,
            "policy_name": self.policy_name,
            "violations": self.violations,
            "metadata": self.metadata,
            "evaluation_time_ms": self.evaluation_time_ms,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class CachedPolicy:
    """Cached compiled policy."""

    policy_hash: str
    compiled_rules: Dict[str, Any]
    created_at: datetime
    last_accessed: datetime
    access_count: int = 0


class PolicyCache:
    """Cache for compiled policies with TTL support."""

    def __init__(self, max_size: int = 100, ttl_seconds: int = 3600):
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self._cache: Dict[str, CachedPolicy] = {}

    def get(self, policy_hash: str) -> Optional[CachedPolicy]:
        """Get cached policy if exists and not expired."""
        if policy_hash not in self._cache:
            return None

        cached = self._cache[policy_hash]
        age = (datetime.utcnow() - cached.created_at).total_seconds()
        if age > self.ttl_seconds:
            del self._cache[policy_hash]
            return None

        cached.last_accessed = datetime.utcnow()
        cached.access_count += 1
        return cached

    def put(self, policy_hash: str, compiled_rules: Dict[str, Any]) -> None:
        """Store compiled policy in cache."""
        if len(self._cache) >= self.max_size:
            self._evict_oldest()

        self._cache[policy_hash] = CachedPolicy(
            policy_hash=policy_hash,
            compiled_rules=compiled_rules,
            created_at=datetime.utcnow(),
            last_accessed=datetime.utcnow(),
        )

    def _evict_oldest(self) -> None:
        """Evict least recently accessed policy."""
        if not self._cache:
            return
        oldest_key = min(
            self._cache.keys(), key=lambda k: self._cache[k].last_accessed
        )
        del self._cache[oldest_key]

    def clear(self) -> None:
        """Clear all cached policies."""
        self._cache.clear()

    @property
    def size(self) -> int:
        """Return current cache size."""
        return len(self._cache)


class PolicyEngine:
    """
    Policy engine for evaluating Rego policies.

    Provides policy compilation, caching, and evaluation with support
    for multiple compliance frameworks.
    """

    def __init__(self, cache: Optional[PolicyCache] = None):
        self.cache = cache or PolicyCache()
        self._policies: Dict[str, Dict[str, Any]] = {}
        self._builtin_rules = self._load_builtin_rules()

    def _load_builtin_rules(self) -> Dict[str, Any]:
        """Load built-in compliance rules."""
        return {
            "data_encryption": {
                "check": lambda d: d.get("encryption_enabled", False),
                "message": "Data must be encrypted at rest and in transit",
                "severity": "high",
            },
            "access_control": {
                "check": lambda d: d.get("access_controls", []) != [],
                "message": "Access controls must be defined",
                "severity": "high",
            },
            "audit_logging": {
                "check": lambda d: d.get("audit_logging_enabled", False),
                "message": "Audit logging must be enabled",
                "severity": "medium",
            },
            "data_retention": {
                "check": lambda d: d.get("retention_policy") is not None,
                "message": "Data retention policy must be defined",
                "severity": "medium",
            },
            "consent_management": {
                "check": lambda d: d.get("consent_obtained", False),
                "message": "User consent must be obtained for data processing",
                "severity": "high",
            },
            "data_minimization": {
                "check": lambda d: d.get("data_minimized", True),
                "message": "Only necessary data should be collected",
                "severity": "medium",
            },
            "breach_notification": {
                "check": lambda d: d.get("breach_notification_process", False),
                "message": "Breach notification process must be in place",
                "severity": "high",
            },
            "authentication": {
                "check": lambda d: d.get("mfa_enabled", False),
                "message": "Multi-factor authentication should be enabled",
                "severity": "high",
            },
            "network_security": {
                "check": lambda d: d.get("firewall_enabled", False),
                "message": "Network firewall must be enabled",
                "severity": "high",
            },
            "vulnerability_management": {
                "check": lambda d: d.get("vulnerability_scanning", False),
                "message": "Regular vulnerability scanning required",
                "severity": "medium",
            },
        }

    def _compute_hash(self, policy_content: str) -> str:
        """Compute hash of policy content."""
        return hashlib.sha256(policy_content.encode()).hexdigest()

    def compile_policy(self, policy_content: str, policy_name: str) -> Dict[str, Any]:
        """
        Compile a Rego policy into executable rules.

        Args:
            policy_content: Rego policy content
            policy_name: Name identifier for the policy

        Returns:
            Compiled policy rules
        """
        policy_hash = self._compute_hash(policy_content)

        cached = self.cache.get(policy_hash)
        if cached:
            return cached.compiled_rules

        compiled = self._parse_rego(policy_content, policy_name)
        self.cache.put(policy_hash, compiled)
        return compiled

    def _parse_rego(self, content: str, name: str) -> Dict[str, Any]:
        """Parse Rego policy content into rule structure."""
        rules: Dict[str, Any] = {
            "name": name,
            "package": "",
            "rules": [],
            "imports": [],
        }

        lines = content.strip().split("\n")
        current_rule: Optional[Dict[str, Any]] = None

        for line in lines:
            line = line.strip()

            if line.startswith("package "):
                rules["package"] = line.replace("package ", "").strip()
            elif line.startswith("import "):
                rules["imports"].append(line.replace("import ", "").strip())
            elif line.startswith("default "):
                match = re.match(r"default\s+(\w+)\s*=\s*(.+)", line)
                if match:
                    rules["rules"].append(
                        {
                            "name": match.group(1),
                            "default": match.group(2).strip(),
                            "conditions": [],
                        }
                    )
            elif re.match(r"^\w+\s*{", line) or re.match(r"^\w+\s*:=", line):
                rule_match = re.match(r"^(\w+)\s*[{:=]", line)
                if rule_match:
                    current_rule = {
                        "name": rule_match.group(1),
                        "body": line,
                        "conditions": [],
                    }
            elif current_rule and line and not line.startswith("#"):
                if line != "}":
                    current_rule["conditions"].append(line)
                else:
                    rules["rules"].append(current_rule)
                    current_rule = None

        return rules

    def load_policy(self, policy_path: Path) -> None:
        """Load policy from file."""
        if not policy_path.exists():
            raise FileNotFoundError(f"Policy file not found: {policy_path}")

        content = policy_path.read_text()
        policy_name = policy_path.stem
        compiled = self.compile_policy(content, policy_name)
        self._policies[policy_name] = compiled

    def load_policy_from_string(self, content: str, policy_name: str) -> None:
        """Load policy from string content."""
        compiled = self.compile_policy(content, policy_name)
        self._policies[policy_name] = compiled

    def evaluate(
        self, policy_name: str, input_data: Dict[str, Any]
    ) -> PolicyResult:
        """
        Evaluate input data against a policy.

        Args:
            policy_name: Name of policy to evaluate
            input_data: Data to evaluate against policy

        Returns:
            PolicyResult with decision and violations
        """
        start_time = time.time()

        if policy_name not in self._policies:
            return PolicyResult(
                decision=PolicyDecision.ERROR,
                policy_name=policy_name,
                violations=[{"message": f"Policy '{policy_name}' not found"}],
                evaluation_time_ms=(time.time() - start_time) * 1000,
            )

        policy = self._policies[policy_name]
        violations: List[Dict[str, Any]] = []

        for rule_name, rule_def in self._builtin_rules.items():
            if not rule_def["check"](input_data):
                violations.append(
                    {
                        "rule": rule_name,
                        "message": rule_def["message"],
                        "severity": rule_def["severity"],
                    }
                )

        decision = PolicyDecision.ALLOW if not violations else PolicyDecision.DENY

        return PolicyResult(
            decision=decision,
            policy_name=policy_name,
            violations=violations,
            metadata={"policy_package": policy.get("package", "")},
            evaluation_time_ms=(time.time() - start_time) * 1000,
        )

    def evaluate_with_rules(
        self, rules: List[str], input_data: Dict[str, Any]
    ) -> PolicyResult:
        """Evaluate input against specific rules."""
        start_time = time.time()
        violations: List[Dict[str, Any]] = []

        for rule_name in rules:
            if rule_name in self._builtin_rules:
                rule_def = self._builtin_rules[rule_name]
                if not rule_def["check"](input_data):
                    violations.append(
                        {
                            "rule": rule_name,
                            "message": rule_def["message"],
                            "severity": rule_def["severity"],
                        }
                    )

        decision = PolicyDecision.ALLOW if not violations else PolicyDecision.DENY

        return PolicyResult(
            decision=decision,
            policy_name="custom_rules",
            violations=violations,
            evaluation_time_ms=(time.time() - start_time) * 1000,
        )

    def get_available_rules(self) -> List[str]:
        """Get list of available built-in rules."""
        return list(self._builtin_rules.keys())

    def get_loaded_policies(self) -> List[str]:
        """Get list of loaded policy names."""
        return list(self._policies.keys())

    def export_policy_result(
        self, result: PolicyResult, output_path: Path
    ) -> None:
        """Export policy result to JSON file."""
        output_path.write_text(json.dumps(result.to_dict(), indent=2))
