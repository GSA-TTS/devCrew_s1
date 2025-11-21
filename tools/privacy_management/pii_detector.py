"""PII Detection Module for Privacy Management Platform."""

import re
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional

try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False


class PIIType(Enum):
    """Supported PII types."""
    EMAIL = "email"
    PHONE = "phone"
    SSN = "ssn"
    CREDIT_CARD = "credit_card"
    IP_ADDRESS = "ip_address"
    NAME = "name"
    ADDRESS = "address"


@dataclass
class PIIMatch:
    """Represents a detected PII match."""
    pii_type: PIIType
    value: str
    confidence: float
    field: Optional[str] = None
    start: Optional[int] = None
    end: Optional[int] = None


class PIIDetector:
    """Detects Personally Identifiable Information in data."""

    # Regex patterns for PII detection
    PATTERNS: Dict[PIIType, re.Pattern] = {
        PIIType.EMAIL: re.compile(
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        ),
        PIIType.PHONE: re.compile(
            r'\b(?:\+1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b'
        ),
        PIIType.SSN: re.compile(
            r'\b\d{3}[-.\s]?\d{2}[-.\s]?\d{4}\b'
        ),
        PIIType.CREDIT_CARD: re.compile(
            r'\b(?:\d{4}[-.\s]?){3}\d{4}\b'
        ),
        PIIType.IP_ADDRESS: re.compile(
            r'\b(?:\d{1,3}\.){3}\d{1,3}\b'
        ),
        PIIType.NAME: re.compile(
            r'\b[A-Z][a-z]+\s+[A-Z][a-z]+\b'
        ),
        PIIType.ADDRESS: re.compile(
            r'\b\d+\s+[A-Za-z]+\s+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Drive|Dr|Lane|Ln|Court|Ct)\b',
            re.IGNORECASE
        ),
    }

    # Confidence scores for each PII type
    CONFIDENCE_SCORES: Dict[PIIType, float] = {
        PIIType.EMAIL: 0.95,
        PIIType.PHONE: 0.85,
        PIIType.SSN: 0.90,
        PIIType.CREDIT_CARD: 0.90,
        PIIType.IP_ADDRESS: 0.80,
        PIIType.NAME: 0.60,
        PIIType.ADDRESS: 0.75,
    }

    def __init__(
        self,
        pii_types: Optional[List[PIIType]] = None,
        custom_patterns: Optional[Dict[str, re.Pattern]] = None
    ):
        """
        Initialize PII Detector.

        Args:
            pii_types: List of PII types to detect. If None, detect all.
            custom_patterns: Additional custom regex patterns.
        """
        self.pii_types = pii_types or list(PIIType)
        self.custom_patterns = custom_patterns or {}

    def scan_text(self, text: str) -> List[PIIMatch]:
        """
        Scan text for PII.

        Args:
            text: Text to scan.

        Returns:
            List of PII matches found.
        """
        if not text or not isinstance(text, str):
            return []

        matches: List[PIIMatch] = []

        for pii_type in self.pii_types:
            pattern = self.PATTERNS.get(pii_type)
            if pattern:
                for match in pattern.finditer(text):
                    matches.append(PIIMatch(
                        pii_type=pii_type,
                        value=match.group(),
                        confidence=self.CONFIDENCE_SCORES.get(pii_type, 0.5),
                        start=match.start(),
                        end=match.end()
                    ))

        # Check custom patterns
        for name, pattern in self.custom_patterns.items():
            for match in pattern.finditer(text):
                matches.append(PIIMatch(
                    pii_type=PIIType.NAME,  # Default type for custom
                    value=match.group(),
                    confidence=0.70,
                    start=match.start(),
                    end=match.end()
                ))

        return matches

    def scan_dict(self, data: Dict[str, Any]) -> List[PIIMatch]:
        """
        Scan dictionary for PII.

        Args:
            data: Dictionary to scan.

        Returns:
            List of PII matches found.
        """
        matches: List[PIIMatch] = []

        for field, value in data.items():
            if isinstance(value, str):
                field_matches = self.scan_text(value)
                for match in field_matches:
                    match.field = field
                matches.extend(field_matches)
            elif isinstance(value, dict):
                nested_matches = self.scan_dict(value)
                for match in nested_matches:
                    match.field = f"{field}.{match.field}" if match.field else field
                matches.extend(nested_matches)

        return matches

    def scan_dataframe(self, df: Any) -> List[PIIMatch]:
        """
        Scan pandas DataFrame for PII.

        Args:
            df: DataFrame to scan.

        Returns:
            List of PII matches found.
        """
        if not HAS_PANDAS:
            raise ImportError("pandas is required for DataFrame scanning")

        matches: List[PIIMatch] = []

        for column in df.columns:
            for idx, value in df[column].items():
                if isinstance(value, str):
                    cell_matches = self.scan_text(value)
                    for match in cell_matches:
                        match.field = f"{column}[{idx}]"
                    matches.extend(cell_matches)

        return matches

    def get_summary(self, matches: List[PIIMatch]) -> Dict[str, int]:
        """
        Get summary of PII matches by type.

        Args:
            matches: List of PII matches.

        Returns:
            Dictionary with count per PII type.
        """
        summary: Dict[str, int] = {}
        for match in matches:
            type_name = match.pii_type.value
            summary[type_name] = summary.get(type_name, 0) + 1
        return summary
