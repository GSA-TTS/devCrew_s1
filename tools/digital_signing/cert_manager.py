"""
Certificate Manager - X.509 certificate operations.

Provides certificate generation, CSR creation, chain validation,
and certificate lifecycle management using the cryptography library.
"""

from datetime import UTC, datetime, timedelta
from typing import List, Optional, Tuple

from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import ExtensionOID, NameOID


class CertificateManager:
    """Manage X.509 certificates and certificate operations."""

    def __init__(self):
        """Initialize certificate manager."""
        self.backend = default_backend()

    def generate_self_signed_cert(
        self,
        common_name: str,
        validity_days: int = 365,
        key_size: int = 2048,
        country: Optional[str] = None,
        state: Optional[str] = None,
        locality: Optional[str] = None,
        organization: Optional[str] = None,
        is_ca: bool = False,
    ) -> Tuple[str, str]:
        """
        Generate a self-signed X.509 certificate.

        Args:
            common_name: Common Name (CN) for certificate
            validity_days: Certificate validity in days
            key_size: RSA key size (2048, 3072, 4096)
            country: Country code (C)
            state: State or province (ST)
            locality: Locality or city (L)
            organization: Organization name (O)
            is_ca: Whether this is a CA certificate

        Returns:
            Tuple of (certificate PEM, private key PEM)
        """
        # Generate private key
        private_key = rsa.generate_private_key(
            public_exponent=65537, key_size=key_size, backend=self.backend
        )

        # Build subject name
        subject_attrs = [x509.NameAttribute(NameOID.COMMON_NAME, common_name)]
        if country:
            subject_attrs.append(x509.NameAttribute(NameOID.COUNTRY_NAME, country))
        if state:
            subject_attrs.append(
                x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, state)
            )
        if locality:
            subject_attrs.append(x509.NameAttribute(NameOID.LOCALITY_NAME, locality))
        if organization:
            subject_attrs.append(
                x509.NameAttribute(NameOID.ORGANIZATION_NAME, organization)
            )

        subject = x509.Name(subject_attrs)

        # Build certificate
        builder = (
            x509.CertificateBuilder()
            .subject_name(subject)
            .issuer_name(subject)  # Self-signed
            .public_key(private_key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(datetime.now(UTC))
            .not_valid_after(datetime.now(UTC) + timedelta(days=validity_days))
        )

        # Add extensions
        builder = builder.add_extension(
            x509.SubjectKeyIdentifier.from_public_key(private_key.public_key()),
            critical=False,
        )

        if is_ca:
            builder = builder.add_extension(
                x509.BasicConstraints(ca=True, path_length=None), critical=True
            )
            builder = builder.add_extension(
                x509.KeyUsage(
                    digital_signature=True,
                    key_cert_sign=True,
                    crl_sign=True,
                    key_encipherment=False,
                    content_commitment=False,
                    data_encipherment=False,
                    key_agreement=False,
                    encipher_only=False,
                    decipher_only=False,
                ),
                critical=True,
            )
        else:
            builder = builder.add_extension(
                x509.BasicConstraints(ca=False, path_length=None), critical=True
            )
            builder = builder.add_extension(
                x509.KeyUsage(
                    digital_signature=True,
                    key_encipherment=True,
                    key_cert_sign=False,
                    crl_sign=False,
                    content_commitment=False,
                    data_encipherment=False,
                    key_agreement=False,
                    encipher_only=False,
                    decipher_only=False,
                ),
                critical=True,
            )

        # Sign certificate
        certificate = builder.sign(private_key, hashes.SHA256(), self.backend)

        # Serialize certificate and key
        cert_pem = certificate.public_bytes(serialization.Encoding.PEM).decode("utf-8")
        key_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        ).decode("utf-8")

        return cert_pem, key_pem

    def generate_csr(
        self,
        common_name: str,
        key_size: int = 2048,
        country: Optional[str] = None,
        state: Optional[str] = None,
        locality: Optional[str] = None,
        organization: Optional[str] = None,
    ) -> Tuple[str, str]:
        """
        Generate a Certificate Signing Request (CSR).

        Args:
            common_name: Common Name (CN) for certificate
            key_size: RSA key size
            country: Country code (C)
            state: State or province (ST)
            locality: Locality or city (L)
            organization: Organization name (O)

        Returns:
            Tuple of (CSR PEM, private key PEM)
        """
        # Generate private key
        private_key = rsa.generate_private_key(
            public_exponent=65537, key_size=key_size, backend=self.backend
        )

        # Build subject name
        subject_attrs = [x509.NameAttribute(NameOID.COMMON_NAME, common_name)]
        if country:
            subject_attrs.append(x509.NameAttribute(NameOID.COUNTRY_NAME, country))
        if state:
            subject_attrs.append(
                x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, state)
            )
        if locality:
            subject_attrs.append(x509.NameAttribute(NameOID.LOCALITY_NAME, locality))
        if organization:
            subject_attrs.append(
                x509.NameAttribute(NameOID.ORGANIZATION_NAME, organization)
            )

        # Build CSR
        csr = (
            x509.CertificateSigningRequestBuilder()
            .subject_name(x509.Name(subject_attrs))
            .sign(private_key, hashes.SHA256(), self.backend)
        )

        # Serialize CSR and key
        csr_pem = csr.public_bytes(serialization.Encoding.PEM).decode("utf-8")
        key_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        ).decode("utf-8")

        return csr_pem, key_pem

    def sign_certificate(
        self,
        csr_pem: Optional[str],
        ca_cert_pem: str,
        ca_key_pem: str,
        validity_days: int = 365,
        common_name: Optional[str] = None,
        is_ca: bool = False,
    ) -> Tuple[str, str]:
        """
        Sign a certificate or CSR with a CA certificate.

        Args:
            csr_pem: CSR in PEM format (None to generate internally)
            ca_cert_pem: CA certificate PEM
            ca_key_pem: CA private key PEM
            validity_days: Certificate validity in days
            common_name: CN if generating internally
            is_ca: Whether signed cert is a CA

        Returns:
            Tuple of (signed certificate PEM, subject private key PEM)
        """
        # Load CA certificate and key
        ca_cert = x509.load_pem_x509_certificate(
            ca_cert_pem.encode("utf-8"), self.backend
        )
        ca_key = serialization.load_pem_private_key(
            ca_key_pem.encode("utf-8"), password=None, backend=self.backend
        )

        # Load or generate CSR
        if csr_pem:
            csr = x509.load_pem_x509_csr(csr_pem.encode("utf-8"), self.backend)
            subject_public_key = csr.public_key()
            subject_name = csr.subject
            subject_key = None
        else:
            # Generate new key pair
            subject_key = rsa.generate_private_key(
                public_exponent=65537, key_size=2048, backend=self.backend
            )
            subject_public_key = subject_key.public_key()
            subject_name = x509.Name(
                [x509.NameAttribute(NameOID.COMMON_NAME, common_name)]
            )

        # Build certificate
        builder = (
            x509.CertificateBuilder()
            .subject_name(subject_name)
            .issuer_name(ca_cert.subject)
            .public_key(subject_public_key)
            .serial_number(x509.random_serial_number())
            .not_valid_before(datetime.now(UTC))
            .not_valid_after(datetime.now(UTC) + timedelta(days=validity_days))
        )

        # Add extensions
        builder = builder.add_extension(
            x509.SubjectKeyIdentifier.from_public_key(subject_public_key),
            critical=False,
        )

        # Add authority key identifier
        try:
            ca_ski = ca_cert.extensions.get_extension_for_oid(
                ExtensionOID.SUBJECT_KEY_IDENTIFIER
            ).value
            builder = builder.add_extension(
                x509.AuthorityKeyIdentifier.from_issuer_subject_key_identifier(ca_ski),
                critical=False,
            )
        except x509.ExtensionNotFound:
            pass

        if is_ca:
            builder = builder.add_extension(
                x509.BasicConstraints(ca=True, path_length=0), critical=True
            )
        else:
            builder = builder.add_extension(
                x509.BasicConstraints(ca=False, path_length=None), critical=True
            )

        # Sign certificate
        certificate = builder.sign(ca_key, hashes.SHA256(), self.backend)

        # Serialize certificate
        cert_pem = certificate.public_bytes(serialization.Encoding.PEM).decode("utf-8")

        # Serialize subject key if generated
        if subject_key:
            key_pem = subject_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption(),
            ).decode("utf-8")
        else:
            key_pem = ""

        return cert_pem, key_pem

    def validate_chain(self, cert_chain_pems: List[str]) -> bool:
        """
        Validate a certificate chain.

        Args:
            cert_chain_pems: List of certificate PEMs (leaf to root)

        Returns:
            True if chain is valid
        """
        if not cert_chain_pems:
            return False

        try:
            # Load all certificates
            certs = [
                x509.load_pem_x509_certificate(pem.encode("utf-8"), self.backend)
                for pem in cert_chain_pems
            ]

            # Validate each certificate against its issuer
            for i in range(len(certs) - 1):
                cert = certs[i]
                issuer_cert = certs[i + 1]

                # Check if issuer name matches
                if cert.issuer != issuer_cert.subject:
                    return False

                # Verify signature
                try:
                    issuer_public_key = issuer_cert.public_key()
                    issuer_public_key.verify(
                        cert.signature,
                        cert.tbs_certificate_bytes,
                        cert.signature_algorithm_parameters,
                        cert.signature_hash_algorithm,
                    )
                except Exception:
                    return False

                # Check validity dates
                now = datetime.now(UTC)
                if not (cert.not_valid_before_utc <= now <= cert.not_valid_after_utc):
                    return False

            # Check root certificate is self-signed
            root = certs[-1]
            if root.issuer != root.subject:
                return False

            return True

        except Exception:
            return False

    def is_certificate_expired(self, cert_pem: str) -> bool:
        """
        Check if certificate is expired.

        Args:
            cert_pem: Certificate PEM

        Returns:
            True if expired
        """
        cert = x509.load_pem_x509_certificate(cert_pem.encode("utf-8"), self.backend)
        return datetime.now(UTC) > cert.not_valid_after_utc

    def days_until_expiry(self, cert_pem: str) -> int:
        """
        Calculate days until certificate expiration.

        Args:
            cert_pem: Certificate PEM

        Returns:
            Days until expiration (negative if expired)
        """
        cert = x509.load_pem_x509_certificate(cert_pem.encode("utf-8"), self.backend)
        delta = cert.not_valid_after_utc - datetime.now(UTC)
        return delta.days

    def get_certificate_info(self, cert_pem: str) -> dict:
        """
        Extract certificate information.

        Args:
            cert_pem: Certificate PEM

        Returns:
            Dictionary with certificate details
        """
        cert = x509.load_pem_x509_certificate(cert_pem.encode("utf-8"), self.backend)

        # Extract subject fields
        subject_fields = {}
        for attr in cert.subject:
            subject_fields[attr.oid._name] = attr.value

        # Extract issuer fields
        issuer_fields = {}
        for attr in cert.issuer:
            issuer_fields[attr.oid._name] = attr.value

        return {
            "subject": subject_fields,
            "issuer": issuer_fields,
            "serial_number": cert.serial_number,
            "not_valid_before": cert.not_valid_before.isoformat(),
            "not_valid_after": cert.not_valid_after.isoformat(),
            "is_ca": self._is_ca_certificate(cert),
            "signature_algorithm": cert.signature_algorithm_oid._name,
        }

    def _is_ca_certificate(self, cert: x509.Certificate) -> bool:
        """Check if certificate is a CA certificate."""
        try:
            basic_constraints = cert.extensions.get_extension_for_oid(
                ExtensionOID.BASIC_CONSTRAINTS
            ).value
            return basic_constraints.ca
        except x509.ExtensionNotFound:
            return False
