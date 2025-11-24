"""
Backup & Recovery Management Platform.

Automated backup management, disaster recovery testing, and point-in-time recovery
using restic for deduplicated and encrypted backups, supporting multiple cloud backends
(S3, Azure Blob, GCS).

Protocol Coverage:
- P-OPS-RESILIENCE: Operational resilience with automated backups
- P-BACKUP-VALIDATION: Automated backup integrity validation
- P-RES-DR-DRILL: Disaster recovery drills with compliance reporting
- P-SYSTEM-BACKUP: Automated system-level backups with retention policies
"""

__version__ = "1.0.0"
__author__ = "devCrew_s1"

from .backup_manager import BackupConfig, BackupManager, Snapshot
from .backup_validator import (BackupValidator, ValidationConfig,
                               ValidationResult)
from .dr_drill import ComplianceReporter, DRDrill, DrillConfig, DrillReport
from .recovery_manager import RecoveryManager, RestoreConfig, RestoreResult
from .scheduler import BackupJob, ScheduleConfig, Scheduler
from .storage_adapter import (AzureBackend, GCSBackend, LocalBackend,
                              S3Backend, StorageAdapter, StorageBackend)

__all__ = [
    "BackupManager",
    "BackupConfig",
    "Snapshot",
    "StorageAdapter",
    "StorageBackend",
    "S3Backend",
    "AzureBackend",
    "GCSBackend",
    "LocalBackend",
    "RecoveryManager",
    "RestoreConfig",
    "RestoreResult",
    "BackupValidator",
    "ValidationResult",
    "ValidationConfig",
    "DRDrill",
    "DrillReport",
    "DrillConfig",
    "ComplianceReporter",
    "Scheduler",
    "ScheduleConfig",
    "BackupJob",
]
