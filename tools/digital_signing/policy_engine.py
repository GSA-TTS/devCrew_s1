"""
Policy Engine - Policy-based signature verification.

Implements policy rules for signature verification, enforcement,
and compliance checking.
"""

import fnmatch
import json
from datetime import datetime
from typing import Dict, List, Optional


class PolicyEngine:
    """
    Manage and enforce signing policies.

    Supports pattern-based rules, multi-signature requirements,
    and policy compliance reporting.
    """

    def __init__(self, policy_file: Optional[str] = None):
        """
        Initialize policy engine.

        Args:
            policy_file: Optional path to policy configuration file
        """
        self.rules: List[Dict] = []
        self.exemptions: Dict[str, List[str]] = {}

        if policy_file:
            self.load_policies(policy_file)

    def add_rule(
        self,
        name: str,
        artifact_pattern: str,
        required_signers: List[str],
        min_signatures: int = 1,
        trust_root: Optional[str] = None,
        max_age_days: Optional[int] = None,
    ) -> None:
        """
        Add a policy rule.

        Args:
            name: Rule name
            artifact_pattern: Artifact pattern (supports wildcards)
            required_signers: List of required signer identities
            min_signatures: Minimum number of valid signatures required
            trust_root: Required trust root
            max_age_days: Maximum signature age in days
        """
        rule = {
            "name": name,
            "artifact_pattern": artifact_pattern,
            "required_signers": required_signers,
            "min_signatures": min_signatures,
            "trust_root": trust_root,
            "max_age_days": max_age_days,
            "created": datetime.now().isoformat(),
            "enabled": True,
        }

        self.rules.append(rule)

    def remove_rule(self, name: str) -> bool:
        """
        Remove a policy rule.

        Args:
            name: Rule name to remove

        Returns:
            True if rule was removed
        """
        original_length = len(self.rules)
        self.rules = [r for r in self.rules if r["name"] != name]
        return len(self.rules) < original_length

    def get_rules(self, enabled_only: bool = True) -> List[Dict]:
        """
        Get all policy rules.

        Args:
            enabled_only: Only return enabled rules

        Returns:
            List of rule dictionaries
        """
        if enabled_only:
            return [r for r in self.rules if r.get("enabled", True)]
        return self.rules

    def get_matching_rules(self, artifact: str) -> List[Dict]:
        """
        Get rules matching an artifact.

        Args:
            artifact: Artifact identifier

        Returns:
            List of matching rules
        """
        matching = []

        for rule in self.rules:
            if not rule.get("enabled", True):
                continue

            pattern = rule["artifact_pattern"]

            # Support glob patterns
            if fnmatch.fnmatch(artifact, pattern):
                matching.append(rule)

        return matching

    def evaluate(self, artifact: str, verification_results: List[Dict]) -> Dict:
        """
        Evaluate policy compliance for an artifact.

        Args:
            artifact: Artifact identifier
            verification_results: List of verification result dictionaries

        Returns:
            Policy evaluation result
        """
        # Get matching rules
        matching_rules = self.get_matching_rules(artifact)

        if not matching_rules:
            # No policies apply - allow by default
            return {
                "compliant": True,
                "artifact": artifact,
                "matched_rules": [],
                "violations": [],
                "evaluated_at": datetime.now().isoformat(),
            }

        # Check exemptions
        if self._has_exemption(artifact):
            return {
                "compliant": True,
                "artifact": artifact,
                "matched_rules": [r["name"] for r in matching_rules],
                "violations": [],
                "exempted": True,
                "evaluated_at": datetime.now().isoformat(),
            }

        violations = []

        # Evaluate each rule
        for rule in matching_rules:
            rule_violations = self._evaluate_rule(rule, artifact, verification_results)
            violations.extend(rule_violations)

        return {
            "compliant": len(violations) == 0,
            "artifact": artifact,
            "matched_rules": [r["name"] for r in matching_rules],
            "violations": violations,
            "evaluated_at": datetime.now().isoformat(),
        }

    def _evaluate_rule(
        self, rule: Dict, artifact: str, verification_results: List[Dict]
    ) -> List[Dict]:
        """Evaluate a single rule."""
        violations = []

        # Filter valid verification results
        valid_results = [r for r in verification_results if r.get("valid")]

        # Check minimum signatures
        min_sigs = rule["min_signatures"]
        if len(valid_results) < min_sigs:
            violations.append(
                {
                    "rule": rule["name"],
                    "type": "insufficient_signatures",
                    "message": (
                        f"Required {min_sigs} signatures, "
                        f"found {len(valid_results)}"
                    ),
                    "severity": "critical",
                }
            )

        # Check required signers
        required_signers = rule["required_signers"]
        found_signers = set()

        for result in valid_results:
            signer = result.get("signer")
            if signer:
                found_signers.add(signer)

        missing_signers = set(required_signers) - found_signers

        if missing_signers:
            violations.append(
                {
                    "rule": rule["name"],
                    "type": "missing_required_signers",
                    "message": f"Missing signatures from: {', '.join(missing_signers)}",
                    "severity": "critical",
                }
            )

        # Check signature age
        max_age_days = rule.get("max_age_days")
        if max_age_days:
            for result in valid_results:
                timestamp = result.get("timestamp")
                if timestamp:
                    sig_time = datetime.fromisoformat(timestamp)
                    age_days = (datetime.now() - sig_time).days

                    if age_days > max_age_days:
                        violations.append(
                            {
                                "rule": rule["name"],
                                "type": "signature_too_old",
                                "message": (
                                    f"Signature is {age_days} days old "
                                    f"(max: {max_age_days})"
                                ),
                                "severity": "warning",
                                "signer": result.get("signer"),
                            }
                        )

        # Check trust root
        trust_root = rule.get("trust_root")
        if trust_root:
            for result in valid_results:
                result_trust_root = result.get("trust_root")
                if result_trust_root and result_trust_root != trust_root:
                    violations.append(
                        {
                            "rule": rule["name"],
                            "type": "invalid_trust_root",
                            "message": (
                                f"Expected trust root '{trust_root}', "
                                f"got '{result_trust_root}'"
                            ),
                            "severity": "critical",
                        }
                    )

        return violations

    def add_exemption(self, artifact: str, reason: str, expiry_days: int = 30) -> None:
        """
        Add policy exemption for an artifact.

        Args:
            artifact: Artifact identifier
            reason: Exemption reason
            expiry_days: Days until exemption expires
        """
        from datetime import timedelta

        expiry = datetime.now() + timedelta(days=expiry_days)

        if artifact not in self.exemptions:
            self.exemptions[artifact] = []

        self.exemptions[artifact].append(
            {
                "reason": reason,
                "created": datetime.now().isoformat(),
                "expires": expiry.isoformat(),
            }
        )

    def remove_exemption(self, artifact: str) -> None:
        """
        Remove policy exemption for an artifact.

        Args:
            artifact: Artifact identifier
        """
        if artifact in self.exemptions:
            del self.exemptions[artifact]

    def _has_exemption(self, artifact: str) -> bool:
        """Check if artifact has valid exemption."""
        if artifact not in self.exemptions:
            return False

        # Check if any exemptions are still valid
        now = datetime.now()
        valid_exemptions = []

        for exemption in self.exemptions[artifact]:
            expiry = datetime.fromisoformat(exemption["expires"])
            if now < expiry:
                valid_exemptions.append(exemption)

        # Update exemptions list
        if valid_exemptions:
            self.exemptions[artifact] = valid_exemptions
            return True
        else:
            del self.exemptions[artifact]
            return False

    def enable_rule(self, name: str) -> bool:
        """
        Enable a policy rule.

        Args:
            name: Rule name

        Returns:
            True if rule was found and enabled
        """
        for rule in self.rules:
            if rule["name"] == name:
                rule["enabled"] = True
                return True
        return False

    def disable_rule(self, name: str) -> bool:
        """
        Disable a policy rule.

        Args:
            name: Rule name

        Returns:
            True if rule was found and disabled
        """
        for rule in self.rules:
            if rule["name"] == name:
                rule["enabled"] = False
                return True
        return False

    def load_policies(self, policy_file: str) -> None:
        """
        Load policies from file.

        Args:
            policy_file: Path to policy JSON file
        """
        with open(policy_file, "r") as f:
            data = json.load(f)

        if "rules" in data:
            self.rules = data["rules"]

        if "exemptions" in data:
            self.exemptions = data["exemptions"]

    def save_policies(self, policy_file: str) -> None:
        """
        Save policies to file.

        Args:
            policy_file: Path to policy JSON file
        """
        data = {"rules": self.rules, "exemptions": self.exemptions}

        with open(policy_file, "w") as f:
            json.dump(data, f, indent=2)

    def get_policy_stats(self) -> Dict:
        """
        Get policy statistics.

        Returns:
            Statistics dictionary
        """
        enabled_rules = len([r for r in self.rules if r.get("enabled", True)])
        disabled_rules = len(self.rules) - enabled_rules

        active_exemptions = sum(
            1 for exs in self.exemptions.values() if self._has_exemption(exs)
        )

        return {
            "total_rules": len(self.rules),
            "enabled_rules": enabled_rules,
            "disabled_rules": disabled_rules,
            "active_exemptions": active_exemptions,
        }

    def validate_policy_config(self) -> List[str]:
        """
        Validate policy configuration.

        Returns:
            List of validation errors
        """
        errors = []

        for i, rule in enumerate(self.rules):
            # Check required fields
            if "name" not in rule:
                errors.append(f"Rule {i}: Missing 'name' field")

            if "artifact_pattern" not in rule:
                errors.append(f"Rule {i}: Missing 'artifact_pattern' field")

            if "required_signers" not in rule:
                errors.append(f"Rule {i}: Missing 'required_signers' field")

            # Validate min_signatures
            min_sigs = rule.get("min_signatures", 1)
            if min_sigs < 1:
                errors.append(
                    f"Rule {rule.get('name', i)}: min_signatures must be >= 1"
                )

            # Check for duplicate rule names
            names = [r["name"] for r in self.rules]
            if names.count(rule.get("name")) > 1:
                errors.append(f"Duplicate rule name: {rule.get('name')}")

        return errors
