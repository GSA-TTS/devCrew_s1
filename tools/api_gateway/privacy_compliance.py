"""
Issue #41: Privacy Compliance Module
Implements PII detection, GDPR compliance, and data anonymization.
"""

import hashlib
import re
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set

import phonenumbers
from email_validator import EmailNotValidError, validate_email
from pydantic import BaseModel, Field


class PIIType(str, Enum):
    """Types of Personally Identifiable Information."""

    EMAIL = "email"
    PHONE = "phone"
    SSN = "ssn"
    CREDIT_CARD = "credit_card"
    IP_ADDRESS = "ip_address"
    NAME = "name"
    ADDRESS = "address"
    DATE_OF_BIRTH = "date_of_birth"
    DRIVERS_LICENSE = "drivers_license"
    PASSPORT = "passport"


class ConsentType(str, Enum):
    """Types of consent."""

    MARKETING = "marketing"
    DATA_PROCESSING = "data_processing"
    DATA_SHARING = "data_sharing"
    ANALYTICS = "analytics"
    PROFILING = "profiling"


class ConsentStatus(str, Enum):
    """Consent status."""

    GRANTED = "granted"
    DENIED = "denied"
    PENDING = "pending"
    REVOKED = "revoked"


class PIIField(BaseModel):
    """PII field detection result."""

    field_name: str
    pii_type: PIIType
    value: str
    confidence: float = Field(..., ge=0.0, le=1.0)


class ConsentRecord(BaseModel):
    """Consent record."""

    customer_id: str
    consent_type: ConsentType
    status: ConsentStatus
    granted_at: Optional[datetime] = None
    revoked_at: Optional[datetime] = None
    ip_address: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class PIIDetector:
    """Detect PII in text and data structures."""

    # Regular expressions for PII detection
    EMAIL_PATTERN = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b")
    SSN_PATTERN = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
    CREDIT_CARD_PATTERN = re.compile(r"\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b")
    IP_ADDRESS_PATTERN = re.compile(
        r"\b(?:\d{1,3}\.){3}\d{1,3}\b"
    )

    @staticmethod
    def is_valid_email(text: str) -> bool:
        """
        Check if text is a valid email.

        Args:
            text: Text to check

        Returns:
            True if valid email, False otherwise
        """
        try:
            validate_email(text, check_deliverability=False)
            return True
        except EmailNotValidError:
            return False

    @staticmethod
    def is_valid_phone(text: str) -> bool:
        """
        Check if text is a valid phone number.

        Args:
            text: Text to check

        Returns:
            True if valid phone, False otherwise
        """
        try:
            parsed = phonenumbers.parse(text, None)
            return phonenumbers.is_valid_number(parsed)
        except phonenumbers.NumberParseException:
            return False

    @staticmethod
    def is_valid_ssn(text: str) -> bool:
        """
        Check if text is a valid SSN.

        Args:
            text: Text to check

        Returns:
            True if valid SSN, False otherwise
        """
        return bool(PIIDetector.SSN_PATTERN.match(text))

    @staticmethod
    def is_valid_credit_card(text: str) -> bool:
        """
        Check if text is a valid credit card using Luhn algorithm.

        Args:
            text: Text to check

        Returns:
            True if valid credit card, False otherwise
        """
        # Remove spaces and dashes
        digits = re.sub(r"[- ]", "", text)

        if not digits.isdigit() or len(digits) < 13 or len(digits) > 19:
            return False

        # Luhn algorithm
        total = 0
        for i, digit in enumerate(reversed(digits)):
            n = int(digit)
            if i % 2 == 1:
                n *= 2
                if n > 9:
                    n -= 9
            total += n

        return total % 10 == 0

    def detect_pii_in_text(self, text: str) -> List[PIIField]:
        """
        Detect PII in text.

        Args:
            text: Text to analyze

        Returns:
            List of detected PII fields
        """
        detected_pii: List[PIIField] = []

        # Detect emails
        for match in self.EMAIL_PATTERN.finditer(text):
            email = match.group()
            if self.is_valid_email(email):
                detected_pii.append(
                    PIIField(
                        field_name="email",
                        pii_type=PIIType.EMAIL,
                        value=email,
                        confidence=1.0,
                    )
                )

        # Detect SSNs
        for match in self.SSN_PATTERN.finditer(text):
            ssn = match.group()
            if self.is_valid_ssn(ssn):
                detected_pii.append(
                    PIIField(
                        field_name="ssn",
                        pii_type=PIIType.SSN,
                        value=ssn,
                        confidence=0.95,
                    )
                )

        # Detect credit cards
        for match in self.CREDIT_CARD_PATTERN.finditer(text):
            cc = match.group()
            if self.is_valid_credit_card(cc):
                detected_pii.append(
                    PIIField(
                        field_name="credit_card",
                        pii_type=PIIType.CREDIT_CARD,
                        value=cc,
                        confidence=0.9,
                    )
                )

        # Detect IP addresses
        for match in self.IP_ADDRESS_PATTERN.finditer(text):
            ip = match.group()
            detected_pii.append(
                PIIField(
                    field_name="ip_address",
                    pii_type=PIIType.IP_ADDRESS,
                    value=ip,
                    confidence=0.8,
                )
            )

        return detected_pii

    def detect_pii_in_dict(self, data: Dict[str, Any]) -> List[PIIField]:
        """
        Detect PII in dictionary.

        Args:
            data: Dictionary to analyze

        Returns:
            List of detected PII fields
        """
        detected_pii: List[PIIField] = []

        # Common PII field names
        email_fields = {"email", "e_mail", "email_address", "user_email"}
        phone_fields = {"phone", "phone_number", "mobile", "tel", "telephone"}
        ssn_fields = {"ssn", "social_security_number", "social_security"}
        name_fields = {"name", "full_name", "first_name", "last_name"}
        dob_fields = {"dob", "date_of_birth", "birth_date", "birthdate"}

        for key, value in data.items():
            if not isinstance(value, str):
                continue

            key_lower = key.lower()

            # Check email fields
            if key_lower in email_fields and self.is_valid_email(value):
                detected_pii.append(
                    PIIField(
                        field_name=key,
                        pii_type=PIIType.EMAIL,
                        value=value,
                        confidence=1.0,
                    )
                )

            # Check phone fields
            elif key_lower in phone_fields and self.is_valid_phone(value):
                detected_pii.append(
                    PIIField(
                        field_name=key,
                        pii_type=PIIType.PHONE,
                        value=value,
                        confidence=1.0,
                    )
                )

            # Check SSN fields
            elif key_lower in ssn_fields and self.is_valid_ssn(value):
                detected_pii.append(
                    PIIField(
                        field_name=key,
                        pii_type=PIIType.SSN,
                        value=value,
                        confidence=1.0,
                    )
                )

            # Check name fields
            elif key_lower in name_fields:
                detected_pii.append(
                    PIIField(
                        field_name=key,
                        pii_type=PIIType.NAME,
                        value=value,
                        confidence=0.8,
                    )
                )

            # Check DOB fields
            elif key_lower in dob_fields:
                detected_pii.append(
                    PIIField(
                        field_name=key,
                        pii_type=PIIType.DATE_OF_BIRTH,
                        value=value,
                        confidence=0.9,
                    )
                )

        return detected_pii


class DataAnonymizer:
    """Anonymize and pseudonymize PII data."""

    @staticmethod
    def mask_email(email: str) -> str:
        """
        Mask email address.

        Args:
            email: Email to mask

        Returns:
            Masked email
        """
        local, domain = email.split("@")
        if len(local) <= 2:
            masked_local = "*" * len(local)
        else:
            masked_local = local[0] + "*" * (len(local) - 2) + local[-1]
        return f"{masked_local}@{domain}"

    @staticmethod
    def mask_phone(phone: str) -> str:
        """
        Mask phone number.

        Args:
            phone: Phone to mask

        Returns:
            Masked phone
        """
        digits = re.sub(r"\D", "", phone)
        if len(digits) >= 4:
            return "*" * (len(digits) - 4) + digits[-4:]
        return "*" * len(digits)

    @staticmethod
    def mask_ssn(ssn: str) -> str:
        """
        Mask SSN.

        Args:
            ssn: SSN to mask

        Returns:
            Masked SSN
        """
        return "***-**-" + ssn.split("-")[-1]

    @staticmethod
    def mask_credit_card(cc: str) -> str:
        """
        Mask credit card number.

        Args:
            cc: Credit card to mask

        Returns:
            Masked credit card
        """
        digits = re.sub(r"[- ]", "", cc)
        return "*" * (len(digits) - 4) + digits[-4:]

    @staticmethod
    def hash_value(value: str, salt: str = "") -> str:
        """
        Hash a value using SHA-256.

        Args:
            value: Value to hash
            salt: Salt for hashing

        Returns:
            Hashed value
        """
        return hashlib.sha256(f"{value}{salt}".encode()).hexdigest()

    def anonymize_dict(
        self, data: Dict[str, Any], pii_fields: List[PIIField]
    ) -> Dict[str, Any]:
        """
        Anonymize PII in dictionary.

        Args:
            data: Dictionary to anonymize
            pii_fields: List of detected PII fields

        Returns:
            Anonymized dictionary
        """
        anonymized = data.copy()

        for pii_field in pii_fields:
            if pii_field.field_name not in anonymized:
                continue

            if pii_field.pii_type == PIIType.EMAIL:
                anonymized[pii_field.field_name] = self.mask_email(pii_field.value)
            elif pii_field.pii_type == PIIType.PHONE:
                anonymized[pii_field.field_name] = self.mask_phone(pii_field.value)
            elif pii_field.pii_type == PIIType.SSN:
                anonymized[pii_field.field_name] = self.mask_ssn(pii_field.value)
            elif pii_field.pii_type == PIIType.CREDIT_CARD:
                anonymized[pii_field.field_name] = self.mask_credit_card(
                    pii_field.value
                )
            else:
                # Generic masking for other PII types
                anonymized[pii_field.field_name] = "*" * len(pii_field.value)

        return anonymized

    def pseudonymize_dict(
        self, data: Dict[str, Any], pii_fields: List[PIIField], salt: str = ""
    ) -> Dict[str, Any]:
        """
        Pseudonymize PII in dictionary using hashing.

        Args:
            data: Dictionary to pseudonymize
            pii_fields: List of detected PII fields
            salt: Salt for hashing

        Returns:
            Pseudonymized dictionary
        """
        pseudonymized = data.copy()

        for pii_field in pii_fields:
            if pii_field.field_name in pseudonymized:
                pseudonymized[pii_field.field_name] = self.hash_value(
                    pii_field.value, salt
                )

        return pseudonymized


class ConsentManager:
    """Manage user consent for GDPR compliance."""

    def __init__(self):
        """Initialize consent manager."""
        self.consents: Dict[str, List[ConsentRecord]] = {}

    def grant_consent(
        self,
        customer_id: str,
        consent_type: ConsentType,
        ip_address: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ConsentRecord:
        """
        Grant consent for a customer.

        Args:
            customer_id: Customer ID
            consent_type: Type of consent
            ip_address: IP address
            metadata: Additional metadata

        Returns:
            Consent record
        """
        consent = ConsentRecord(
            customer_id=customer_id,
            consent_type=consent_type,
            status=ConsentStatus.GRANTED,
            granted_at=datetime.utcnow(),
            ip_address=ip_address,
            metadata=metadata or {},
        )

        if customer_id not in self.consents:
            self.consents[customer_id] = []

        self.consents[customer_id].append(consent)
        return consent

    def revoke_consent(
        self, customer_id: str, consent_type: ConsentType
    ) -> Optional[ConsentRecord]:
        """
        Revoke consent for a customer.

        Args:
            customer_id: Customer ID
            consent_type: Type of consent

        Returns:
            Updated consent record or None
        """
        if customer_id not in self.consents:
            return None

        for consent in self.consents[customer_id]:
            if (
                consent.consent_type == consent_type
                and consent.status == ConsentStatus.GRANTED
            ):
                consent.status = ConsentStatus.REVOKED
                consent.revoked_at = datetime.utcnow()
                return consent

        return None

    def check_consent(self, customer_id: str, consent_type: ConsentType) -> bool:
        """
        Check if customer has granted consent.

        Args:
            customer_id: Customer ID
            consent_type: Type of consent

        Returns:
            True if consent granted, False otherwise
        """
        if customer_id not in self.consents:
            return False

        for consent in self.consents[customer_id]:
            if (
                consent.consent_type == consent_type
                and consent.status == ConsentStatus.GRANTED
            ):
                return True

        return False

    def get_consents(self, customer_id: str) -> List[ConsentRecord]:
        """
        Get all consents for a customer.

        Args:
            customer_id: Customer ID

        Returns:
            List of consent records
        """
        return self.consents.get(customer_id, [])


class GDPRCompliance:
    """GDPR compliance validation and enforcement."""

    REQUIRED_CONSENTS = {
        ConsentType.DATA_PROCESSING,
    }

    @staticmethod
    def validate_consent(consents: List[ConsentRecord]) -> bool:
        """
        Validate that all required consents are granted.

        Args:
            consents: List of consent records

        Returns:
            True if compliant, False otherwise
        """
        granted_consents = {
            c.consent_type for c in consents if c.status == ConsentStatus.GRANTED
        }

        return GDPRCompliance.REQUIRED_CONSENTS.issubset(granted_consents)

    @staticmethod
    def can_process_data(customer_id: str, consent_manager: ConsentManager) -> bool:
        """
        Check if data can be processed under GDPR.

        Args:
            customer_id: Customer ID
            consent_manager: Consent manager

        Returns:
            True if data can be processed, False otherwise
        """
        return consent_manager.check_consent(
            customer_id, ConsentType.DATA_PROCESSING
        )

    @staticmethod
    def can_share_data(customer_id: str, consent_manager: ConsentManager) -> bool:
        """
        Check if data can be shared under GDPR.

        Args:
            customer_id: Customer ID
            consent_manager: Consent manager

        Returns:
            True if data can be shared, False otherwise
        """
        return consent_manager.check_consent(customer_id, ConsentType.DATA_SHARING)


class PrivacyImpactAssessment:
    """Privacy Impact Assessment (PIA) for data processing."""

    def __init__(self):
        """Initialize PIA."""
        self.assessments: Dict[str, Dict[str, Any]] = {}

    def assess_data_processing(
        self, process_name: str, data_types: List[PIIType]
    ) -> Dict[str, Any]:
        """
        Assess privacy impact of data processing.

        Args:
            process_name: Name of the process
            data_types: Types of data being processed

        Returns:
            Assessment results
        """
        risk_scores = {
            PIIType.EMAIL: 3,
            PIIType.PHONE: 3,
            PIIType.SSN: 10,
            PIIType.CREDIT_CARD: 10,
            PIIType.NAME: 2,
            PIIType.ADDRESS: 5,
            PIIType.DATE_OF_BIRTH: 5,
            PIIType.DRIVERS_LICENSE: 8,
            PIIType.PASSPORT: 9,
            PIIType.IP_ADDRESS: 2,
        }

        total_risk = sum(risk_scores.get(dt, 0) for dt in data_types)
        risk_level = "low" if total_risk < 10 else "medium" if total_risk < 30 else "high"  # noqa: E501

        assessment = {
            "process_name": process_name,
            "data_types": [dt.value for dt in data_types],
            "total_risk_score": total_risk,
            "risk_level": risk_level,
            "requires_dpo_approval": risk_level == "high",
            "assessed_at": datetime.utcnow().isoformat(),
        }

        self.assessments[process_name] = assessment
        return assessment


# Global instances
pii_detector = PIIDetector()
data_anonymizer = DataAnonymizer()
consent_manager = ConsentManager()
gdpr_compliance = GDPRCompliance()
