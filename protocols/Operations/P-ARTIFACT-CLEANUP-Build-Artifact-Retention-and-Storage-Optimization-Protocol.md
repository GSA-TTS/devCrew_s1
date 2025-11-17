# P-ARTIFACT-CLEANUP: Build Artifact Retention and Storage Optimization Protocol

**Version**: 1.0
**Last Updated**: 2025-11-17
**Status**: Active
**Owner**: DevOps-Engineer

## Objective

Establish automated build artifact retention and storage optimization protocol enabling intelligent artifact lifecycle management, version retention policies, storage tier optimization, checksum integrity verification, artifact repository cleanup, and cost-effective storage reclamation ensuring CI/CD efficiency, compliance with retention requirements, and prevention of artifact storage exhaustion.

## Trigger

- Scheduled artifact cleanup (daily, weekly)
- Artifact repository storage threshold breach (>80%, >90%)
- Build pipeline slowdown due to artifact proliferation
- Post-release cleanup requirement
- Compliance audit requiring retention validation
- Artifact repository migration preparation
- Cost optimization initiative for artifact storage

## Agents

**Primary**: DevOps-Engineer
**Supporting**: Backend-Engineer, SRE, Release-Manager
**Review**: Technical-Lead, Compliance-Officer
**Orchestration**: Orchestrator (CORE-COORD-002)

## Prerequisites

- Access to artifact repositories (Artifactory, Nexus, S3, Azure Artifacts)
- Retention policy definitions (by artifact type, environment, compliance)
- Build metadata and artifact manifest access
- Storage backend monitoring
- Backup procedures for critical artifacts
- Notification system for stakeholders
- Cost tracking for artifact storage

## Steps

### Step 1: Artifact Inventory and Classification (Estimated Time: 15 minutes)
**Action**: Catalog all artifacts and classify by type, version, environment, retention requirements

**Artifact Classification**:
```python
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Optional

@dataclass
class ArtifactMetadata:
    artifact_id: str
    artifact_type: str  # jar, war, docker, npm, nuget, maven, pypi
    version: str
    environment: str  # dev, test, staging, production
    build_date: datetime
    build_number: int
    size_bytes: int
    repository: str
    retention_class: str  # temporary, standard, long-term, permanent
    compliance_required: bool
    last_accessed: Optional[datetime]
    checksum: str

class ArtifactInventory:
    def __init__(self):
        self.artifacts: List[ArtifactMetadata] = []

    def classify_artifact(self, artifact: ArtifactMetadata) -> str:
        """Classify artifact by retention requirements"""
        # Production artifacts: long-term retention
        if artifact.environment == 'production':
            return 'long-term'  # 2 years

        # Release candidates: standard retention
        if 'rc' in artifact.version or 'release' in artifact.version:
            return 'standard'  # 6 months

        # Snapshot/dev builds: temporary retention
        if 'SNAPSHOT' in artifact.version or artifact.environment == 'dev':
            return 'temporary'  # 30 days

        # Compliance-required: permanent retention
        if artifact.compliance_required:
            return 'permanent'  # indefinite

        return 'standard'

    def calculate_retention_period(self, retention_class: str) -> timedelta:
        retention_policies = {
            'temporary': timedelta(days=30),
            'standard': timedelta(days=180),
            'long-term': timedelta(days=730),
            'permanent': None  # Never delete
        }
        return retention_policies.get(retention_class)
```

**Expected Outcome**: Complete artifact inventory with retention classification
**Validation**: All artifacts classified, retention policies mapped, storage metrics collected

### Step 2: Retention Policy Enforcement and Cleanup Candidate Identification (Estimated Time: 15 minutes)
**Action**: Identify artifacts eligible for deletion based on retention policies

**Cleanup Candidate Selection**:
```python
from datetime import datetime

class ArtifactCleanupPolicy:
    def __init__(self, inventory: ArtifactInventory):
        self.inventory = inventory
        self.cleanup_candidates = []

    def identify_cleanup_candidates(self) -> List[ArtifactMetadata]:
        """Identify artifacts eligible for deletion"""
        current_date = datetime.now()

        for artifact in self.inventory.artifacts:
            retention_period = self.inventory.calculate_retention_period(artifact.retention_class)

            # Skip permanent retention artifacts
            if retention_period is None:
                continue

            # Calculate artifact age
            artifact_age = current_date - artifact.build_date

            # Check if artifact exceeded retention period
            if artifact_age > retention_period:
                # Additional safety checks
                if not self._is_protected_artifact(artifact):
                    self.cleanup_candidates.append({
                        'artifact': artifact,
                        'age_days': artifact_age.days,
                        'retention_days': retention_period.days,
                        'size_mb': artifact.size_bytes / (1024 * 1024),
                        'reason': f'Exceeded {artifact.retention_class} retention policy'
                    })

        return self.cleanup_candidates

    def _is_protected_artifact(self, artifact: ArtifactMetadata) -> bool:
        """Check if artifact should be protected from deletion"""
        protected_conditions = [
            artifact.environment == 'production' and artifact.build_date > datetime.now() - timedelta(days=90),  # Recent prod
            artifact.version.endswith('.0'),  # Major releases
            'latest' in artifact.version,
            artifact.compliance_required,
        ]
        return any(protected_conditions)
```

**Expected Outcome**: List of cleanup candidates with deletion rationale
**Validation**: Protected artifacts excluded, retention policies correctly applied

### Step 3: Version Retention and Cleanup Execution (Estimated Time: 20 minutes)
**Action**: Execute artifact deletion with version retention (keep latest N versions)

**Version-Aware Cleanup**:
```bash
#!/bin/bash
# Artifact cleanup with version retention

RETENTION_DAYS=30
KEEP_LATEST_N=5
DRY_RUN=false
REPOSITORY="maven-releases"

# Example: Maven artifact cleanup (Artifactory)
echo "=== Artifact Cleanup for Repository: $REPOSITORY ==="

# Query Artifactory API for artifacts older than retention period
curl -u admin:password -X POST "http://artifactory.example.com/api/search/aql" \
  -H "Content-Type: text/plain" \
  -d "items.find({
    \"repo\": \"$REPOSITORY\",
    \"modified\": {\"\$before\": \"${RETENTION_DAYS}d\"}
  })" | jq -r '.results[] | "\(.repo)/\(.path)/\(.name)"' > artifacts_to_cleanup.txt

# Group artifacts by artifact ID and keep latest N versions
cat artifacts_to_cleanup.txt | while read artifact_path; do
  artifact_name=$(basename "$artifact_path")
  artifact_group=$(dirname "$artifact_path")

  # Get all versions for this artifact
  versions=$(curl -s -u admin:password \
    "http://artifactory.example.com/api/search/artifact?name=${artifact_name}" | \
    jq -r '.results[].uri' | sort -V)

  # Keep latest N versions, delete older ones
  delete_versions=$(echo "$versions" | head -n -$KEEP_LATEST_N)

  for version_uri in $delete_versions; do
    echo "Deleting artifact: $version_uri"
    [[ "$DRY_RUN" == false ]] && curl -u admin:password -X DELETE "$version_uri"
  done
done

echo "Artifact cleanup complete"
```

**Expected Outcome**: Old artifacts deleted, latest versions preserved, storage reclaimed
**Validation**: Version retention enforced, no latest versions deleted

### Step 4: Storage Tier Optimization and Archival (Estimated Time: 20 minutes)
**Action**: Move infrequently accessed artifacts to cost-effective storage tiers

**Storage Tier Strategy**:
```python
from enum import Enum

class StorageTier(Enum):
    HOT = "hot"          # Frequently accessed, high-cost (SSD)
    COOL = "cool"        # Infrequently accessed, medium-cost (HDD)
    COLD = "cold"        # Rarely accessed, low-cost (Archive)
    GLACIER = "glacier"  # Compliance/audit, lowest-cost (Deep Archive)

class StorageTierOptimizer:
    def __init__(self, inventory: ArtifactInventory):
        self.inventory = inventory

    def recommend_storage_tier(self, artifact: ArtifactMetadata) -> StorageTier:
        """Recommend optimal storage tier based on access patterns"""
        days_since_last_access = (datetime.now() - artifact.last_accessed).days if artifact.last_accessed else 9999

        # Hot tier: Accessed within 7 days
        if days_since_last_access <= 7:
            return StorageTier.HOT

        # Cool tier: Accessed within 30 days
        elif days_since_last_access <= 30:
            return StorageTier.COOL

        # Cold tier: Accessed within 180 days
        elif days_since_last_access <= 180:
            return StorageTier.COLD

        # Glacier: Not accessed in 180+ days OR compliance-required
        else:
            return StorageTier.GLACIER

    def calculate_cost_savings(self, artifact: ArtifactMetadata, new_tier: StorageTier) -> float:
        """Calculate monthly cost savings from tier transition"""
        # Cost per GB per month (example pricing)
        tier_costs = {
            StorageTier.HOT: 0.023,
            StorageTier.COOL: 0.01,
            StorageTier.COLD: 0.004,
            StorageTier.GLACIER: 0.001
        }

        current_tier = self._infer_current_tier(artifact)
        artifact_size_gb = artifact.size_bytes / (1024 ** 3)

        current_cost = artifact_size_gb * tier_costs[current_tier]
        new_cost = artifact_size_gb * tier_costs[new_tier]

        return current_cost - new_cost  # Monthly savings

    def _infer_current_tier(self, artifact: ArtifactMetadata) -> StorageTier:
        # Infer from repository configuration or metadata
        return StorageTier.HOT  # Default assumption
```

**Expected Outcome**: Artifacts moved to cost-effective tiers, storage costs reduced
**Validation**: Access patterns analyzed, ≥40% cost reduction for infrequently accessed artifacts

### Step 5: Checksum Integrity Verification and Corruption Detection (Estimated Time: 15 minutes)
**Action**: Verify artifact integrity using checksums, detect corruption

**Integrity Verification**:
```bash
#!/bin/bash
# Artifact integrity verification

REPOSITORY_PATH="/var/artifactory/data"
CHECKSUM_ALGORITHM="sha256"

echo "=== Artifact Integrity Verification ==="

# Find all artifacts with stored checksums
find "$REPOSITORY_PATH" -type f -name "*.jar" -o -name "*.war" -o -name "*.tar.gz" | while read artifact_file; do
  checksum_file="${artifact_file}.${CHECKSUM_ALGORITHM}"

  # Check if checksum file exists
  if [ -f "$checksum_file" ]; then
    stored_checksum=$(cat "$checksum_file")
    calculated_checksum=$(sha256sum "$artifact_file" | awk '{print $1}')

    if [ "$stored_checksum" != "$calculated_checksum" ]; then
      echo "CORRUPTION DETECTED: $artifact_file"
      echo "  Stored: $stored_checksum"
      echo "  Calculated: $calculated_checksum"
      echo "  Action: Quarantine and restore from backup"

      # Quarantine corrupted artifact
      mkdir -p /var/artifactory/quarantine
      mv "$artifact_file" /var/artifactory/quarantine/
    else
      echo "OK: $artifact_file"
    fi
  else
    echo "WARNING: No checksum for $artifact_file - generating..."
    sha256sum "$artifact_file" | awk '{print $1}' > "$checksum_file"
  fi
done

echo "Integrity verification complete"
```

**Expected Outcome**: Corrupted artifacts identified and quarantined, integrity verified
**Validation**: 100% artifacts verified, corrupted artifacts replaced from backup

### Step 6: Artifact Repository Consolidation and Deduplication (Estimated Time: 20 minutes)
**Action**: Identify and eliminate duplicate artifacts, consolidate repositories

**Deduplication Strategy**:
```python
import hashlib
from collections import defaultdict

class ArtifactDeduplicator:
    def __init__(self, inventory: ArtifactInventory):
        self.inventory = inventory
        self.duplicates = defaultdict(list)

    def identify_duplicates(self) -> dict:
        """Identify duplicate artifacts by content hash"""
        hash_map = defaultdict(list)

        for artifact in self.inventory.artifacts:
            # Group artifacts by checksum (content hash)
            hash_map[artifact.checksum].append(artifact)

        # Find duplicates (same checksum, different paths)
        for checksum, artifacts in hash_map.items():
            if len(artifacts) > 1:
                # Calculate total wasted space
                artifact_size = artifacts[0].size_bytes
                wasted_space = artifact_size * (len(artifacts) - 1)

                self.duplicates[checksum] = {
                    'artifacts': artifacts,
                    'duplicate_count': len(artifacts) - 1,
                    'wasted_space_mb': wasted_space / (1024 * 1024),
                    'canonical_artifact': min(artifacts, key=lambda a: a.build_date)  # Keep oldest
                }

        return self.duplicates

    def deduplicate(self, dry_run=True) -> dict:
        """Remove duplicate artifacts, keeping canonical version"""
        dedup_report = {
            'artifacts_removed': 0,
            'space_reclaimed_mb': 0,
            'actions': []
        }

        for checksum, dup_info in self.duplicates.items():
            canonical = dup_info['canonical_artifact']

            for artifact in dup_info['artifacts']:
                if artifact != canonical:
                    action = f"DELETE {artifact.repository}/{artifact.artifact_id} (duplicate of {canonical.artifact_id})"
                    dedup_report['actions'].append(action)

                    if not dry_run:
                        self._delete_artifact(artifact)

                    dedup_report['artifacts_removed'] += 1
                    dedup_report['space_reclaimed_mb'] += artifact.size_bytes / (1024 * 1024)

        return dedup_report

    def _delete_artifact(self, artifact: ArtifactMetadata):
        """Delete artifact via repository API"""
        # Implementation depends on artifact repository (Artifactory, Nexus, etc.)
        pass
```

**Expected Outcome**: Duplicate artifacts removed, storage optimized, canonical versions preserved
**Validation**: Deduplication savings ≥20% for large repositories, no data loss

### Step 7: Cleanup Report and Storage Analytics (Estimated Time: 10 minutes)
**Action**: Generate comprehensive cleanup report with storage analytics and cost savings

**Expected Outcome**: Detailed report with artifacts deleted, storage reclaimed, cost savings
**Validation**: Report accurate, stakeholders notified, compliance documented

## Expected Outputs

- **Artifact Inventory Report**: Complete catalog with retention classification
- **Cleanup Summary**: Artifacts deleted per retention policy
- **Version Retention Report**: Latest N versions preserved per artifact
- **Storage Tier Optimization**: Cost savings from tier transitions
- **Integrity Verification Report**: Checksum validation, corruption detection
- **Deduplication Report**: Duplicate removal, space reclaimed
- **Cost Savings Analysis**: Monthly storage cost reduction
- **Success Indicators**: ≥40% storage reduction, 100% integrity verified, ≥30% cost savings

## Rollback/Recovery

**Trigger**: Accidental artifact deletion, critical version removed, compliance violation

**P-RECOVERY Integration**:
1. Restore artifacts from backup repository or cold storage
2. Rebuild artifacts from source code if backups unavailable
3. Restore artifact metadata and checksums
4. Re-publish artifacts to repository with original versions

**Verification**: Artifacts restored, builds functional, checksums validated
**Data Integrity**: Critical - Backup verification before cleanup mandatory

## Failure Handling

### Failure Scenario 1: Production Artifact Accidentally Deleted
- **Symptoms**: Build fails with "artifact not found", deployment blocked
- **Root Cause**: Production artifact deleted due to misconfigured retention policy
- **Impact**: Critical - Production deployments blocked, rollback impossible
- **Resolution**:
  1. Immediate restore from backup repository
  2. If no backup, rebuild from source: `git checkout v1.2.3 && ./build.sh`
  3. Re-publish artifact with original version and checksum
  4. Update retention policy to protect production artifacts
  5. Implement dry-run validation before production cleanup
- **Prevention**: Production artifact protection, retention policy testing, immutable artifact flags

### Failure Scenario 2: Latest Version Deleted Breaking CI/CD
- **Symptoms**: CI/CD pipeline fails referencing latest artifact version
- **Root Cause**: Version retention logic error, latest version incorrectly identified
- **Impact**: High - CI/CD broken, development velocity impacted
- **Resolution**:
  1. Restore latest version from backup or rebuild
  2. Fix version retention logic to use semantic version comparison
  3. Test retention logic against historical artifacts
  4. Implement version pinning in CI/CD to avoid "latest" dependency
  5. Add pre-cleanup version validation
- **Prevention**: Semantic version sorting, latest tag protection, CI/CD version pinning

### Failure Scenario 3: Checksum Mismatch After Cleanup
- **Symptoms**: Artifact integrity checks fail, builds reject artifacts
- **Root Cause**: Checksum corruption during storage tier migration, incomplete transfers
- **Impact**: High - Artifacts unusable, trust in repository compromised
- **Resolution**:
  1. Quarantine artifacts with checksum mismatches
  2. Restore from backup with verified checksums
  3. Re-verify entire repository with integrity scan
  4. Investigate storage backend corruption
  5. Implement atomic tier migrations with checksum validation
- **Prevention**: Checksum verification during migration, atomic operations, backup validation

### Failure Scenario 4: Compliance Artifact Deleted Violating Retention
- **Symptoms**: Audit fails due to missing compliance-required artifact
- **Root Cause**: Compliance flag not set, retention policy override
- **Impact**: Critical - Regulatory violations, audit failures, legal risk
- **Resolution**:
  1. Restore artifact from compliance backup or cold storage
  2. Implement mandatory compliance tagging
  3. Create immutable compliance repository with no cleanup
  4. Audit all compliance artifacts for retention compliance
  5. Document retention policy exception process
- **Prevention**: Mandatory compliance flags, immutable repositories, audit trails

### Failure Scenario 5: Storage Not Reclaimed After Cleanup
- **Symptoms**: Cleanup reports artifacts deleted but storage usage unchanged
- **Root Cause**: Repository not running garbage collection, soft deletes only
- **Impact**: Medium - Storage goals not met, costs not reduced
- **Resolution**:
  1. Run repository garbage collection: `artifactory cleanup` or `nexus cleanup`
  2. Verify physical deletion of artifacts on storage backend
  3. Check for snapshot/version history retention
  4. Implement hard delete for cleanup operations
  5. Monitor storage metrics post-cleanup
- **Prevention**: Automated GC after cleanup, hard delete configuration, storage monitoring

### Failure Scenario 6: Deduplication Breaking Artifact References
- **Symptoms**: Builds fail after deduplication, artifacts not found at expected paths
- **Root Cause**: Deduplication changed artifact paths, references not updated
- **Impact**: High - Builds broken, CI/CD failures, team productivity impacted
- **Resolution**:
  1. Restore duplicate artifacts to original paths
  2. Implement symbolic links or repository redirects
  3. Update build configurations to use canonical artifact paths
  4. Test deduplication in isolated repository first
  5. Implement gradual deduplication with path validation
- **Prevention**: Path-preserving deduplication, redirect rules, build configuration updates

## Validation Criteria

### Quantitative Thresholds
- Storage reclamation: ≥40% for repositories >1TB
- Artifact cleanup: ≥80% artifacts exceeding retention deleted
- Version retention: 100% compliance with keep-latest-N policy
- Integrity verification: 100% artifacts checksum-validated
- Deduplication: ≥20% duplicate removal for large repositories
- Cost savings: ≥30% monthly storage costs reduced
- Cleanup execution time: ≤45 minutes

### Boolean Checks
- Artifact inventory completed: Pass/Fail
- Retention policies enforced: Pass/Fail
- Version retention validated: Pass/Fail
- Storage tier optimization executed: Pass/Fail
- Integrity verification passed: Pass/Fail
- Deduplication completed: Pass/Fail
- Cleanup report generated: Pass/Fail

### Qualitative Assessments
- Cleanup safety and correctness: Release manager review (≥4/5)
- Storage efficiency improvement: DevOps team feedback (≥4/5)
- CI/CD impact minimization: Development team survey (≥4/5)

**Overall Success**: Thresholds met AND boolean checks pass AND assessments ≥4/5

## HITL Escalation

### Automatic Triggers
- Production artifact deletion detected
- Compliance artifact missing
- Checksum verification failures
- Storage not reclaimed after cleanup

### Manual Triggers
- Retention policy exceptions requiring approval
- Large-scale cleanup approval (>500GB, >10K artifacts)
- Compliance retention disputes
- Cost optimization strategy decisions

### Escalation Procedure
1. **Level 1**: DevOps-Engineer recovery and policy correction
2. **Level 2**: Release Manager for version retention decisions
3. **Level 3**: Compliance Officer for retention policy exceptions
4. **Level 4**: Engineering Leadership for repository strategy changes

## Related Protocols

### Upstream
- **CI/CD Pipeline**: Produces artifacts requiring lifecycle management
- **Release Management**: Defines artifact retention requirements

### Downstream
- **P-RECOVERY**: Handles artifact restoration from backups
- **P-FINOPS-COST-MONITOR**: Tracks artifact storage costs
- **Compliance Reporting**: Uses artifact retention for audit evidence

### Alternatives
- **Manual Cleanup**: Periodic manual review vs. automated
- **No Cleanup**: Accept storage growth vs. proactive optimization
- **Cloud-Managed**: Use managed artifact repositories with automatic cleanup

## Test Scenarios

### Happy Path

#### Scenario 1: Successful Monthly Artifact Cleanup
- **Setup**: Repository with 5K artifacts, 1.5TB storage, 60% exceeding retention
- **Execution**: Run P-ARTIFACT-CLEANUP with retention enforcement
- **Expected Result**: 3K artifacts deleted, storage reduced to 650GB (57% reduction), latest versions preserved
- **Validation**: No production artifacts deleted, CI/CD unaffected, cost savings 55%

### Failure Scenarios

#### Scenario 2: Production Artifact Deletion Recovery
- **Setup**: Cleanup accidentally deletes production v2.5.0 artifact
- **Execution**: Immediate detection, restore from backup
- **Expected Result**: Artifact restored within 10 minutes, builds operational, retention policy corrected
- **Validation**: Zero downtime, policy updated to protect production artifacts

### Edge Cases

#### Scenario 3: Deduplication with Complex Version Trees
- **Setup**: Multiple artifact versions with identical content (repackaging)
- **Execution**: Deduplication identifies canonical version, removes duplicates
- **Expected Result**: 30% space reclaimed, all version references preserved via redirects
- **Validation**: Builds functional, no broken references, storage optimized

## Metadata

### Version History
| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0 | 2025-10-10 | Initial protocol for Epic 111. Build artifact lifecycle with retention policies, storage optimization, 6 failure scenarios. | DevOps-Engineer |

### Review Cycle
- **Frequency**: Quarterly
- **Next Review**: 2026-01-10
- **Reviewers**: DevOps-Engineer lead, Release manager, Compliance officer

### Compliance Status
- **Framework Standards**: ✅ Compliant
- **Artifact Retention**: Required
- **Last Validation**: 2025-10-10

## Performance SLOs

- **Cleanup execution**: ≤45 minutes
- **Storage reclamation**: ≥40% (for repos >1TB)
- **Artifact cleanup**: ≥80% expired artifacts
- **Integrity verification**: 100% checksums validated
- **Deduplication**: ≥20% duplicate removal
- **Cost savings**: ≥30% monthly costs reduced
