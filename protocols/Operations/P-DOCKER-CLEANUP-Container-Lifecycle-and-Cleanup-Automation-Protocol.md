# P-DOCKER-CLEANUP: Container Lifecycle and Cleanup Automation Protocol

**Version**: 1.0
**Last Updated**: 2025-11-14
**Status**: Active
**Owner**: DevOps-Engineer

## Objective

Establish automated container lifecycle and cleanup protocol enabling Docker/Kubernetes resource management, orphaned container detection, image layer optimization, volume cleanup, network pruning, registry maintenance, and storage reclamation ensuring container platform health, cost efficiency, and preventing resource exhaustion with automated cleanup policies.

## Tool Requirements

- **TOOL-INFRA-002** (Container Platform): Container lifecycle management, Kubernetes orchestration, and container cleanup automation
  - Execute: Container lifecycle management, Kubernetes orchestration, container cleanup automation, container operations, orchestration coordination
  - Integration: Container platforms (Docker, Kubernetes), orchestration tools, container management systems, cleanup automation, container operations
  - Usage: Container management, lifecycle automation, orchestration coordination, cleanup operations, container platform management

- **TOOL-INFRA-001** (Infrastructure): Infrastructure monitoring, resource management, and storage optimization
  - Execute: Infrastructure monitoring, resource management, storage optimization, infrastructure coordination, resource cleanup
  - Integration: Infrastructure platforms, resource monitoring, storage management, infrastructure coordination, optimization tools
  - Usage: Infrastructure management, resource optimization, storage cleanup, infrastructure coordination, resource monitoring

- **TOOL-MON-001** (APM): Container monitoring, resource tracking, and cleanup analytics
  - Execute: Container monitoring, resource tracking, cleanup analytics, container metrics, resource monitoring
  - Integration: Monitoring platforms, container monitoring tools, resource tracking systems, analytics frameworks, metrics collection
  - Usage: Container monitoring, resource tracking, cleanup monitoring, container analytics, resource observability

- **TOOL-CICD-001** (Pipeline Platform): Automated cleanup integration, CI/CD coordination, and cleanup automation
  - Execute: Automated cleanup integration, CI/CD coordination, cleanup automation, pipeline integration, automated operations
  - Integration: CI/CD platforms, automation systems, cleanup automation, pipeline tools, automated workflows
  - Usage: Cleanup automation, CI/CD integration, automated operations, pipeline coordination, workflow automation

## Trigger

- Scheduled container cleanup (daily, weekly)
- Disk space threshold breach (>80%, >90%)
- Container platform performance degradation
- Orphaned resource accumulation detection
- Registry storage exceeding quota
- Pre-deployment environment preparation
- Post-incident cleanup requirement
- Development environment refresh

## Agents

**Primary**: DevOps-Engineer
**Supporting**: SRE, Infrastructure-Engineer, Backend-Engineer
**Review**: Platform-Team-Lead, Cloud-Architect
**Orchestration**: Orchestrator (CORE-COORD-002)

## Prerequisites

- Docker/Kubernetes cluster access with admin permissions
- Container registry credentials and access
- Monitoring system for disk usage and container metrics
- Backup procedures for persistent volumes
- Label/tag strategy for resource management
- Cleanup policy definitions
- Notification system for stakeholders

## Steps

### Step 1: Container and Image Inventory Analysis (Estimated Time: 10 minutes)
**Action**: Collect comprehensive inventory of containers, images, volumes, networks

**Inventory Collection**:
```bash
#!/bin/bash
# Docker inventory analysis

echo "=== Container Inventory ==="
docker ps -a --format "table {{.ID}}\t{{.Image}}\t{{.Status}}\t{{.RunningFor}}\t{{.Names}}"

echo -e "\n=== Image Inventory ==="
docker images --format "table {{.Repository}}\t{{.Tag}}\t{{.ID}}\t{{.Size}}\t{{.CreatedSince}}"

echo -e "\n=== Disk Usage Summary ==="
docker system df -v

echo -e "\n=== Dangling Images ==="
docker images -f "dangling=true" --format "{{.ID}}\t{{.Size}}"

echo -e "\n=== Stopped Containers ==="
docker ps -a -f "status=exited" --format "{{.ID}}\t{{.Image}}\t{{.Status}}\t{{.Names}}"

echo -e "\n=== Unused Volumes ==="
docker volume ls -f "dangling=true"

echo -e "\n=== Unused Networks ==="
docker network ls --filter "type=custom" --format "{{.ID}}\t{{.Name}}\t{{.Driver}}"
```

**Expected Outcome**: Complete inventory with resource usage, age, and status
**Validation**: All resources accounted for, baseline metrics established

### Step 2: Stopped Container Cleanup (Estimated Time: 10 minutes)
**Action**: Remove stopped containers following retention policies

**Cleanup Policy**:
- **Exited containers**: Remove after 24 hours
- **Failed containers**: Retain for 7 days for debugging
- **Dev/test containers**: Remove immediately after use
- **Production containers**: Retain for 30 days (compliance)

**Cleanup Script**:
```bash
#!/bin/bash
# Safe stopped container cleanup

RETENTION_HOURS=24
DRY_RUN=false

# Find stopped containers older than retention period
docker ps -a -f "status=exited" --format "{{.ID}}\t{{.CreatedAt}}\t{{.Names}}\t{{.Label \"environment\"}}" | \
  while IFS=$'\t' read id created name env; do
    created_epoch=$(date -d "$created" +%s)
    current_epoch=$(date +%s)
    age_hours=$(( ($current_epoch - $created_epoch) / 3600 ))

    # Skip production containers within 30-day retention
    if [[ "$env" == "production" ]]; then
      if [ $age_hours -lt 720 ]; then
        echo "SKIP: Production container $name retained (${age_hours}h old)"
        continue
      fi
    fi

    if [ $age_hours -gt $RETENTION_HOURS ]; then
      echo "Removing stopped container: $name ($id) - ${age_hours}h old"
      [[ "$DRY_RUN" == false ]] && docker rm "$id"
    fi
  done

echo "Stopped container cleanup complete"
```

**Expected Outcome**: Stopped containers removed per policy, logs preserved
**Validation**: Only eligible containers deleted, production containers protected

### Step 3: Dangling and Unused Image Cleanup (Estimated Time: 15 minutes)
**Action**: Remove dangling images, unused images, and old image versions

**Image Cleanup Strategy**:
```bash
#!/bin/bash
# Image cleanup with version retention

# Remove dangling images (untagged intermediate layers)
echo "=== Removing Dangling Images ==="
docker images -f "dangling=true" -q | xargs -r docker rmi
dangling_space_freed=$(docker system df | awk '/Images/ {print $4}')
echo "Space freed from dangling images: $dangling_space_freed"

# Remove unused images (not referenced by any container)
echo -e "\n=== Removing Unused Images ==="
docker image prune -a --filter "until=168h" -f  # Images older than 7 days

# Remove old image versions (keep latest 3 versions per repository)
echo -e "\n=== Removing Old Image Versions ==="
docker images --format "{{.Repository}}\t{{.Tag}}\t{{.ID}}\t{{.CreatedAt}}" | \
  sort -k1,1 -k4,4r | \
  awk '
    {repo=$1; tag=$2; id=$3}
    repo != prev_repo {count=0; prev_repo=repo}
    count >= 3 && tag != "latest" {print id}
    {count++}
  ' | \
  xargs -r docker rmi -f

echo "Image cleanup complete"
```

**Expected Outcome**: Dangling images removed, old versions pruned, storage reclaimed
**Validation**: Latest versions preserved, ≥30% storage reduction for images >50GB

### Step 4: Volume and Data Cleanup (Estimated Time: 15 minutes)
**Action**: Identify and remove unused volumes with data integrity protection

**Volume Cleanup**:
```bash
#!/bin/bash
# Safe volume cleanup with backup verification

echo "=== Dangling Volume Analysis ==="
docker volume ls -f "dangling=true" --format "{{.Name}}\t{{.Driver}}\t{{.Mountpoint}}"

# List volumes with size and last access
echo -e "\n=== Volume Usage Analysis ==="
docker volume ls --format "{{.Name}}" | while read vol; do
  mountpoint=$(docker volume inspect "$vol" --format '{{.Mountpoint}}')
  size=$(du -sh "$mountpoint" 2>/dev/null | awk '{print $1}')
  last_access=$(find "$mountpoint" -type f -printf '%T+\n' 2>/dev/null | sort -r | head -1)
  echo "$vol\t$size\t$last_access"
done | column -t

# Remove dangling volumes (not attached to any container)
echo -e "\n=== Removing Dangling Volumes ==="
# First, verify no active containers reference these volumes
active_volumes=$(docker ps -q | xargs docker inspect -f '{{range .Mounts}}{{.Name}}{{"\n"}}{{end}}' | sort -u)
dangling_volumes=$(docker volume ls -qf "dangling=true")

for vol in $dangling_volumes; do
  if ! echo "$active_volumes" | grep -q "$vol"; then
    echo "Removing dangling volume: $vol"
    docker volume rm "$vol"
  else
    echo "SKIP: Volume $vol still referenced by running container"
  fi
done

echo "Volume cleanup complete"
```

**Expected Outcome**: Unused volumes removed, active data protected, storage reclaimed
**Validation**: No data loss, active volumes preserved, backup verification

### Step 5: Network Cleanup and Optimization (Estimated Time: 10 minutes)
**Action**: Remove unused Docker networks and optimize network configuration

**Network Cleanup**:
```bash
#!/bin/bash
# Docker network cleanup

echo "=== Network Inventory ==="
docker network ls --format "{{.ID}}\t{{.Name}}\t{{.Driver}}\t{{.Scope}}"

# Identify unused networks (no containers attached)
echo -e "\n=== Unused Networks ==="
docker network ls --format "{{.ID}}\t{{.Name}}" | while IFS=$'\t' read id name; do
  # Skip default networks
  if [[ "$name" =~ ^(bridge|host|none)$ ]]; then
    continue
  fi

  container_count=$(docker network inspect "$id" --format '{{len .Containers}}')
  if [ "$container_count" -eq 0 ]; then
    echo "Removing unused network: $name ($id)"
    docker network rm "$id" 2>/dev/null || echo "Failed to remove $name (may be in use)"
  fi
done

# Prune all unused networks
docker network prune -f

echo "Network cleanup complete"
```

**Expected Outcome**: Unused networks removed, default networks preserved
**Validation**: Active networks untouched, namespace optimization achieved

### Step 6: Container Registry Cleanup (Estimated Time: 20 minutes)
**Action**: Clean up container registry by removing untagged images and old versions

**Registry Cleanup Strategy**:
```bash
#!/bin/bash
# Container registry cleanup (example for Docker Registry v2)

REGISTRY_URL="registry.example.com"
RETENTION_DAYS=90

# List all repositories
repositories=$(curl -s -X GET "https://${REGISTRY_URL}/v2/_catalog" | jq -r '.repositories[]')

for repo in $repositories; do
  echo "Processing repository: $repo"

  # Get all tags for the repository
  tags=$(curl -s -X GET "https://${REGISTRY_URL}/v2/${repo}/tags/list" | jq -r '.tags[]')

  for tag in $tags; do
    # Get manifest digest
    digest=$(curl -s -I -H "Accept: application/vnd.docker.distribution.manifest.v2+json" \
      -X GET "https://${REGISTRY_URL}/v2/${repo}/manifests/${tag}" | \
      grep -i Docker-Content-Digest | awk '{print $2}' | tr -d '\r')

    # Get image creation date
    created_date=$(curl -s -X GET "https://${REGISTRY_URL}/v2/${repo}/manifests/${tag}" | \
      jq -r '.history[0].v1Compatibility' | jq -r '.created')

    created_epoch=$(date -d "$created_date" +%s)
    current_epoch=$(date +%s)
    age_days=$(( ($current_epoch - $created_epoch) / 86400 ))

    # Remove images older than retention period (keep latest tag)
    if [ $age_days -gt $RETENTION_DAYS ] && [ "$tag" != "latest" ]; then
      echo "Deleting old image: ${repo}:${tag} (${age_days} days old)"
      curl -s -X DELETE "https://${REGISTRY_URL}/v2/${repo}/manifests/${digest}"
    fi
  done
done

# Run garbage collection on registry
echo "Running registry garbage collection"
# (Registry-specific GC command, e.g., for Docker Registry v2)
# docker exec registry bin/registry garbage-collect /etc/docker/registry/config.yml

echo "Registry cleanup complete"
```

**Expected Outcome**: Registry storage optimized, old images removed, retention policy enforced
**Validation**: Active images preserved, ≥40% registry storage reduction

### Step 7: Comprehensive System Cleanup and Reporting (Estimated Time: 10 minutes)
**Action**: Perform system-wide cleanup and generate comprehensive report

**System Cleanup**:
```bash
#!/bin/bash
# Comprehensive Docker system cleanup

echo "=== Before Cleanup ==="
docker system df

echo -e "\n=== Running System Prune ==="
# Remove all unused data (stopped containers, unused networks, dangling images, build cache)
docker system prune -a --volumes -f

echo -e "\n=== After Cleanup ==="
docker system df

echo -e "\n=== Space Reclaimed ==="
# Calculate space savings
before=$(docker system df | awk '/Local Volumes/ {print $3}')
after=$(docker system df | awk '/Local Volumes/ {print $3}')
echo "Storage optimization complete"

# Generate cleanup report
cat > /tmp/docker_cleanup_report.txt <<EOF
Docker Cleanup Report - $(date)
================================

Container Cleanup:
- Stopped containers removed: $(docker ps -a -f "status=exited" 2>/dev/null | wc -l)

Image Cleanup:
- Dangling images removed
- Unused images older than 7 days removed
- Old image versions pruned

Volume Cleanup:
- Dangling volumes removed
- Storage reclaimed

Network Cleanup:
- Unused networks removed

Registry Cleanup:
- Images older than ${RETENTION_DAYS:-90} days removed

Total disk space reclaimed: Check docker system df output
EOF

cat /tmp/docker_cleanup_report.txt
```

**Expected Outcome**: Comprehensive cleanup report with space reclamation metrics
**Validation**: Report complete, metrics accurate, stakeholders notified

## Expected Outputs

- **Container Inventory Report**: All containers, images, volumes, networks cataloged
- **Cleanup Summary**: Resources removed with retention policy compliance
- **Storage Reclamation Report**: Disk space freed per resource type
- **Registry Optimization Report**: Old image removal and storage savings
- **Performance Metrics**: Before/after disk usage, container density
- **Failure Report**: Resources that couldn't be removed with reasons
- **Success Indicators**: ≥30% storage reduction, <5% disk usage, zero orphaned resources

## Rollback/Recovery

**Trigger**: Accidental volume deletion, critical container removal, data loss

**P-RECOVERY Integration**:
1. Restore volumes from backups (snapshot-based recovery)
2. Recreate containers from image registry
3. Restore network configurations from IaC definitions
4. Verify data integrity and service functionality

**Verification**: All services operational, data restored, no functionality loss
**Data Integrity**: Critical - Always backup volumes before cleanup

## Failure Handling

### Failure Scenario 1: Accidental Production Volume Deletion
- **Symptoms**: Critical data volume deleted during cleanup, service fails to start
- **Root Cause**: Misconfigured retention policy, missing production label
- **Impact**: Critical - Data loss, service downtime, compliance violations
- **Resolution**:
  1. Immediate restore from volume snapshot/backup
  2. Verify data integrity with application-level checks
  3. Restart services and validate functionality
  4. Implement volume label validation before deletion
  5. Post-mortem on labeling failure
- **Prevention**: Mandatory production labels, dry-run mode, volume backup verification

### Failure Scenario 2: Image Cleanup Breaking Active Deployments
- **Symptoms**: Container fails to start after image cleanup, "image not found" errors
- **Root Cause**: Active image removed due to "unused" classification, container not running during cleanup
- **Impact**: High - Deployment failures, rollback required, service interruption
- **Resolution**:
  1. Re-pull image from registry or restore from backup
  2. Update cleanup policy to check image references in deployment configs
  3. Implement image pinning for active deployments
  4. Verify image availability before cleanup
  5. Coordinate cleanup with deployment schedules
- **Prevention**: Check Kubernetes deployments, docker-compose references, image registry tags

### Failure Scenario 3: Disk Space Not Reclaimed After Cleanup
- **Symptoms**: Cleanup completes but disk usage unchanged
- **Root Cause**: Docker daemon not releasing space, volumes with active file handles
- **Impact**: Medium - Storage goals not met, cleanup ineffective
- **Resolution**:
  1. Restart Docker daemon to release space: `systemctl restart docker`
  2. Manually verify volume mountpoint deletion
  3. Check for zombie containers holding file handles: `lsof | grep deleted`
  4. Force filesystem sync: `sync && echo 3 > /proc/sys/vm/drop_caches`
  5. Investigate large container logs: `du -sh /var/lib/docker/containers/*/`
- **Prevention**: Log rotation, daemon restart in maintenance window, monitoring alerts

### Failure Scenario 4: Registry Cleanup Causing Manifest Corruption
- **Symptoms**: Image pull failures after registry cleanup, manifest not found errors
- **Root Cause**: Aggressive tag deletion without garbage collection, orphaned layers
- **Impact**: High - Image pulls fail, deployments blocked, CI/CD broken
- **Resolution**:
  1. Restore registry from backup snapshot
  2. Run registry garbage collection: `registry garbage-collect /etc/docker/registry/config.yml`
  3. Rebuild image manifests from layers if recoverable
  4. Coordinate registry GC with cleanup operations
  5. Implement manifest validation post-cleanup
- **Prevention**: Registry GC before tag deletion, atomic operations, backup verification

### Failure Scenario 5: Network Cleanup Breaking Service Communication
- **Symptoms**: Containers lose connectivity after network cleanup, DNS resolution fails
- **Root Cause**: Network removed while containers still using it, stale network references
- **Impact**: High - Service communication broken, microservices unavailable
- **Resolution**:
  1. Recreate network with same name and configuration
  2. Reconnect containers to network: `docker network connect <network> <container>`
  3. Verify DNS resolution and service discovery
  4. Update network cleanup to check active container connections
  5. Implement network dependency mapping
- **Prevention**: Active connection verification, network usage audit, Kubernetes network policies

### Failure Scenario 6: Cleanup Job Itself Consuming Excessive Resources
- **Symptoms**: Cleanup process causing CPU/memory spikes, impacting production workloads
- **Root Cause**: Unbounded parallel operations, large dataset processing, insufficient throttling
- **Impact**: Medium - Production performance degraded during cleanup
- **Resolution**:
  1. Kill runaway cleanup process: `pkill -f docker-cleanup`
  2. Implement resource limits for cleanup jobs: `docker run --cpus=1 --memory=512m`
  3. Add throttling between operations: `sleep 1` between deletions
  4. Schedule cleanup during low-traffic windows
  5. Batch operations instead of parallel execution
- **Prevention**: Resource-limited cleanup containers, off-peak scheduling, progress monitoring

## Validation Criteria

### Quantitative Thresholds
- Storage reclamation: ≥30% disk space freed (for systems >80% full)
- Container cleanup: ≥90% stopped containers >24h old removed
- Image cleanup: ≥50% dangling images removed
- Volume cleanup: ≥80% dangling volumes removed
- Registry optimization: ≥40% old image removal (images >90 days)
- Cleanup execution time: ≤30 minutes total

### Boolean Checks
- Inventory analysis completed: Pass/Fail
- Stopped containers cleaned: Pass/Fail
- Dangling images removed: Pass/Fail
- Unused volumes cleaned: Pass/Fail
- Unused networks removed: Pass/Fail
- Registry cleanup executed: Pass/Fail
- Cleanup report generated: Pass/Fail

### Qualitative Assessments
- Cleanup safety and correctness: Platform team review (≥4/5)
- Storage efficiency improvement: Infrastructure team feedback (≥4/5)
- Production impact minimization: SRE assessment (≥4/5)

**Overall Success**: Thresholds met AND boolean checks pass AND assessments ≥4/5

## HITL Escalation

### Automatic Triggers
- Critical volume deletion detected
- Production container removal
- Registry manifest corruption
- Disk space not reclaimed after cleanup

### Manual Triggers
- Cleanup policy disputes requiring business decision
- Large-scale cleanup approval (>100GB, >500 containers)
- Registry strategy decisions
- Performance impact during cleanup

### Escalation Procedure
1. **Level 1**: DevOps-Engineer safe recovery and remediation
2. **Level 2**: Platform Team Lead for policy exceptions
3. **Level 3**: Cloud Architect for registry and storage strategies
4. **Level 4**: Engineering Leadership for infrastructure investment

## Related Protocols

### Upstream
- **Container Deployment**: Creates resources requiring cleanup
- **CI/CD Pipeline**: Triggers automated cleanup jobs

### Downstream
- **P-RECOVERY**: Handles volume and container restoration
- **P-SYSTEM-BACKUP**: Provides recovery points for volumes
- **Monitoring and Alerting**: Tracks disk usage triggering cleanup

### Alternatives
- **Manual Cleanup**: Periodic manual review vs. automated
- **No Cleanup**: Accept resource accumulation vs. proactive maintenance
- **Cloud-Managed**: Use managed services with automatic cleanup

## Test Scenarios

### Happy Path

#### Scenario 1: Successful Weekly Cleanup Run
- **Setup**: Docker host with 150 stopped containers, 50GB dangling images, 20 unused volumes
- **Execution**: Run P-DOCKER-CLEANUP automated maintenance
- **Expected Result**: 140 containers removed, 35GB freed, 18 volumes deleted, zero production impact
- **Validation**: Storage reduced from 85% to 55%, all services operational

### Failure Scenarios

#### Scenario 2: Accidental Volume Deletion Recovery
- **Setup**: Cleanup policy accidentally deletes production database volume
- **Execution**: Immediate detection, volume restore from snapshot
- **Expected Result**: Volume restored within 5 minutes, database operational, no data loss
- **Validation**: Data integrity verified, cleanup policy corrected

### Edge Cases

#### Scenario 3: Cleanup During Active Deployment
- **Setup**: Automated cleanup runs while CI/CD deploying new containers
- **Execution**: Cleanup detects active deployment, skips related resources
- **Expected Result**: Deployment succeeds, cleanup defers to next window, no conflicts
- **Validation**: Smart scheduling prevents interference, deployment unaffected

## Metadata

### Version History
| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0 | 2025-10-10 | Initial protocol for Epic 111. Container lifecycle cleanup with storage optimization, registry maintenance, 6 failure scenarios. | DevOps-Engineer |

### Review Cycle
- **Frequency**: Quarterly
- **Next Review**: 2026-01-10
- **Reviewers**: DevOps-Engineer lead, Platform team, SRE lead

### Compliance Status
- **Framework Standards**: ✅ Compliant
- **Container Platform Maintenance**: Required
- **Last Validation**: 2025-10-10

## Performance SLOs

- **Cleanup execution**: ≤30 minutes
- **Storage reclamation**: ≥30% (for systems >80% full)
- **Container cleanup**: ≥90% stopped >24h
- **Image cleanup**: ≥50% dangling images
- **Volume cleanup**: ≥80% dangling volumes
- **Zero data loss**: 100% recovery capability
