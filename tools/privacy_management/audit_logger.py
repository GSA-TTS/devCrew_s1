"""Audit Logging Module for Privacy Management Platform."""

import hashlib
import json
import os
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional


class AuditEventType(Enum):
    """Types of audit events."""
    DATA_ACCESS = "data_access"
    DATA_MODIFICATION = "data_modification"
    DATA_DELETION = "data_deletion"
    CONSENT_CHANGE = "consent_change"
    PII_DETECTION = "pii_detection"
    ANONYMIZATION = "anonymization"
    COMPLIANCE_CHECK = "compliance_check"
    EXPORT_REQUEST = "export_request"
    LOGIN = "login"
    LOGOUT = "logout"


@dataclass
class AuditEvent:
    """Represents an audit event."""
    event_id: str
    event_type: AuditEventType
    timestamp: str
    user_id: Optional[str]
    action: str
    resource: Optional[str]
    details: Dict[str, Any]
    ip_address: Optional[str]
    hash: str


class AuditLogger:
    """Logs and manages audit events."""

    def __init__(self, log_file: Optional[str] = None):
        """
        Initialize Audit Logger.

        Args:
            log_file: Path to log file. If None, uses in-memory storage.
        """
        self.log_file = log_file
        self._events: List[AuditEvent] = []
        self._event_counter = 0

        if log_file:
            Path(log_file).parent.mkdir(parents=True, exist_ok=True)
            self._load_existing_logs()

    def _load_existing_logs(self) -> None:
        """Load existing logs from file."""
        if self.log_file and os.path.exists(self.log_file):
            try:
                with open(self.log_file, "r") as f:
                    for line in f:
                        if line.strip():
                            data = json.loads(line)
                            event = AuditEvent(
                                event_id=data["event_id"],
                                event_type=AuditEventType(data["event_type"]),
                                timestamp=data["timestamp"],
                                user_id=data.get("user_id"),
                                action=data["action"],
                                resource=data.get("resource"),
                                details=data.get("details", {}),
                                ip_address=data.get("ip_address"),
                                hash=data["hash"]
                            )
                            self._events.append(event)
                            self._event_counter += 1
            except (json.JSONDecodeError, KeyError):
                pass

    def _generate_hash(self, event_data: Dict[str, Any]) -> str:
        """Generate hash for event integrity."""
        # Include previous hash for chain integrity
        prev_hash = self._events[-1].hash if self._events else "genesis"
        data_str = json.dumps(event_data, sort_keys=True) + prev_hash
        return hashlib.sha256(data_str.encode()).hexdigest()

    def log_event(
        self,
        event_type: AuditEventType,
        action: str,
        user_id: Optional[str] = None,
        resource: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None
    ) -> AuditEvent:
        """
        Log an audit event.

        Args:
            event_type: Type of event.
            action: Description of action.
            user_id: User who performed action.
            resource: Resource affected.
            details: Additional details.
            ip_address: Source IP address.

        Returns:
            Created audit event.
        """
        self._event_counter += 1
        timestamp = datetime.now().isoformat()

        event_data = {
            "event_type": event_type.value,
            "timestamp": timestamp,
            "user_id": user_id,
            "action": action,
            "resource": resource,
            "details": details or {}
        }

        event_hash = self._generate_hash(event_data)

        event = AuditEvent(
            event_id=f"EVT-{self._event_counter:08d}",
            event_type=event_type,
            timestamp=timestamp,
            user_id=user_id,
            action=action,
            resource=resource,
            details=details or {},
            ip_address=ip_address,
            hash=event_hash
        )

        self._events.append(event)

        if self.log_file:
            self._persist_event(event)

        return event

    def _persist_event(self, event: AuditEvent) -> None:
        """Persist event to log file."""
        event_dict = {
            "event_id": event.event_id,
            "event_type": event.event_type.value,
            "timestamp": event.timestamp,
            "user_id": event.user_id,
            "action": event.action,
            "resource": event.resource,
            "details": event.details,
            "ip_address": event.ip_address,
            "hash": event.hash
        }
        with open(self.log_file, "a") as f:
            f.write(json.dumps(event_dict) + "\n")

    def query_logs(
        self,
        user_id: Optional[str] = None,
        event_type: Optional[AuditEventType] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        resource: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[AuditEvent]:
        """
        Query audit logs with filters.

        Args:
            user_id: Filter by user.
            event_type: Filter by event type.
            start_date: Filter by start date.
            end_date: Filter by end date.
            resource: Filter by resource.
            limit: Maximum results.

        Returns:
            List of matching events.
        """
        results = self._events

        if user_id:
            results = [e for e in results if e.user_id == user_id]

        if event_type:
            results = [e for e in results if e.event_type == event_type]

        if start_date:
            start_str = start_date.isoformat()
            results = [e for e in results if e.timestamp >= start_str]

        if end_date:
            end_str = end_date.isoformat()
            results = [e for e in results if e.timestamp <= end_str]

        if resource:
            results = [e for e in results if e.resource == resource]

        if limit:
            results = results[:limit]

        return results

    def verify_integrity(self) -> bool:
        """
        Verify integrity of audit log chain.

        Returns:
            True if log integrity is valid, False otherwise.
        """
        if not self._events:
            return True

        prev_hash = "genesis"
        for event in self._events:
            event_data = {
                "event_type": event.event_type.value,
                "timestamp": event.timestamp,
                "user_id": event.user_id,
                "action": event.action,
                "resource": event.resource,
                "details": event.details
            }
            data_str = json.dumps(event_data, sort_keys=True) + prev_hash
            expected_hash = hashlib.sha256(data_str.encode()).hexdigest()

            if event.hash != expected_hash:
                return False

            prev_hash = event.hash

        return True

    def get_event_count(self) -> int:
        """Get total number of events."""
        return len(self._events)

    def get_events_by_type(self) -> Dict[str, int]:
        """Get count of events by type."""
        counts: Dict[str, int] = {}
        for event in self._events:
            type_name = event.event_type.value
            counts[type_name] = counts.get(type_name, 0) + 1
        return counts

    def export_logs(
        self,
        format: str = "json",
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> str:
        """
        Export logs in specified format.

        Args:
            format: Export format (json, csv).
            start_date: Filter start date.
            end_date: Filter end date.

        Returns:
            Exported log data as string.
        """
        events = self.query_logs(start_date=start_date, end_date=end_date)

        if format == "json":
            return json.dumps([
                {
                    "event_id": e.event_id,
                    "event_type": e.event_type.value,
                    "timestamp": e.timestamp,
                    "user_id": e.user_id,
                    "action": e.action,
                    "resource": e.resource,
                    "details": e.details,
                    "ip_address": e.ip_address,
                    "hash": e.hash
                }
                for e in events
            ], indent=2)
        elif format == "csv":
            lines = ["event_id,event_type,timestamp,user_id,action,resource"]
            for e in events:
                lines.append(
                    f"{e.event_id},{e.event_type.value},{e.timestamp},"
                    f"{e.user_id or ''},{e.action},{e.resource or ''}"
                )
            return "\n".join(lines)

        return ""

    def clear_logs(self) -> None:
        """Clear all logs (use with caution)."""
        self._events.clear()
        self._event_counter = 0
        if self.log_file and os.path.exists(self.log_file):
            os.remove(self.log_file)
