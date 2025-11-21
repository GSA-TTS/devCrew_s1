"""
Cosign Manager - Container image signing simulation.

Simulates Cosign operations for container image signing, verification,
and SLSA provenance generation without requiring actual Cosign binary.
"""

import hashlib
import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec, padding, rsa


class CosignManager:
    """
    Manage container image signing operations with Cosign simulation.

    Provides mock implementation for testing environments.
    """

    def __init__(self):
        """Initialize Cosign manager."""
        self.signatures: Dict[str, List[Dict]] = {}
        self.attestations: Dict[str, List[Dict]] = {}
        self.rekor_entries: Dict[str, Dict] = {}

    def generate_signing_key(
        self, algorithm: str = "ecdsa", key_size: int = 256
    ) -> str:
        """
        Generate a signing key for Cosign operations.

        Args:
            algorithm: "rsa" or "ecdsa"
            key_size: 256, 384, or 521 for ECDSA; 2048, 3072, 4096 for RSA

        Returns:
            Private key PEM
        """
        if algorithm == "ecdsa":
            curve_map = {256: ec.SECP256R1(), 384: ec.SECP384R1(), 521: ec.SECP521R1()}
            private_key = ec.generate_private_key(
                curve_map.get(key_size, ec.SECP256R1()), backend=default_backend()
            )
        else:  # rsa
            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=key_size if key_size >= 2048 else 2048,
                backend=default_backend(),
            )

        return private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        ).decode("utf-8")

    def sign_image(
        self, image: str, key_pem: str, annotations: Optional[Dict[str, str]] = None
    ) -> Dict:
        """
        Sign a container image with a private key.

        Args:
            image: Image reference (e.g., "myapp:1.2.3")
            key_pem: Private key in PEM format
            annotations: Optional annotations to include

        Returns:
            Signature result dictionary
        """
        # Load private key
        private_key = serialization.load_pem_private_key(
            key_pem.encode("utf-8"), password=None, backend=default_backend()
        )

        # Generate image digest (simulated)
        image_digest = hashlib.sha256(image.encode("utf-8")).hexdigest()

        # Create signature payload
        payload = {
            "critical": {
                "identity": {"docker-reference": image},
                "image": {"docker-manifest-digest": f"sha256:{image_digest}"},
                "type": "cosign container image signature",
            },
            "optional": annotations or {},
        }

        payload_bytes = json.dumps(payload, sort_keys=True).encode("utf-8")

        # Sign payload
        if isinstance(private_key, rsa.RSAPrivateKey):
            signature = private_key.sign(
                payload_bytes,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH,
                ),
                hashes.SHA256(),
            )
        else:  # ECDSA
            signature = private_key.sign(payload_bytes, ec.ECDSA(hashes.SHA256()))

        # Generate signature digest
        sig_digest = hashlib.sha256(signature).hexdigest()

        # Store signature
        if image not in self.signatures:
            self.signatures[image] = []

        sig_record = {
            "image": image,
            "signature": signature.hex(),
            "signature_digest": sig_digest,
            "payload": payload,
            "timestamp": datetime.now().isoformat(),
            "signer": "system",
        }

        self.signatures[image].append(sig_record)

        # Create mock Rekor entry
        rekor_entry_id = str(uuid.uuid4())
        self.rekor_entries[rekor_entry_id] = {
            "uuid": rekor_entry_id,
            "body": {
                "kind": "hashedrekord",
                "apiVersion": "0.0.1",
                "spec": {
                    "signature": {
                        "content": signature.hex(),
                        "publicKey": {"content": "mock_public_key"},
                    },
                    "data": {"hash": {"algorithm": "sha256", "value": sig_digest}},
                },
            },
            "integratedTime": int(datetime.now().timestamp()),
            "logIndex": len(self.rekor_entries),
        }

        return {
            "signed": True,
            "image": image,
            "signature_digest": sig_digest,
            "rekor_entry": (
                f"https://rekor.sigstore.dev/api/v1/log/entries/{rekor_entry_id}"
            ),
            "timestamp": sig_record["timestamp"],
        }

    def sign_image_keyless(self, image: str, identity: str, oidc_issuer: str) -> Dict:
        """
        Sign image using keyless (OIDC) workflow.

        Args:
            image: Image reference
            identity: Identity (email or URI)
            oidc_issuer: OIDC issuer URL

        Returns:
            Signature result dictionary
        """
        # Generate ephemeral key
        ephemeral_key = ec.generate_private_key(
            ec.SECP256R1(), backend=default_backend()
        )

        # Simulate Fulcio certificate issuance
        cert_subject = f"CN={identity}"

        # Generate image digest
        image_digest = hashlib.sha256(image.encode("utf-8")).hexdigest()

        # Create signature payload
        payload = {
            "critical": {
                "identity": {"docker-reference": image},
                "image": {"docker-manifest-digest": f"sha256:{image_digest}"},
                "type": "cosign container image signature",
            },
            "optional": {
                "oidcIssuer": oidc_issuer,
                "subject": identity,
            },
        }

        payload_bytes = json.dumps(payload, sort_keys=True).encode("utf-8")

        # Sign with ephemeral key
        signature = ephemeral_key.sign(payload_bytes, ec.ECDSA(hashes.SHA256()))

        sig_digest = hashlib.sha256(signature).hexdigest()

        # Store signature
        if image not in self.signatures:
            self.signatures[image] = []

        sig_record = {
            "image": image,
            "signature": signature.hex(),
            "signature_digest": sig_digest,
            "payload": payload,
            "timestamp": datetime.now().isoformat(),
            "signer": identity,
            "keyless": True,
            "certificate_subject": cert_subject,
            "oidc_issuer": oidc_issuer,
        }

        self.signatures[image].append(sig_record)

        # Create Rekor entry
        rekor_entry_id = str(uuid.uuid4())
        self.rekor_entries[rekor_entry_id] = {
            "uuid": rekor_entry_id,
            "body": {
                "kind": "hashedrekord",
                "apiVersion": "0.0.1",
                "spec": {
                    "signature": {
                        "content": signature.hex(),
                        "publicKey": {"content": cert_subject},
                    },
                    "data": {"hash": {"algorithm": "sha256", "value": sig_digest}},
                },
            },
            "integratedTime": int(datetime.now().timestamp()),
            "logIndex": len(self.rekor_entries),
        }

        return {
            "signed": True,
            "image": image,
            "signature_digest": sig_digest,
            "rekor_entry": (
                f"https://rekor.sigstore.dev/api/v1/log/entries/{rekor_entry_id}"
            ),
            "timestamp": sig_record["timestamp"],
            "identity": identity,
            "oidc_issuer": oidc_issuer,
        }

    def verify_image(
        self,
        image: str,
        public_key_pem: Optional[str] = None,
        identity: Optional[str] = None,
        oidc_issuer: Optional[str] = None,
    ) -> Dict:
        """
        Verify container image signature.

        Args:
            image: Image reference
            public_key_pem: Public key for key-based verification
            identity: Expected identity for keyless verification
            oidc_issuer: Expected OIDC issuer for keyless verification

        Returns:
            Verification result dictionary
        """
        if image not in self.signatures:
            return {"valid": False, "error": "No signatures found for image"}

        # Get latest signature
        sig_record = self.signatures[image][-1]

        # Keyless verification
        if identity and oidc_issuer:
            if sig_record.get("keyless"):
                if (
                    sig_record.get("signer") == identity
                    and sig_record.get("oidc_issuer") == oidc_issuer
                ):
                    return {
                        "valid": True,
                        "image": image,
                        "signer": identity,
                        "oidc_issuer": oidc_issuer,
                        "timestamp": sig_record["timestamp"],
                        "rekor_verified": True,
                    }
            return {"valid": False, "error": "Identity or OIDC issuer mismatch"}

        # Key-based verification (simplified)
        return {
            "valid": True,
            "image": image,
            "signer": sig_record.get("signer", "unknown"),
            "timestamp": sig_record["timestamp"],
            "signature_digest": sig_record["signature_digest"],
        }

    def generate_slsa_provenance(
        self,
        artifact: str,
        builder_id: str,
        build_type: str,
        materials: List[Dict],
        invocation_id: Optional[str] = None,
        build_config: Optional[Dict] = None,
    ) -> Dict:
        """
        Generate SLSA provenance document.

        Args:
            artifact: Artifact name
            builder_id: Builder identity URI
            build_type: Build type URI
            materials: List of input materials
            invocation_id: Build invocation ID
            build_config: Build configuration

        Returns:
            SLSA provenance document (in-toto format)
        """
        # Generate artifact digest
        artifact_digest = hashlib.sha256(artifact.encode("utf-8")).hexdigest()

        provenance = {
            "_type": "https://in-toto.io/Statement/v1",
            "subject": [{"name": artifact, "digest": {"sha256": artifact_digest}}],
            "predicateType": "https://slsa.dev/provenance/v1",
            "predicate": {
                "buildDefinition": {
                    "buildType": build_type,
                    "externalParameters": build_config or {},
                    "internalParameters": {
                        "timestamp": datetime.now().isoformat(),
                    },
                    "resolvedDependencies": materials,
                },
                "runDetails": {
                    "builder": {"id": builder_id},
                    "metadata": {
                        "invocationId": invocation_id or str(uuid.uuid4()),
                        "startedOn": datetime.now().isoformat(),
                        "finishedOn": datetime.now().isoformat(),
                    },
                },
            },
        }

        return provenance

    def sign_attestation(
        self,
        image: str,
        attestation: str,
        key_pem: str,
        attestation_type: str = "slsaprovenance",
    ) -> Dict:
        """
        Sign an attestation document.

        Args:
            image: Image reference
            attestation: Attestation JSON string
            key_pem: Private key PEM
            attestation_type: Type of attestation

        Returns:
            Signing result dictionary
        """
        # Load private key
        private_key = serialization.load_pem_private_key(
            key_pem.encode("utf-8"), password=None, backend=default_backend()
        )

        # Sign attestation
        attestation_bytes = attestation.encode("utf-8")

        if isinstance(private_key, rsa.RSAPrivateKey):
            signature = private_key.sign(
                attestation_bytes,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH,
                ),
                hashes.SHA256(),
            )
        else:  # ECDSA
            signature = private_key.sign(attestation_bytes, ec.ECDSA(hashes.SHA256()))

        sig_digest = hashlib.sha256(signature).hexdigest()

        # Store attestation
        if image not in self.attestations:
            self.attestations[image] = []

        attest_record = {
            "image": image,
            "attestation_type": attestation_type,
            "attestation": attestation,
            "signature": signature.hex(),
            "signature_digest": sig_digest,
            "timestamp": datetime.now().isoformat(),
        }

        self.attestations[image].append(attest_record)

        return {
            "signed": True,
            "image": image,
            "attestation_type": attestation_type,
            "signature_digest": sig_digest,
            "timestamp": attest_record["timestamp"],
        }

    def verify_attestation(
        self, image: str, attestation_type: str, policy: Optional[Dict] = None
    ) -> Dict:
        """
        Verify attestation for an image.

        Args:
            image: Image reference
            attestation_type: Type of attestation to verify
            policy: Policy rules to enforce

        Returns:
            Verification result dictionary
        """
        if image not in self.attestations:
            return {"valid": False, "error": "No attestations found"}

        # Find matching attestation
        matching = [
            a
            for a in self.attestations[image]
            if a["attestation_type"] == attestation_type
        ]

        if not matching:
            return {"valid": False, "error": f"No {attestation_type} attestation found"}

        attest_record = matching[-1]

        # Apply policy if provided
        if policy:
            attestation_data = json.loads(attest_record["attestation"])
            if "builder_id" in policy:
                predicate = attestation_data.get("predicate", {})
                run_details = predicate.get("runDetails", {})
                builder = run_details.get("builder", {})
                if builder.get("id") != policy["builder_id"]:
                    return {"valid": False, "error": "Builder ID policy violation"}

        return {
            "valid": True,
            "image": image,
            "attestation_type": attestation_type,
            "timestamp": attest_record["timestamp"],
        }

    def get_image_signatures(self, image: str) -> List[Dict]:
        """
        Get all signatures for an image.

        Args:
            image: Image reference

        Returns:
            List of signature records
        """
        return self.signatures.get(image, [])

    def get_image_attestations(self, image: str) -> List[Dict]:
        """
        Get all attestations for an image.

        Args:
            image: Image reference

        Returns:
            List of attestation records
        """
        return self.attestations.get(image, [])
