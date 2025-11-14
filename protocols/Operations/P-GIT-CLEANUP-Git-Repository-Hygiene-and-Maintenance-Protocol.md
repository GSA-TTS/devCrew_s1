# P-GIT-CLEANUP: Git Repository Hygiene and Maintenance Protocol

**Version**: 1.0
**Last Updated**: 2025-11-14
**Status**: Active
**Owner**: DevOps-Engineer

## Objective

Establish automated git repository hygiene and maintenance protocol enabling branch cleanup, large file detection, commit hygiene validation, tag management, repository optimization, and historical analysis ensuring repository health, storage efficiency, and development velocity with automated cleanup policies and proactive maintenance.

## Trigger

- Scheduled repository maintenance (daily branch cleanup, weekly optimization)
- Repository size exceeding threshold (>1GB, >5GB)
- Large file detection in pull requests requiring intervention
- Stale branch accumulation (>50 branches, >100 branches)
- Post-release tag management requiring verification
- Pre-migration repository preparation
- Developer request for repository analysis

## Agents

**Primary**: DevOps-Engineer
**Supporting**: Backend-Engineer, SRE, Infrastructure-Engineer
**Review**: Technical-Lead, Engineering-Leadership
**Orchestration**: Orchestrator (CORE-COORD-002)

## Prerequisites

- Git repository with full history access
- Branch protection rules configured
- CI/CD integration for automation
- Git LFS configuration (if applicable)
- Repository access permissions
- Backup/restore procedures
- Notification system for stakeholders

## Steps

### Step 1: Repository Analysis and Health Assessment (Estimated Time: 15 minutes)
**Action**: Analyze repository metrics for size, branches, commits, large files

**Analysis Metrics**:
```bash
# Repository size and object count
git count-objects -vH

# Branch statistics
echo "Total branches: $(git branch -a | wc -l)"
echo "Stale branches (>90 days): $(git for-each-ref --sort=-committerdate refs/heads/ --format='%(refname:short) %(committerdate:relative)' | grep -c 'month\|year')"

# Large file detection (>10MB)
git rev-list --objects --all | \
  git cat-file --batch-check='%(objecttype) %(objectname) %(objectsize) %(rest)' | \
  awk '$1 == "blob" && $3 > 10485760 {print $3/1048576 "MB", $4}' | \
  sort -rn

# Commit distribution
git shortlog -sn --all --no-merges | head -20
```

**Expected Outcome**: Comprehensive repository health report with size, branch count, large files identified
**Validation**: Metrics accurate, baseline established, issues identified

### Step 2: Stale Branch Identification and Cleanup (Estimated Time: 20 minutes)
**Action**: Identify and remove stale branches following cleanup policies

**Branch Cleanup Policy**:
- **Merged branches**: Delete after 30 days post-merge
- **Unmerged inactive branches**: Flag after 90 days, delete after 180 days with owner approval
- **Protected branches**: main, master, develop, release/* (never auto-delete)
- **Feature branches**: Delete after successful merge and release

**Cleanup Script**:
```bash
#!/bin/bash
# Stale branch cleanup with safety checks

DAYS_STALE=90
DRY_RUN=false

# Find merged branches older than 30 days
git branch --merged main --format='%(refname:short) %(committerdate:iso8601)' | while read branch date; do
  if [[ "$branch" != "main" && "$branch" != "master" && "$branch" != "develop" ]]; then
    days_old=$(( ( $(date +%s) - $(date -d "$date" +%s) ) / 86400 ))
    if [ $days_old -gt 30 ]; then
      echo "Deleting merged branch: $branch (${days_old} days old)"
      [[ "$DRY_RUN" == false ]] && git branch -d "$branch"
    fi
  fi
done

# Flag stale unmerged branches
git for-each-ref --sort=-committerdate refs/heads/ --format='%(refname:short) %(committerdate:relative) %(authorname)' | \
  grep -E 'month|year' | \
  while read branch age author; do
    echo "STALE UNMERGED: $branch - Last commit: $age by $author"
  done
```

**Expected Outcome**: Stale branches deleted, repository streamlined, notifications sent
**Validation**: Only safe deletions performed, protected branches untouched, audit log created

### Step 3: Large File Detection and Remediation (Estimated Time: 30 minutes)
**Action**: Identify large files and migrate to Git LFS or external storage

**Large File Handling**:
```bash
#!/bin/bash
# Detect and analyze large files in repository history

# Find files >5MB in entire history
git rev-list --objects --all | \
  git cat-file --batch-check='%(objecttype) %(objectname) %(objectsize) %(rest)' | \
  awk '$1 == "blob" && $3 > 5242880' | \
  sort -k3 -rn | \
  head -50 > large_files_report.txt

# For each large file, find commits
while read type sha size path; do
  echo "File: $path ($(($size / 1048576))MB)"
  git log --all --pretty=format:"%H %ai %an" --follow -- "$path" | head -5
  echo "---"
done < large_files_report.txt

# Git LFS migration for binary files
git lfs migrate import --include="*.zip,*.jar,*.war,*.tar.gz,*.mp4,*.pdf" --everything
```

**Expected Outcome**: Large files identified, LFS migration completed, storage optimized
**Validation**: Repository size reduced, LFS tracking configured, history preserved

### Step 4: Commit Hygiene and History Validation (Estimated Time: 20 minutes)
**Action**: Validate commit message quality and identify problematic commits

**Commit Quality Checks**:
```bash
#!/bin/bash
# Analyze commit message quality

# Check for conventional commits compliance
git log --pretty=format:"%s" --since="1 month ago" | \
  grep -vE '^(feat|fix|docs|style|refactor|test|chore|perf|ci|build|revert)(\(.+\))?:' | \
  head -20 > non_conventional_commits.txt

# Identify large commits (>1000 files changed)
git log --since="6 months ago" --numstat --pretty=format:"%H %s" | \
  awk '
    /^[0-9a-f]{40}/ {hash=$1; msg=$0; files=0; next}
    {files++}
    END {if (files > 1000) print hash, files, msg}
  ' > large_commits.txt

# Find commits without issue references
git log --pretty=format:"%H %s" --since="1 month ago" | \
  grep -viE '#[0-9]+|JIRA-[0-9]+|closes|fixes|resolves' | \
  head -20 > commits_without_issue_refs.txt
```

**Expected Outcome**: Commit quality report with recommendations for improvement
**Validation**: Problematic patterns identified, team guidelines updated

### Step 5: Tag Management and Release Verification (Estimated Time: 15 minutes)
**Action**: Validate tags, clean up unofficial tags, verify semantic versioning

**Tag Management**:
```bash
#!/bin/bash
# Tag validation and cleanup

# List all tags with creation dates
git for-each-ref --sort=-creatordate --format '%(refname:short) %(creatordate:short) %(subject)' refs/tags

# Identify non-semantic version tags
git tag -l | grep -vE '^v?[0-9]+\.[0-9]+\.[0-9]+(-[a-zA-Z0-9.]+)?$' > non_semver_tags.txt

# Verify tag signatures (if using signed tags)
git tag -v $(git tag -l | head -10) 2>&1 | grep -E 'Good|BAD'

# Delete local tags not on remote
git fetch --prune origin "+refs/tags/*:refs/tags/*"
comm -23 <(git tag | sort) <(git ls-remote --tags origin | awk '{print $2}' | sed 's|refs/tags/||' | sort) > orphan_tags.txt
```

**Expected Outcome**: Tags validated, semantic versioning enforced, orphan tags cleaned
**Validation**: Release tags verified, unofficial tags documented

### Step 6: Repository Optimization and Garbage Collection (Estimated Time: 25 minutes)
**Action**: Perform git garbage collection, repack objects, optimize storage

**Optimization Commands**:
```bash
#!/bin/bash
# Repository optimization with aggressive settings

echo "Before optimization:"
git count-objects -vH

# Aggressive garbage collection
git reflog expire --expire=now --all
git gc --aggressive --prune=now

# Repack with optimal settings
git repack -a -d -f --depth=250 --window=250

# Optimize pack files
git prune-packed

echo "After optimization:"
git count-objects -vH

# Calculate space savings
du -sh .git/
```

**Expected Outcome**: Repository optimized, storage reduced, performance improved
**Validation**: Size reduction achieved, no data loss, history intact

### Step 7: Maintenance Report and Policy Updates (Estimated Time: 15 minutes)
**Action**: Generate comprehensive maintenance report and update policies

**Expected Outcome**: Detailed report with metrics, actions taken, recommendations
**Validation**: Report complete, policies updated, stakeholders notified

## Expected Outputs

- **Repository Health Report**: Size, branches, commits, large files analysis
- **Branch Cleanup Summary**: Deleted branches, stale branch notifications
- **Large File Report**: Files >5MB with LFS migration plan
- **Commit Quality Analysis**: Conventional commit compliance, issue references
- **Tag Validation Report**: Semantic versioning compliance, orphan tags
- **Optimization Results**: Storage savings, performance improvements
- **Success Indicators**: >30% size reduction, <10 stale branches, 100% tag compliance

## Rollback/Recovery

**Trigger**: Accidental branch deletion, data loss, repository corruption

**P-RECOVERY Integration**:
1. Restore deleted branches from reflog: `git reflog` → `git checkout -b recovered-branch <commit-hash>`
2. Recover from backup if reflog expired
3. Revert aggressive GC if objects lost: restore from `.git/objects` backup

**Verification**: All branches restored, commit history intact, no data loss
**Data Integrity**: Critical - Always backup before aggressive operations

## Failure Handling

### Failure Scenario 1: Accidental Protected Branch Deletion
- **Symptoms**: Critical branch deleted despite protection rules
- **Root Cause**: Protection rules not properly configured, admin override
- **Impact**: Critical - Development blocked, release process disrupted
- **Resolution**:
  1. Immediate recovery from reflog: `git reflog` → identify commit → `git checkout -b branch-name <commit>`
  2. Restore branch protection rules
  3. Verify branch integrity with last known good commit
  4. Notify all developers of restoration
  5. Post-mortem on protection rule failure
- **Prevention**: Enforce branch protection via GitHub API, audit admin actions, test protection rules

### Failure Scenario 2: Repository Corruption After Aggressive GC
- **Symptoms**: Objects missing, `git fsck` errors, history inaccessible
- **Root Cause**: Aggressive GC with active operations, concurrent writes
- **Impact**: Critical - Repository unusable, data loss risk
- **Resolution**:
  1. Abort aggressive GC immediately
  2. Restore from `.git` backup (pre-GC snapshot)
  3. Run `git fsck --full` to identify corruption
  4. Recover missing objects from remote: `git fetch origin --all`
  5. Verify repository integrity before allowing access
- **Prevention**: Exclusive lock during GC, incremental optimization, tested backup/restore

### Failure Scenario 3: Large File Removal Breaking History
- **Symptoms**: Commits referencing removed files cause checkout failures
- **Root Cause**: BFG/filter-branch removing files without proper history rewrite
- **Impact**: High - History rewriting required, developer coordination needed
- **Resolution**:
  1. Restore original repository from backup
  2. Use Git LFS migration instead of history rewriting
  3. Document large file handling process
  4. Coordinate force-push with all developers
  5. Verify all references updated
- **Prevention**: Git LFS for large files, avoid history rewriting, coordinate migrations

### Failure Scenario 4: Stale Branch Deletion with Unmerged Work
- **Symptoms**: Developer discovers work deleted, no local backup
- **Root Cause**: Branch considered stale but contained unreleased work
- **Impact**: Medium - Work lost, developer productivity impacted
- **Resolution**:
  1. Search reflog for deleted branch: `git reflog | grep branch-name`
  2. Restore branch from commit hash
  3. Notify developer and merge/rebase work
  4. Update stale branch policy with better notification
  5. Implement pre-deletion review for unmerged branches
- **Prevention**: 30-day warning before deletion, developer notification, unmerged work protection

### Failure Scenario 5: Tag Deletion Breaking Release Pipeline
- **Symptoms**: CI/CD pipeline fails due to missing release tag
- **Root Cause**: Tag cleanup deleted active release tag
- **Impact**: High - Release process broken, deployments blocked
- **Resolution**:
  1. Restore tag from remote: `git fetch origin refs/tags/v1.2.3:refs/tags/v1.2.3`
  2. If not on remote, recreate tag at known release commit
  3. Push tag to remote with force: `git push origin refs/tags/v1.2.3`
  4. Verify CI/CD pipeline recovery
  5. Update tag protection rules
- **Prevention**: Protect release tags, semantic version validation, tag retention policy

### Failure Scenario 6: Repository Size Not Reduced After Cleanup
- **Symptoms**: Cleanup completed but repository size unchanged
- **Root Cause**: References preventing garbage collection, objects still reachable
- **Impact**: Medium - Storage goals not met, optimization ineffective
- **Resolution**:
  1. Identify lingering references: `git for-each-ref` → check reflog, stashes
  2. Expire reflog aggressively: `git reflog expire --expire=now --all`
  3. Clear stashes: `git stash clear`
  4. Re-run GC: `git gc --aggressive --prune=now`
  5. Analyze remaining large objects with detailed audit
- **Prevention**: Pre-cleanup reference audit, realistic size expectations, gradual optimization

## Validation Criteria

### Quantitative Thresholds
- Repository size reduction: ≥30% for repositories >1GB
- Stale branch cleanup: ≤10 branches remaining >90 days old
- Large file remediation: ≥90% files >10MB migrated to LFS
- Tag compliance: 100% release tags follow semantic versioning
- Commit message quality: ≥80% conventional commit compliance
- Optimization time: ≤60 minutes total maintenance window

### Boolean Checks
- Repository health analysis completed: Pass/Fail
- Branch cleanup executed safely: Pass/Fail
- Large files identified and addressed: Pass/Fail
- Tags validated and cleaned: Pass/Fail
- Repository optimization successful: Pass/Fail
- Maintenance report generated: Pass/Fail

### Qualitative Assessments
- Repository cleanliness: Development team feedback (≥4/5)
- Cleanup safety and correctness: Technical lead review (≥4/5)
- Developer impact minimization: Team survey (≥4/5)

**Overall Success**: Thresholds met AND boolean checks pass AND assessments ≥4/5

## HITL Escalation

### Automatic Triggers
- Protected branch deletion detected
- Repository corruption after optimization
- Stale branch with unmerged critical work
- Repository size not reduced after cleanup

### Manual Triggers
- Branch deletion policy disputes
- Large file migration strategy decisions
- Tag management exceptions
- Aggressive optimization approval

### Escalation Procedure
1. **Level 1**: DevOps-Engineer analysis and safe recovery
2. **Level 2**: Technical Lead for policy decisions
3. **Level 3**: Engineering Leadership for process changes
4. **Level 4**: Executive approval for force-push operations

## Related Protocols

### Upstream
- **Git Workflow**: Defines branching strategy requiring cleanup
- **CI/CD Pipeline**: Triggers automated maintenance jobs

### Downstream
- **P-RECOVERY**: Handles branch/tag restoration
- **Backup Procedures**: Provides recovery points
- **Developer Onboarding**: Documents repository hygiene practices

### Alternatives
- **Manual Cleanup**: Periodic manual review vs. automated
- **No Cleanup**: Accept repository growth vs. proactive maintenance

## Test Scenarios

### Happy Path

#### Scenario 1: Successful Weekly Maintenance Run
- **Setup**: Repository with 45 stale branches, 25GB size, 15 large files
- **Execution**: Run P-GIT-CLEANUP automated maintenance
- **Expected Result**: 40 branches deleted, repository reduced to 18GB, LFS migration complete
- **Validation**: No data loss, all active work preserved, 28% size reduction

### Failure Scenarios

#### Scenario 2: Accidental Branch Deletion Recovery
- **Setup**: Stale branch cleanup accidentally deletes feature branch with unreleased work
- **Execution**: Developer reports missing branch, run recovery procedure
- **Expected Result**: Branch restored from reflog, work recovered, policy updated
- **Validation**: All commits recovered, developer productivity restored

### Edge Cases

#### Scenario 3: Repository Optimization During Active Development
- **Setup**: GC triggered while developers actively pushing commits
- **Execution**: Concurrent operations cause temporary corruption
- **Expected Result**: GC aborted, repository recovered from backup, maintenance rescheduled
- **Validation**: No data loss, maintenance window policy enforced

## Metadata

### Version History
| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0 | 2025-10-10 | Initial protocol for Epic 111. Git repository hygiene with branch cleanup, large file detection, 6 failure scenarios. | DevOps-Engineer |

### Review Cycle
- **Frequency**: Quarterly
- **Next Review**: 2026-01-10
- **Reviewers**: DevOps-Engineer lead, Technical leads, SRE

### Compliance Status
- **Framework Standards**: ✅ Compliant
- **Repository Maintenance**: Required
- **Last Validation**: 2025-10-10

## Performance SLOs

- **Maintenance window**: ≤60 minutes
- **Repository size reduction**: ≥30% (for repos >1GB)
- **Stale branch cleanup**: ≤10 branches >90 days
- **Large file remediation**: ≥90% files >10MB migrated
- **Zero data loss**: 100% recovery capability
