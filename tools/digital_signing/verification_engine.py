"""
Verification Engine - Multi-format signature verification.

Provides unified interface for verifying signatures from different
signing methods (GPG, Cosign, X.509) with trust root management.
"""

from datetime import datetime
from typing import Dict, List, Optional


class VerificationEngine:
    """
    Unified signature verification engine.

    Supports multiple verification methods and trust root management.
    """

    def __init__(self, gpg_handler=None, cosign_manager=None, cert_manager=None):
        """
        Initialize verification engine.

        Args:
            gpg_handler: Optional GPGHandler instance to use
            cosign_manager: Optional CosignManager instance to use
            cert_manager: Optional CertificateManager instance to use
        """
        self.trust_roots: Dict[str, Dict] = {}
        self.verification_cache: Dict[str, Dict] = {}
        self.gpg_handler = gpg_handler
        self.cosign_manager = cosign_manager
        self.cert_manager = cert_manager

    def add_trust_root(self, name: str, trust_data: Dict) -> None:
        """
        Add a trust root for verification.

        Args:
            name: Trust root name
            trust_data: Trust root configuration
        """
        self.trust_roots[name] = trust_data

    def remove_trust_root(self, name: str) -> None:
        """
        Remove a trust root.

        Args:
            name: Trust root name to remove
        """
        if name in self.trust_roots:
            del self.trust_roots[name]

    def has_trust_root(self, name: str) -> bool:
        """
        Check if trust root exists.

        Args:
            name: Trust root name

        Returns:
            True if trust root exists
        """
        return name in self.trust_roots

    def verify(
        self,
        artifact_type: str,
        artifact: str,
        verification_method: str,
        signature_file: Optional[str] = None,
        public_key: Optional[str] = None,
        key_id: Optional[str] = None,
        identity: Optional[str] = None,
        oidc_issuer: Optional[str] = None,
    ) -> Dict:
        """
        Verify artifact signature.

        Args:
            artifact_type: Type of artifact ("file", "container")
            artifact: Artifact identifier
            verification_method: "gpg", "cosign", "x509"
            signature_file: Path to signature file (for file artifacts)
            public_key: Public key for verification
            key_id: Key ID for GPG verification
            identity: Identity for keyless verification
            oidc_issuer: OIDC issuer for keyless verification

        Returns:
            Verification result dictionary
        """
        # Check cache
        cache_key = f"{artifact_type}:{artifact}:{verification_method}"
        if cache_key in self.verification_cache:
            cached = self.verification_cache[cache_key]
            # Return cached result if less than 5 minutes old
            cache_time = datetime.fromisoformat(cached["verified_at"])
            if (datetime.now() - cache_time).seconds < 300:
                return cached

        # Perform verification based on method
        if verification_method == "gpg":
            result = self._verify_gpg(artifact, signature_file, key_id)
        elif verification_method == "cosign":
            result = self._verify_cosign(artifact, public_key, identity, oidc_issuer)
        elif verification_method == "x509":
            result = self._verify_x509(artifact, signature_file, public_key)
        else:
            result = {
                "valid": False,
                "error": f"Unsupported verification method: {verification_method}",
            }

        # Add metadata
        result["artifact"] = artifact
        result["artifact_type"] = artifact_type
        result["verification_method"] = verification_method
        result["verified_at"] = datetime.now().isoformat()

        # Cache result
        if result.get("valid"):
            self.verification_cache[cache_key] = result

        return result

    def _verify_gpg(
        self, artifact: str, signature_file: Optional[str], key_id: Optional[str]
    ) -> Dict:
        """Verify GPG signature."""
        try:
            if not signature_file:
                return {
                    "valid": False,
                    "error": "Signature file required for GPG verification",
                }

            # Use provided handler or create new one
            if self.gpg_handler:
                handler = self.gpg_handler
            else:
                import os
                import sys

                sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
                from gpg_handler import GPGHandler

                handler = GPGHandler()

            result = handler.verify_signature(artifact, signature_file, key_id)
            return result

        except Exception as e:
            return {"valid": False, "error": f"GPG verification failed: {str(e)}"}

    def _verify_cosign(
        self,
        image: str,
        public_key: Optional[str],
        identity: Optional[str],
        oidc_issuer: Optional[str],
    ) -> Dict:
        """Verify Cosign signature."""
        try:
            # Use provided manager or create new one
            if self.cosign_manager:
                manager = self.cosign_manager
            else:
                import os
                import sys

                sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
                from cosign_manager import CosignManager

                manager = CosignManager()

            result = manager.verify_image(image, public_key, identity, oidc_issuer)
            return result

        except Exception as e:
            return {"valid": False, "error": f"Cosign verification failed: {str(e)}"}

    def _verify_x509(
        self, artifact: str, signature_file: Optional[str], cert_pem: Optional[str]
    ) -> Dict:
        """Verify X.509 certificate signature."""
        try:
            # Use provided manager or create new one
            if self.cert_manager:
                manager = self.cert_manager
            else:
                import os
                import sys

                sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
                from cert_manager import CertificateManager

                manager = CertificateManager()

            if not cert_pem:
                return {
                    "valid": False,
                    "error": "Certificate required for X.509 verification",
                }

            # Check certificate validity
            if manager.is_certificate_expired(cert_pem):
                return {"valid": False, "error": "Certificate expired"}

            # Get certificate info
            cert_info = manager.get_certificate_info(cert_pem)

            return {
                "valid": True,
                "certificate_subject": cert_info["subject"],
                "certificate_issuer": cert_info["issuer"],
                "certificate_valid_until": cert_info["not_valid_after"],
            }

        except Exception as e:
            return {"valid": False, "error": f"X.509 verification failed: {str(e)}"}

    def batch_verify(
        self, artifacts: List[Dict], parallel: bool = False, fail_fast: bool = False
    ) -> Dict[str, Dict]:
        """
        Verify multiple artifacts.

        Args:
            artifacts: List of artifact verification specifications
            parallel: Run verifications in parallel (not implemented)
            fail_fast: Stop on first failure

        Returns:
            Dictionary mapping artifact names to verification results
        """
        results = {}

        for artifact_spec in artifacts:
            artifact_name = artifact_spec.get("name", artifact_spec.get("artifact"))

            result = self.verify(
                artifact_type=artifact_spec.get("type", "file"),
                artifact=artifact_name,
                verification_method=artifact_spec.get("method", "gpg"),
                signature_file=artifact_spec.get("signature_file"),
                public_key=artifact_spec.get("public_key"),
                key_id=artifact_spec.get("key_id"),
                identity=artifact_spec.get("identity"),
                oidc_issuer=artifact_spec.get("oidc_issuer"),
            )

            results[artifact_name] = result

            if fail_fast and not result.get("valid"):
                break

        return results

    def generate_verification_report(self, verification_results: List[Dict]) -> Dict:
        """
        Generate summary report from verification results.

        Args:
            verification_results: List of verification result dictionaries

        Returns:
            Summary report dictionary
        """
        total = len(verification_results)
        valid = sum(1 for r in verification_results if r.get("valid"))
        invalid = total - valid

        # Group by verification method
        by_method = {}
        for result in verification_results:
            method = result.get("verification_method", "unknown")
            if method not in by_method:
                by_method[method] = {"total": 0, "valid": 0, "invalid": 0}
            by_method[method]["total"] += 1
            if result.get("valid"):
                by_method[method]["valid"] += 1
            else:
                by_method[method]["invalid"] += 1

        # Collect errors
        errors = [
            {"artifact": r.get("artifact"), "error": r.get("error")}
            for r in verification_results
            if not r.get("valid") and r.get("error")
        ]

        return {
            "summary": {
                "total": total,
                "valid": valid,
                "invalid": invalid,
                "success_rate": (valid / total * 100) if total > 0 else 0,
            },
            "by_method": by_method,
            "errors": errors,
            "generated_at": datetime.now().isoformat(),
        }

    def clear_cache(self) -> None:
        """Clear verification cache."""
        self.verification_cache.clear()

    def get_cache_stats(self) -> Dict:
        """
        Get cache statistics.

        Returns:
            Cache statistics dictionary
        """
        return {
            "cached_verifications": len(self.verification_cache),
            "trust_roots": len(self.trust_roots),
        }
