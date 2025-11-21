"""Data Anonymization Module for Privacy Management Platform."""

import hashlib
import secrets
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

from pii_detector import PIIMatch, PIIType


class AnonymizationMethod(Enum):
    """Available anonymization methods."""
    MASKING = "masking"
    HASHING = "hashing"
    PSEUDONYMIZATION = "pseudonymization"
    GENERALIZATION = "generalization"
    SUPPRESSION = "suppression"


@dataclass
class AnonymizationConfig:
    """Configuration for anonymization."""
    method: AnonymizationMethod
    mask_char: str = "*"
    visible_chars: int = 4
    hash_salt: Optional[str] = None
    generalization_rules: Dict[str, Callable] = field(default_factory=dict)


class DataAnonymizer:
    """Anonymizes sensitive data using various techniques."""

    def __init__(self, salt: Optional[str] = None):
        """
        Initialize Data Anonymizer.

        Args:
            salt: Salt for hashing operations. If None, generates random salt.
        """
        self.salt = salt or secrets.token_hex(16)
        self._pseudonym_map: Dict[str, str] = {}

    def mask(
        self,
        value: str,
        mask_char: str = "*",
        visible_chars: int = 4,
        visible_position: str = "end"
    ) -> str:
        """
        Mask sensitive data keeping some characters visible.

        Args:
            value: Value to mask.
            mask_char: Character to use for masking.
            visible_chars: Number of visible characters.
            visible_position: Where to keep visible chars ("start" or "end").

        Returns:
            Masked value.
        """
        if not value or len(value) <= visible_chars:
            return mask_char * len(value) if value else ""

        if visible_position == "start":
            return value[:visible_chars] + mask_char * (len(value) - visible_chars)
        else:  # end
            return mask_char * (len(value) - visible_chars) + value[-visible_chars:]

    def hash_value(self, value: str, salt: Optional[str] = None) -> str:
        """
        Hash value using SHA-256 with salt.

        Args:
            value: Value to hash.
            salt: Optional salt override.

        Returns:
            Hashed value.
        """
        use_salt = salt or self.salt
        salted_value = f"{use_salt}{value}"
        return hashlib.sha256(salted_value.encode()).hexdigest()

    def pseudonymize(self, value: str) -> str:
        """
        Replace value with consistent pseudonym.

        Args:
            value: Value to pseudonymize.

        Returns:
            Pseudonymized value (consistent for same input).
        """
        if value not in self._pseudonym_map:
            self._pseudonym_map[value] = f"PSEUDO_{uuid.uuid4().hex[:8].upper()}"
        return self._pseudonym_map[value]

    def generalize(
        self,
        value: Any,
        generalization_type: str = "age_range"
    ) -> str:
        """
        Generalize value to reduce precision.

        Args:
            value: Value to generalize.
            generalization_type: Type of generalization.

        Returns:
            Generalized value.
        """
        if generalization_type == "age_range":
            try:
                age = int(value)
                if age < 18:
                    return "under 18"
                elif age < 30:
                    return "18-29"
                elif age < 50:
                    return "30-49"
                elif age < 65:
                    return "50-64"
                else:
                    return "65+"
            except (ValueError, TypeError):
                return str(value)

        elif generalization_type == "zip_prefix":
            zip_str = str(value)
            if len(zip_str) >= 3:
                return zip_str[:3] + "XX"
            return zip_str

        elif generalization_type == "date_year":
            date_str = str(value)
            if len(date_str) >= 4:
                return date_str[:4]
            return date_str

        return str(value)

    def suppress(self, value: Any) -> str:
        """
        Suppress (remove) value entirely.

        Args:
            value: Value to suppress.

        Returns:
            Empty string or placeholder.
        """
        return "[SUPPRESSED]"

    def anonymize_pii(
        self,
        text: str,
        matches: List[PIIMatch],
        method: AnonymizationMethod = AnonymizationMethod.MASKING,
        **kwargs: Any
    ) -> str:
        """
        Anonymize PII in text based on detected matches.

        Args:
            text: Original text.
            matches: List of PII matches to anonymize.
            method: Anonymization method to use.
            **kwargs: Additional arguments for the method.

        Returns:
            Anonymized text.
        """
        # Sort matches by position in reverse to avoid offset issues
        sorted_matches = sorted(
            [m for m in matches if m.start is not None],
            key=lambda m: m.start or 0,
            reverse=True
        )

        result = text
        for match in sorted_matches:
            if match.start is None or match.end is None:
                continue

            if method == AnonymizationMethod.MASKING:
                replacement = self.mask(match.value, **kwargs)
            elif method == AnonymizationMethod.HASHING:
                replacement = self.hash_value(match.value)
            elif method == AnonymizationMethod.PSEUDONYMIZATION:
                replacement = self.pseudonymize(match.value)
            elif method == AnonymizationMethod.SUPPRESSION:
                replacement = self.suppress(match.value)
            else:
                replacement = match.value

            result = result[:match.start] + replacement + result[match.end:]

        return result

    def anonymize_dict(
        self,
        data: Dict[str, Any],
        fields_config: Dict[str, AnonymizationMethod],
        **kwargs: Any
    ) -> Dict[str, Any]:
        """
        Anonymize specific fields in a dictionary.

        Args:
            data: Dictionary with data.
            fields_config: Mapping of field names to anonymization methods.
            **kwargs: Additional arguments.

        Returns:
            Anonymized dictionary.
        """
        result = data.copy()

        for field_name, method in fields_config.items():
            if field_name in result:
                value = str(result[field_name])

                if method == AnonymizationMethod.MASKING:
                    result[field_name] = self.mask(value, **kwargs)
                elif method == AnonymizationMethod.HASHING:
                    result[field_name] = self.hash_value(value)
                elif method == AnonymizationMethod.PSEUDONYMIZATION:
                    result[field_name] = self.pseudonymize(value)
                elif method == AnonymizationMethod.SUPPRESSION:
                    result[field_name] = self.suppress(value)
                elif method == AnonymizationMethod.GENERALIZATION:
                    gen_type = kwargs.get("generalization_type", "age_range")
                    result[field_name] = self.generalize(value, gen_type)

        return result

    def reset_pseudonyms(self) -> None:
        """Reset the pseudonym mapping."""
        self._pseudonym_map.clear()
