# SCM-SBOM: Software Bill of Materials Lifecycle Management Protocol

**Version**: 1.0
**Last Updated**: 2025-11-18
**Status**: Active
**Owner**: DevOps-Engineer

## Objective

Establish comprehensive Software Bill of Materials (SBOM) lifecycle management protocol enabling automated generation, validation, distribution, and consumption of machine-readable SBOMs (SPDX 2.2/CycloneDX 1.4) throughout the software development and deployment pipeline, ensuring software supply chain transparency, vulnerability tracking, compliance validation, and integration with security tooling for dependency risk assessment and license compliance across all software artifacts.

## Tool Requirements

- **TOOL-SEC-003** (SCA Scanner): Software composition analysis and SBOM generation
  - Execute: Dependency analysis, SBOM generation, component identification, license analysis, vulnerability correlation
  - Integration: Syft, SPDX tools, CycloneDX generators, package managers, dependency analyzers
  - Usage: SBOM generation, dependency inventory, component analysis, license compliance, vulnerability tracking

- **TOOL-CICD-001** (Pipeline Platform): SBOM automation and distribution pipeline
  - Execute: Automated SBOM generation, pipeline integration, artifact distribution, deployment coordination
  - Integration: CI/CD platforms, build systems, artifact repositories, deployment automation, container registries
  - Usage: SBOM automation, pipeline integration, artifact management, deployment coordination, distribution automation

- **TOOL-COLLAB-001** (GitHub Integration): SBOM documentation, version control, and team coordination
  - Execute: SBOM version control, documentation management, team coordination, compliance tracking
  - Integration: CLI commands (gh, git), API calls, repository operations, documentation management, collaboration workflows
  - Usage: SBOM version control, documentation coordination, team collaboration, compliance documentation, artifact tracking

- **TOOL-SEC-011** (Compliance): SBOM compliance validation and audit trail management
  - Execute: Compliance validation, audit trail maintenance, regulatory reporting, governance enforcement
  - Integration: Compliance frameworks, audit systems, regulatory platforms, governance tools, SBOM validators
  - Usage: Compliance validation, audit preparation, regulatory compliance, governance enforcement, SBOM attestation

- **TOOL-INFRA-001** (Infrastructure Platform): Container and artifact management for SBOM distribution
  - Execute: Container SBOM management, artifact storage, distribution coordination, infrastructure integration
  - Integration: Container registries, artifact repositories, infrastructure management, storage systems
  - Usage: Container SBOM management, artifact distribution, infrastructure coordination, storage management

## Trigger

- New software build or release creation in CI/CD pipeline
- Dependency updates, upgrades, or version changes requiring SBOM refresh
- Pull request merge triggering automated SBOM generation
- Container image build completion requiring SBOM attachment
- Scheduled SBOM refresh for compliance reporting and audit requirements
- Security vulnerability scanning requesting current dependency inventory
- Software distribution or deployment requiring SBOM attestation
- Compliance audit requesting software composition evidence
- Integration with P-DEVSECOPS pipeline security gates
- Manual SBOM generation request for legacy or third-party components

## Agents

**Primary**: DevOps-Engineer
**Supporting**: Security-Auditor, Backend-Engineer, Infrastructure-Engineer, Compliance-Officer
**Review**: CISO, Security-Architecture-Board, Compliance-Committee, Supply-Chain-Security-Team
**Orchestration**: Orchestrator (CORE-COORD-002 hub-and-spoke coordination)

## Prerequisites

- Build environment with dependency resolution capabilities (npm, pip, Maven, Go modules, Cargo)
- SBOM generation tools installed and configured:
  - Syft (general-purpose SBOM generator)
  - SPDX-tools (SPDX format generation and validation)
  - CycloneDX tooling (CycloneDX format generation)
  - Trivy (container image SBOM generation)
- Access to dependency repositories and artifact registries (npm, PyPI, Maven Central, DockerHub)
- Digital signing infrastructure with valid certificates for SBOM integrity
- Storage and distribution infrastructure for SBOM artifacts (artifact registry, S3, CDN)
- Vulnerability database access for dependency risk assessment
- License compliance database for open-source license validation
- CI/CD pipeline integration with SBOM generation hooks
- SBOM registry or repository for centralized SBOM management

## Steps

### Step 1: Build Environment Analysis and Dependency Discovery (Estimated Time: 10 minutes)

**Action**: DevOps-Engineer with Security-Auditor analyze build environment and discover all software dependencies

**Dependency Discovery Framework**:
```python
class DependencyDiscoveryFramework:
    def __init__(self):
        self.package_manager_scanner = PackageManagerScanner()
        self.source_code_analyzer = SourceCodeDependencyAnalyzer()
        self.container_layer_inspector = ContainerLayerInspector()
        self.transitive_dependency_resolver = TransitiveDependencyResolver()

    def discover_all_dependencies(self, build_context):
        """Comprehensive dependency discovery across all ecosystems"""
        dependencies = {
            'direct_dependencies': self._scan_direct_dependencies(build_context),
            'transitive_dependencies': self._resolve_transitive_dependencies(build_context),
            'development_dependencies': self._identify_dev_dependencies(build_context),
            'runtime_dependencies': self._identify_runtime_dependencies(build_context),
            'container_dependencies': self._scan_container_layers(build_context),
            'system_dependencies': self._discover_system_packages(build_context)
        }
        return dependencies

    def _scan_direct_dependencies(self, build_context):
        """Scan package manager manifests for direct dependencies"""
        direct_deps = {
            'python': self._scan_python_dependencies(build_context),
            'javascript': self._scan_javascript_dependencies(build_context),
            'java': self._scan_java_dependencies(build_context),
            'go': self._scan_go_dependencies(build_context),
            'rust': self._scan_rust_dependencies(build_context),
            'ruby': self._scan_ruby_dependencies(build_context),
            'php': self._scan_php_dependencies(build_context),
            'dotnet': self._scan_dotnet_dependencies(build_context)
        }
        return direct_deps

    def _scan_python_dependencies(self, build_context):
        """Scan Python dependencies from requirements.txt, Pipfile, pyproject.toml"""
        python_deps = []

        # requirements.txt parsing
        if build_context.has_file('requirements.txt'):
            with open('requirements.txt') as f:
                for line in f:
                    if line.strip() and not line.startswith('#'):
                        package_spec = self._parse_python_package_spec(line)
                        python_deps.append(package_spec)

        # Pipfile parsing
        if build_context.has_file('Pipfile'):
            pipfile_deps = self._parse_pipfile(build_context.read_file('Pipfile'))
            python_deps.extend(pipfile_deps)

        # pyproject.toml parsing
        if build_context.has_file('pyproject.toml'):
            pyproject_deps = self._parse_pyproject_toml(build_context.read_file('pyproject.toml'))
            python_deps.extend(pyproject_deps)

        return python_deps

    def _scan_javascript_dependencies(self, build_context):
        """Scan JavaScript/TypeScript dependencies from package.json and package-lock.json"""
        js_deps = []

        if build_context.has_file('package.json'):
            package_json = build_context.read_json('package.json')

            # Direct dependencies
            if 'dependencies' in package_json:
                for pkg_name, version_spec in package_json['dependencies'].items():
                    js_deps.append({
                        'name': pkg_name,
                        'version_spec': version_spec,
                        'type': 'runtime',
                        'ecosystem': 'npm'
                    })

            # Development dependencies
            if 'devDependencies' in package_json:
                for pkg_name, version_spec in package_json['devDependencies'].items():
                    js_deps.append({
                        'name': pkg_name,
                        'version_spec': version_spec,
                        'type': 'development',
                        'ecosystem': 'npm'
                    })

        # Resolve exact versions from package-lock.json
        if build_context.has_file('package-lock.json'):
            package_lock = build_context.read_json('package-lock.json')
            exact_versions = self._extract_exact_versions(package_lock)
            js_deps = self._merge_exact_versions(js_deps, exact_versions)

        return js_deps
```

**Dependency Discovery Automation**:
```bash
#!/bin/bash
# SBOM Dependency Discovery Automation

BUILD_ID="$1"
SOURCE_DIR="$2"
OUTPUT_DIR="$3"

echo "=== SBOM Dependency Discovery ==="
echo "Build ID: $BUILD_ID"
echo "Source Directory: $SOURCE_DIR"
echo "Output Directory: $OUTPUT_DIR"
echo "Timestamp: $(date -u +%Y-%m-%dT%H:%M:%SZ)"

cd "$SOURCE_DIR"
mkdir -p "$OUTPUT_DIR/dependency-discovery"

# Python dependency discovery
if [ -f "requirements.txt" ] || [ -f "Pipfile" ] || [ -f "pyproject.toml" ]; then
    echo "📦 Discovering Python dependencies..."

    # Using pipdeptree for transitive dependencies
    if command -v pipdeptree &> /dev/null; then
        pipdeptree --json > "$OUTPUT_DIR/dependency-discovery/python-deps.json"
        echo "✅ Python dependency tree generated"
    fi

    # Using pip-licenses for license information
    if command -v pip-licenses &> /dev/null; then
        pip-licenses --format=json --with-urls > "$OUTPUT_DIR/dependency-discovery/python-licenses.json"
        echo "✅ Python license information extracted"
    fi
fi

# JavaScript/TypeScript dependency discovery
if [ -f "package.json" ]; then
    echo "📦 Discovering JavaScript/TypeScript dependencies..."

    # Generate dependency tree
    npm list --json --all > "$OUTPUT_DIR/dependency-discovery/npm-deps.json" 2>/dev/null || true

    # License information
    if command -v license-checker &> /dev/null; then
        npx license-checker --json > "$OUTPUT_DIR/dependency-discovery/npm-licenses.json"
        echo "✅ NPM license information extracted"
    fi
fi

# Java dependency discovery
if [ -f "pom.xml" ] || [ -f "build.gradle" ]; then
    echo "📦 Discovering Java dependencies..."

    # Maven dependencies
    if [ -f "pom.xml" ] && command -v mvn &> /dev/null; then
        mvn dependency:tree -DoutputType=json -DoutputFile="$OUTPUT_DIR/dependency-discovery/maven-deps.json"
        echo "✅ Maven dependency tree generated"
    fi

    # Gradle dependencies
    if [ -f "build.gradle" ] && command -v gradle &> /dev/null; then
        gradle dependencies --console=plain > "$OUTPUT_DIR/dependency-discovery/gradle-deps.txt"
        echo "✅ Gradle dependency tree generated"
    fi
fi

# Go dependency discovery
if [ -f "go.mod" ]; then
    echo "📦 Discovering Go dependencies..."

    go list -m -json all > "$OUTPUT_DIR/dependency-discovery/go-deps.json"
    go mod graph > "$OUTPUT_DIR/dependency-discovery/go-mod-graph.txt"
    echo "✅ Go dependency information extracted"
fi

# Rust dependency discovery
if [ -f "Cargo.toml" ]; then
    echo "📦 Discovering Rust dependencies..."

    if command -v cargo &> /dev/null; then
        cargo tree --format=json > "$OUTPUT_DIR/dependency-discovery/cargo-deps.json"
        echo "✅ Cargo dependency tree generated"
    fi
fi

# Container image dependency discovery (if Dockerfile present)
if [ -f "Dockerfile" ]; then
    echo "📦 Discovering container image dependencies..."

    # Build container image temporarily for analysis
    IMAGE_NAME="sbom-analysis:$BUILD_ID"
    docker build -t "$IMAGE_NAME" . > /dev/null 2>&1

    # Use Syft for container image analysis
    if command -v syft &> /dev/null; then
        syft "$IMAGE_NAME" -o json > "$OUTPUT_DIR/dependency-discovery/container-deps.json"
        echo "✅ Container dependency analysis completed"
    fi

    # Cleanup temporary image
    docker rmi "$IMAGE_NAME" > /dev/null 2>&1
fi

echo "✅ Dependency discovery completed"
echo "📁 Discovery artifacts: $OUTPUT_DIR/dependency-discovery/"
```

**Expected Outcome**: Comprehensive dependency inventory across all package ecosystems and dependency types
**Validation**: All dependency manifests discovered, transitive dependencies resolved, dependency metadata extracted

### Step 2: SBOM Generation in Standard Format (SPDX/CycloneDX) (Estimated Time: 15 minutes)

**Action**: DevOps-Engineer generate machine-readable SBOM in SPDX 2.2 or CycloneDX 1.4 format with complete dependency metadata

**SBOM Generation Framework**:
```python
class SBOMGenerationFramework:
    def __init__(self):
        self.spdx_generator = SPDXGenerator()
        self.cyclonedx_generator = CycloneDXGenerator()
        self.metadata_enricher = SBOMMetadataEnricher()
        self.format_validator = SBOMFormatValidator()

    def generate_sbom(self, dependencies, build_context, sbom_format='spdx'):
        """Generate SBOM in specified format with comprehensive metadata"""
        sbom = {
            'format': sbom_format,
            'spec_version': self._get_spec_version(sbom_format),
            'metadata': self._generate_metadata(build_context),
            'components': self._convert_dependencies_to_components(dependencies),
            'relationships': self._identify_relationships(dependencies),
            'vulnerabilities': self._enrich_vulnerability_data(dependencies),
            'licenses': self._extract_license_information(dependencies)
        }

        if sbom_format == 'spdx':
            return self.spdx_generator.generate(sbom)
        elif sbom_format == 'cyclonedx':
            return self.cyclonedx_generator.generate(sbom)
        else:
            raise ValueError(f"Unsupported SBOM format: {sbom_format}")
```

**SBOM Generation Automation**:
```bash
#!/bin/bash
# SBOM Generation Automation

BUILD_ID="$1"
SOURCE_DIR="$2"
OUTPUT_DIR="$3"
SBOM_FORMAT="${4:-spdx}"  # spdx or cyclonedx

echo "=== SBOM Generation ==="
echo "Build ID: $BUILD_ID"
echo "SBOM Format: $SBOM_FORMAT"

cd "$SOURCE_DIR"
mkdir -p "$OUTPUT_DIR/sbom"

# Generate SBOM using Syft (supports both SPDX and CycloneDX)
if command -v syft &> /dev/null; then
    echo "🔍 Generating SBOM with Syft..."

    if [ "$SBOM_FORMAT" = "spdx" ]; then
        syft "$SOURCE_DIR" -o spdx-json > "$OUTPUT_DIR/sbom/sbom.spdx.json"
        echo "✅ SPDX 2.2 SBOM generated: sbom.spdx.json"
    elif [ "$SBOM_FORMAT" = "cyclonedx" ]; then
        syft "$SOURCE_DIR" -o cyclonedx-json > "$OUTPUT_DIR/sbom/sbom.cdx.json"
        echo "✅ CycloneDX 1.4 SBOM generated: sbom.cdx.json"
    fi
fi

# Enrich SBOM with additional metadata
echo "📝 Enriching SBOM metadata..."

cat > "$OUTPUT_DIR/sbom/sbom-metadata.json" <<EOF
{
  "build_id": "$BUILD_ID",
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "sbom_format": "$SBOM_FORMAT",
  "source_repository": "$(git remote get-url origin 2>/dev/null || echo 'unknown')",
  "commit_sha": "$(git rev-parse HEAD 2>/dev/null || echo 'unknown')",
  "branch": "$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo 'unknown')",
  "build_environment": {
    "os": "$(uname -s)",
    "architecture": "$(uname -m)",
    "builder": "$(whoami)@$(hostname)"
  }
}
EOF

echo "✅ SBOM generation completed"
```

**Expected Outcome**: Machine-readable SBOM generated in standard format (SPDX 2.2 or CycloneDX 1.4) with comprehensive dependency metadata
**Validation**: SBOM schema validation passes, all dependencies captured, metadata completeness verified

### Step 3: Metadata Enrichment and Vulnerability Assessment (Estimated Time: 20 minutes)

**Action**: Security-Auditor with DevOps-Engineer enrich SBOM with license, vulnerability, and security metadata

**Expected Outcome**: SBOM enriched with license compliance data, vulnerability assessments, and security risk indicators
**Validation**: License information validated, vulnerability data integrated, security metadata complete

### Step 4: Digital Signing and Integrity Verification (Estimated Time: 10 minutes)

**Action**: DevOps-Engineer cryptographically sign SBOM for integrity verification and non-repudiation

**Digital Signing Automation**:
```bash
#!/bin/bash
# SBOM Digital Signing

SBOM_FILE="$1"
OUTPUT_DIR="$2"
SIGNING_KEY="${3:-$SBOM_SIGNING_KEY}"

echo "🔐 Signing SBOM: $(basename $SBOM_FILE)"

# Sign SBOM using GPG
if command -v gpg &> /dev/null; then
    gpg --detach-sign --armor --output "$OUTPUT_DIR/sbom.sig" "$SBOM_FILE"
    echo "✅ SBOM digital signature generated: sbom.sig"
fi

# Sign using cosign for container registries
if command -v cosign &> /dev/null; then
    cosign sign-blob --key "$SIGNING_KEY" --output-signature "$OUTPUT_DIR/sbom.cosign.sig" "$SBOM_FILE"
    echo "✅ Cosign signature generated: sbom.cosign.sig"
fi

# Generate checksum
sha256sum "$SBOM_FILE" > "$OUTPUT_DIR/sbom.sha256"
echo "✅ SHA256 checksum generated: sbom.sha256"
```

**Expected Outcome**: SBOM cryptographically signed with digital signature for integrity verification
**Validation**: Digital signature valid, checksum verified, signing certificate trusted

### Step 5: SBOM Schema Validation and Compliance Verification (Estimated Time: 10 minutes)

**Action**: DevOps-Engineer validate SBOM against official schema and NTIA minimum elements

**Expected Outcome**: SBOM validated against official SPDX/CycloneDX schema and NTIA minimum elements
**Validation**: Schema validation passes, NTIA minimum elements present, compliance requirements met

### Step 6: SBOM Distribution and Artifact Attachment (Estimated Time: 10 minutes)

**Action**: DevOps-Engineer publish SBOM alongside software artifacts in artifact registry

**Expected Outcome**: SBOM distributed with software artifacts in all distribution channels
**Validation**: SBOM available in artifact registry, accessible via standard URLs, integrity maintained

### Step 7: SBOM Registry Integration and Searchability (Estimated Time: 15 minutes)

**Action**: DevOps-Engineer register SBOM in organizational SBOM registry with searchable metadata

**Expected Outcome**: SBOM registered in centralized registry with searchable metadata and query capabilities
**Validation**: SBOM searchable by component, vulnerability, license, version, and other metadata

## Expected Outputs

- **Primary Artifact**: `sbom.spdx.json` or `sbom.cdx.json` - Machine-readable SBOM in SPDX 2.2 or CycloneDX 1.4 format
- **Digital Signature**: `sbom.sig` - Cryptographic signature for SBOM integrity verification
- **Checksum File**: `sbom.sha256` - SHA256 checksum for SBOM integrity validation
- **Metadata File**: `sbom-metadata.json` - Build context and enrichment metadata
- **Registry Entry**: SBOM registered in organizational artifact registry with searchable metadata
- **Integration Hooks**: Vulnerability scanning system integration, license compliance database updates
- **Compliance Reports**: NTIA minimum elements validation, schema compliance verification
- **Distribution URLs**: Public and internal URLs for SBOM artifact access
- **Success Indicators**: 100% dependency coverage, schema validation passed, digital signature valid

## Rollback/Recovery

**Trigger**: Critical failure during Steps 2-7 (SBOM generation, signing, distribution)

**Standard Approach**: Invoke **P-RECOVERY** protocol for SBOM artifact rollback and regeneration

**P-RECOVERY Integration**:
1. Before Step 2: CreateBranch to create isolated SBOM generation workspace (`sbom_${BUILD_ID}_${timestamp}`)
2. Execute Steps 2-7 with checkpoints after each SBOM generation and validation stage
3. On success: MergeBranch commits SBOM artifacts and registry entries atomically
4. On failure: DiscardBranch triggers SBOM regeneration, preserves diagnostic artifacts
5. P-RECOVERY handles retry logic with exponential backoff (3 SBOM generation attempts)
6. P-RECOVERY escalates to NotifyHuman if SBOM generation persistently fails

**Custom Rollback** (SBOM-specific):
1. If generation failure: Retry with alternative SBOM tools (Syft → SPDX-tools → CycloneDX CLI)
2. If signing failure: Verify certificate validity, retry signing with backup certificates
3. If distribution failure: Use alternative distribution channels, escalate if all channels fail
4. If registry integration failure: Queue SBOM for manual registration, notify operations team

**Verification**: SBOM generated and signed successfully, distribution channels operational, registry updated
**Data Integrity**: Medium risk - SBOM artifacts must be regenerated accurately, signatures must remain valid

## Failure Handling

### Failure Scenario 1: Dependency Discovery Incomplete
- **Symptoms**: Missing dependencies in SBOM, transitive dependencies not resolved, package manager failures
- **Root Cause**: Corrupted dependency lock files, offline package repositories, network connectivity issues
- **Impact**: High - Incomplete SBOM leads to undetected vulnerabilities and compliance gaps
- **Resolution**:
  1. Re-run dependency resolution with clean environment and updated lock files
  2. Use alternative package managers or dependency resolution tools
  3. Manually identify missing dependencies and add to SBOM
  4. Validate SBOM completeness against known dependency count
  5. Escalate to Security-Auditor for manual dependency inventory
- **Prevention**: Dependency lock file validation, package repository health checks, network stability monitoring

### Failure Scenario 2: SBOM Generation Tool Failure
- **Symptoms**: SBOM generation crashes, invalid output format, incomplete component data
- **Root Cause**: Tool version incompatibility, unsupported package ecosystem, corrupted source files
- **Impact**: Critical - No SBOM generated, blocking deployment and compliance requirements
- **Resolution**:
  1. Switch to alternative SBOM generation tool (Syft → SPDX-tools → CycloneDX CLI)
  2. Update SBOM generation tools to latest stable versions
  3. Manually construct SBOM from dependency discovery artifacts
  4. Use hybrid approach: automated generation + manual enrichment
  5. Escalate to DevOps-Engineer for tool troubleshooting
- **Prevention**: Tool version management, multi-tool fallback configuration, pre-flight tool validation

### Failure Scenario 3: Digital Signing Infrastructure Failure
- **Symptoms**: Signing failures, certificate expiration, key management issues
- **Root Cause**: Expired certificates, lost private keys, HSM connectivity issues
- **Impact**: Medium - SBOM integrity cannot be verified, compliance requirements unmet
- **Resolution**:
  1. Verify certificate validity and renew if expired
  2. Switch to backup signing certificates and key management infrastructure
  3. Generate new signing keys following secure key generation procedures
  4. Implement emergency unsigned SBOM distribution with manual integrity verification
  5. Escalate to Security-Auditor for certificate management assistance
- **Prevention**: Certificate expiration monitoring, automated renewal procedures, key backup management

### Failure Scenario 4: SBOM Distribution Infrastructure Failure
- **Symptoms**: Upload failures, network timeouts, artifact registry unavailable
- **Root Cause**: Registry downtime, network connectivity issues, storage capacity exhaustion
- **Impact**: Medium - SBOM unavailable to consumers, vulnerability scanning blocked
- **Resolution**:
  1. Retry SBOM distribution with exponential backoff
  2. Switch to alternative distribution channels (backup artifact registry, CDN, S3)
  3. Implement local SBOM caching until distribution infrastructure restored
  4. Queue SBOM for distribution retry when infrastructure recovers
  5. Escalate to Infrastructure-Engineer for registry troubleshooting
- **Prevention**: Multi-region artifact registry deployment, CDN distribution, storage capacity monitoring

### Failure Scenario 5: SBOM Schema Validation Failure
- **Symptoms**: Schema validation errors, invalid SBOM format, missing required fields
- **Root Cause**: Incorrect SBOM generation, unsupported schema version, tool bugs
- **Impact**: Medium - SBOM rejected by consuming systems, compliance validation fails
- **Resolution**:
  1. Re-generate SBOM with corrected schema version and format
  2. Manually fix schema validation errors in generated SBOM
  3. Update SBOM generation tool to support correct schema version
  4. Use schema transformation tools to convert between SPDX and CycloneDX
  5. Escalate to Security-Auditor for manual SBOM correction
- **Prevention**: Schema version compatibility testing, automated validation in CI/CD, tool version management

### Failure Scenario 6: License Compliance Violation Detection
- **Symptoms**: Copyleft license conflicts, incompatible license combinations, prohibited licenses
- **Root Cause**: New dependency with problematic license, license scanning tool updates
- **Impact**: Critical - Legal risk, compliance violation, deployment blocked
- **Resolution**:
  1. Immediately halt deployment and notify compliance and legal teams
  2. Identify specific dependencies with license issues
  3. Replace problematic dependencies with compatible alternatives
  4. Obtain legal approval for exceptional license use
  5. Update license compliance policies and dependency approval lists
- **Prevention**: Automated license scanning in CI/CD, pre-approved dependency lists, license policy enforcement

## Validation Criteria

### Quantitative Thresholds
- SBOM generation success rate: ≥99.5% of all software builds
- Dependency coverage: ≥99% of all direct and transitive dependencies captured
- SBOM generation time: ≤15 minutes (95th percentile)
- Schema validation pass rate: 100% of generated SBOMs
- Digital signature validation: 100% of signed SBOMs
- Distribution availability: ≥99.9% uptime for SBOM artifact access
- NTIA minimum elements: 100% compliance (7/7 required elements present)

### Boolean Checks
- SBOM format compliant (SPDX 2.2 or CycloneDX 1.4): Pass/Fail
- Digital signature valid and verifiable: Pass/Fail
- NTIA minimum elements present (author, supplier, component name, version, dependencies, unique ID, timestamp): Pass/Fail
- Vulnerability data integrated: Pass/Fail
- License information complete: Pass/Fail
- Registry integration operational: Pass/Fail
- Distribution channels accessible: Pass/Fail

### Qualitative Assessments
- SBOM completeness and accuracy: Security-Auditor assessment (≥4/5 rating)
- Vulnerability scanning effectiveness: Security team evaluation (≥4/5 rating)
- License compliance confidence: Compliance-Officer assessment (≥4/5 rating)
- Developer experience and usability: DevOps team feedback (≥4/5 rating)

**Overall Success**: All quantitative thresholds met AND all boolean checks pass AND qualitative assessments ≥4/5 rating

## HITL Escalation

### Automatic Triggers
- Critical license compliance violation detected requiring legal consultation
- SBOM generation failures exceeding retry limit (≥3 attempts)
- Digital signing infrastructure failure preventing integrity verification
- Distribution infrastructure complete failure blocking SBOM access
- Schema validation failures preventing SBOM consumption
- Critical vulnerability discovered in dependencies requiring immediate remediation

### Manual Triggers
- Complex licensing scenario requiring legal interpretation
- Custom SBOM format requirements for specific customers or partners
- Regulatory compliance questions requiring compliance officer input
- SBOM accuracy concerns requiring manual dependency verification
- Strategic decisions on SBOM distribution and access control

### Escalation Procedure
1. **Level 1 - DevOps Team Resolution**: DevOps-Engineer attempts automated retry and alternative tools
2. **Level 2 - Security Team Coordination**: Security-Auditor assists with vulnerability and license analysis
3. **Level 3 - Compliance and Legal**: Compliance-Officer and legal team for licensing and compliance issues
4. **Level 4 - Executive Crisis Management**: CISO and executive leadership for strategic supply chain security decisions

## Related Protocols

### Upstream (Prerequisites)
- **Software Build Process**: Provides compiled artifacts requiring SBOM generation
- **Dependency Management**: Provides dependency resolution and lock files
- **CI/CD Pipeline**: Triggers SBOM generation as part of automated builds

### Downstream (Consumers)
- **P-DEVSECOPS**: Integrates SBOM generation into security pipeline
- **SCM-SLSA**: Consumes SBOM for supply chain provenance attestation
- **SCM-VEX**: Uses SBOM for vulnerability exploitability assessment
- **P-SEC-VULN**: Leverages SBOM for dependency vulnerability scanning
- **Compliance Reporting**: Uses SBOM for regulatory compliance evidence

### Alternatives
- **Manual SBOM Creation**: Human-generated dependency inventory (slower, less comprehensive)
- **Periodic SBOM Audits**: Scheduled dependency audits vs. continuous SBOM generation
- **Vendor-Provided SBOMs**: Third-party SBOM provision vs. internal generation

## Test Scenarios

### Happy Path Scenarios

#### Scenario 1: Successful CI/CD SBOM Generation
- **Setup**: Clean build environment with all dependencies resolved and package managers functional
- **Execution**: Trigger SBOM generation in CI/CD pipeline with automated validation and distribution
- **Expected Result**: SBOM generated in SPDX 2.2 format, schema validation passed, digitally signed, distributed to artifact registry
- **Validation**: SBOM accessible via public URL, vulnerability scanning integration operational, compliance requirements met

#### Scenario 2: Multi-Language Application SBOM
- **Setup**: Application with Python, JavaScript, and Java dependencies across multiple package ecosystems
- **Execution**: Run SCM-SBOM protocol with multi-language dependency discovery and SBOM generation
- **Expected Result**: Comprehensive SBOM with all dependencies across all languages, transitive dependencies resolved
- **Validation**: All package ecosystems represented, dependency counts validated, license information complete

### Failure Scenarios

#### Scenario 3: Dependency Discovery Failure
- **Setup**: Corrupted package lock files causing dependency resolution failures
- **Execution**: Run SCM-SBOM with incomplete dependency discovery triggering retry logic
- **Expected Result**: Alternative dependency resolution methods attempted, manual dependency identification escalated
- **Validation**: Retry logic functional, alternative tools successfully used, SBOM completeness validated

#### Scenario 4: Digital Signing Infrastructure Failure
- **Setup**: Expired signing certificate preventing SBOM digital signature generation
- **Execution**: Run SCM-SBOM with signing failure triggering backup certificate usage
- **Expected Result**: Backup signing certificate used, SBOM signed successfully, certificate renewal triggered
- **Validation**: Backup procedures functional, signed SBOM validated, certificate monitoring alerted

### Edge Cases

#### Scenario 5: Monorepo with Multiple Applications
- **Setup**: Monorepo containing 10+ applications with shared and application-specific dependencies
- **Execution**: Run SCM-SBOM with per-application SBOM generation and dependency deduplication
- **Expected Result**: Individual SBOMs generated for each application, shared dependencies deduplicated, registry organized by application
- **Validation**: All applications have valid SBOMs, dependency relationships correct, no duplicate dependency entries

## Metadata

### Version History
| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0 | 2025-10-10 | Initial protocol creation for Epic 111 (Missing Protocol Development Initiative). Comprehensive 14-section enterprise-grade protocol with dependency discovery, SPDX/CycloneDX generation, digital signing, distribution, registry integration, P-RECOVERY integration, 6 failure scenarios, quantitative validation criteria, and test scenarios. | DevOps-Engineer + Claude Code (Sonnet 4.5) |

### Review Cycle
- **Frequency**: Quarterly (aligned with SBOM tooling updates and compliance requirements)
- **Next Review**: 2026-01-10
- **Reviewers**: DevOps-Engineer supervisor, Security-Auditor, CISO, Compliance-Officer

### Compliance Status
- **Framework Standards**: ✅ Compliant with 14-section protocol template
- **Security Audit**: Required (handles software supply chain security and vulnerability management)
- **Performance Validation**: Required (SBOM generation performance SLOs defined)
- **Compliance Review**: Required (NTIA minimum elements, regulatory compliance)
- **Last Validation**: 2025-10-10

## Performance SLOs

- **Dependency discovery time**: ≤10 minutes (Step 1, 95th percentile)
- **SBOM generation time**: ≤15 minutes (Step 2, 95th percentile)
- **Metadata enrichment time**: ≤20 minutes (Step 3, 95th percentile)
- **Digital signing time**: ≤10 minutes (Step 4, 95th percentile)
- **Schema validation time**: ≤10 minutes (Step 5, 95th percentile)
- **Distribution and registry time**: ≤15 minutes (Steps 6-7, 95th percentile)
- **Total SBOM lifecycle time**: ≤90 minutes (95th percentile for complete pipeline)
- **SBOM availability**: ≥99.9% uptime for artifact registry access
- **Generation success rate**: ≥99.5% of all software builds
