"""Consent Management Module for Privacy Management Platform."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class ConsentPurpose(Enum):
    """Standard consent purposes."""
    MARKETING = "marketing"
    ANALYTICS = "analytics"
    PERSONALIZATION = "personalization"
    THIRD_PARTY_SHARING = "third_party_sharing"
    DATA_PROCESSING = "data_processing"
    ESSENTIAL = "essential"


class ConsentStatus(Enum):
    """Consent status values."""
    GRANTED = "granted"
    DENIED = "denied"
    PENDING = "pending"
    REVOKED = "revoked"


@dataclass
class ConsentRecord:
    """Represents a consent record."""
    user_id: str
    purpose: ConsentPurpose
    status: ConsentStatus
    timestamp: datetime
    opt_in: bool
    expiry: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class ConsentManager:
    """Manages user consent records."""

    def __init__(self):
        """Initialize Consent Manager with in-memory storage."""
        self._consents: Dict[str, Dict[ConsentPurpose, ConsentRecord]] = {}
        self._history: List[ConsentRecord] = []

    def record_consent(
        self,
        user_id: str,
        purposes: List[ConsentPurpose],
        opt_in: bool,
        expiry: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[ConsentRecord]:
        """
        Record consent for specified purposes.

        Args:
            user_id: User identifier.
            purposes: List of consent purposes.
            opt_in: Whether user opted in.
            expiry: Optional expiry date.
            metadata: Additional metadata.

        Returns:
            List of created consent records.
        """
        if user_id not in self._consents:
            self._consents[user_id] = {}

        records = []
        timestamp = datetime.now()

        for purpose in purposes:
            record = ConsentRecord(
                user_id=user_id,
                purpose=purpose,
                status=ConsentStatus.GRANTED if opt_in else ConsentStatus.DENIED,
                timestamp=timestamp,
                opt_in=opt_in,
                expiry=expiry,
                metadata=metadata or {}
            )
            self._consents[user_id][purpose] = record
            self._history.append(record)
            records.append(record)

        return records

    def check_consent(
        self,
        user_id: str,
        purpose: ConsentPurpose
    ) -> bool:
        """
        Check if user has granted consent for a purpose.

        Args:
            user_id: User identifier.
            purpose: Consent purpose to check.

        Returns:
            True if consent granted and valid, False otherwise.
        """
        if user_id not in self._consents:
            return False

        if purpose not in self._consents[user_id]:
            return False

        record = self._consents[user_id][purpose]

        # Check if expired
        if record.expiry and record.expiry < datetime.now():
            return False

        # Check if revoked
        if record.status == ConsentStatus.REVOKED:
            return False

        return record.opt_in

    def revoke_consent(
        self,
        user_id: str,
        purposes: Optional[List[ConsentPurpose]] = None
    ) -> List[ConsentRecord]:
        """
        Revoke consent for specified purposes.

        Args:
            user_id: User identifier.
            purposes: List of purposes to revoke. If None, revoke all.

        Returns:
            List of updated consent records.
        """
        if user_id not in self._consents:
            return []

        if purposes is None:
            purposes = list(self._consents[user_id].keys())

        records = []
        timestamp = datetime.now()

        for purpose in purposes:
            if purpose in self._consents[user_id]:
                old_record = self._consents[user_id][purpose]
                new_record = ConsentRecord(
                    user_id=user_id,
                    purpose=purpose,
                    status=ConsentStatus.REVOKED,
                    timestamp=timestamp,
                    opt_in=False,
                    expiry=old_record.expiry,
                    metadata=old_record.metadata
                )
                self._consents[user_id][purpose] = new_record
                self._history.append(new_record)
                records.append(new_record)

        return records

    def get_consent_status(
        self,
        user_id: str
    ) -> Dict[str, ConsentStatus]:
        """
        Get all consent statuses for a user.

        Args:
            user_id: User identifier.

        Returns:
            Dictionary mapping purpose to status.
        """
        if user_id not in self._consents:
            return {}

        return {
            purpose.value: record.status
            for purpose, record in self._consents[user_id].items()
        }

    def get_consent_history(
        self,
        user_id: Optional[str] = None,
        purpose: Optional[ConsentPurpose] = None
    ) -> List[ConsentRecord]:
        """
        Get consent history with optional filters.

        Args:
            user_id: Filter by user.
            purpose: Filter by purpose.

        Returns:
            List of matching consent records.
        """
        results = self._history

        if user_id:
            results = [r for r in results if r.user_id == user_id]

        if purpose:
            results = [r for r in results if r.purpose == purpose]

        return results

    def get_users_with_consent(
        self,
        purpose: ConsentPurpose
    ) -> List[str]:
        """
        Get list of users who granted consent for a purpose.

        Args:
            purpose: Consent purpose.

        Returns:
            List of user IDs.
        """
        users = []
        for user_id in self._consents:
            if self.check_consent(user_id, purpose):
                users.append(user_id)
        return users

    def export_consents(self, user_id: str) -> Dict[str, Any]:
        """
        Export all consent data for a user (GDPR data portability).

        Args:
            user_id: User identifier.

        Returns:
            Dictionary with all consent data.
        """
        if user_id not in self._consents:
            return {"user_id": user_id, "consents": []}

        consents = []
        for purpose, record in self._consents[user_id].items():
            consents.append({
                "purpose": purpose.value,
                "status": record.status.value,
                "opt_in": record.opt_in,
                "timestamp": record.timestamp.isoformat(),
                "expiry": record.expiry.isoformat() if record.expiry else None,
                "metadata": record.metadata
            })

        return {
            "user_id": user_id,
            "consents": consents,
            "exported_at": datetime.now().isoformat()
        }

    def delete_user_data(self, user_id: str) -> bool:
        """
        Delete all consent data for a user (GDPR right to erasure).

        Args:
            user_id: User identifier.

        Returns:
            True if data was deleted, False if user not found.
        """
        if user_id not in self._consents:
            return False

        del self._consents[user_id]
        self._history = [r for r in self._history if r.user_id != user_id]
        return True
