# P-INFRASTRUCTURE-SETUP: Environment Provisioning Protocol

**Version**: 2.0
**Last Updated**: 2025-11-18
**Status**: Active
**Owner**: DevOps-Engineer

## Objective

Establish comprehensive Infrastructure-as-Code (IaC) workflow for provisioning, configuring, and maintaining development, staging, and production environments with automated deployment pipelines, security hardening, monitoring integration, and disaster recovery capabilities to ensure scalable, reliable, and secure infrastructure that supports high-velocity development while maintaining operational excellence.

## Tool Requirements

- **TOOL-INFRA-001** (Infrastructure): Infrastructure-as-Code provisioning, resource management, and environment orchestration
  - Execute: IaC provisioning, resource management, environment orchestration, infrastructure automation, deployment coordination
  - Integration: Infrastructure platforms (Terraform, CloudFormation, Pulumi), cloud providers, automation tools, orchestration systems
  - Usage: Infrastructure provisioning, resource management, environment setup, deployment orchestration, infrastructure automation

- **TOOL-INFRA-002** (Container Platform): Container orchestration, microservices deployment, and containerized workload management
  - Execute: Container orchestration, microservices deployment, containerized workload management, service coordination, container automation
  - Integration: Container platforms (Kubernetes, Docker, ECS), orchestration tools, container registries, service mesh platforms
  - Usage: Container deployment, microservices orchestration, containerized infrastructure, service management, container automation

- **TOOL-SEC-009** (Infrastructure Security): Infrastructure security hardening, compliance validation, and security automation
  - Execute: Infrastructure security hardening, compliance validation, security automation, vulnerability management, security monitoring
  - Integration: Security tools, compliance frameworks, vulnerability scanners, security automation, monitoring systems
  - Usage: Infrastructure security, compliance validation, security hardening, vulnerability management, security automation

- **TOOL-MON-001** (APM): Infrastructure monitoring, performance tracking, and observability integration
  - Execute: Infrastructure monitoring, performance tracking, observability integration, metrics collection, alerting systems
  - Integration: Monitoring platforms, observability tools, metrics systems, alerting frameworks, performance monitoring
  - Usage: Infrastructure monitoring, performance tracking, observability setup, metrics collection, monitoring automation

## Agent
Primary: DevOps-Engineer
Participants: Cloud-Architect, SRE, Orchestrator (coordinator)

## Trigger
- After architecture approval (QG-PHASE2 passes)
- When new environment is required for project
- During infrastructure updates or scaling
- When disaster recovery environment needed

## Prerequisites
- Architecture specification (tech-spec.md) approved
- Technology stack approved by Human Command Group
- Cloud provider/infrastructure platform selected via **TOOL-INFRA-001** (AWS, Azure, GCP, on-prem)
- Budget and resource limits defined
- Security requirements documented via **TOOL-SEC-009**

## Steps

1. **Architecture Requirements Review**: DevOps-Engineer reviews tech-spec.md to identify infrastructure needs:
   - Compute requirements (VMs, containers, serverless)
   - Storage requirements (databases, object storage, file systems)
   - Networking requirements (VPC, subnets, load balancers, API gateways)
   - Security requirements (firewalls, WAF, DDoS protection)
   - Monitoring and logging requirements

2. **Infrastructure Component Definition**: Define IaC components using approved tools (Terraform, CloudFormation, Pulumi):
   - **Compute Layer**: EC2/ECS/Lambda (AWS), VMs/AKS/Functions (Azure), GCE/GKE/Cloud Functions (GCP)
   - **Data Layer**: RDS/DynamoDB (AWS), SQL Database/Cosmos DB (Azure), Cloud SQL/Firestore (GCP)
   - **Network Layer**: VPC, subnets (public/private), route tables, NAT gateways, load balancers
   - **Security Layer**: Security groups, IAM roles/policies, KMS encryption, Secrets Manager
   - **Observability Layer**: CloudWatch/X-Ray (AWS), Monitor/App Insights (Azure), Cloud Monitoring/Trace (GCP)

3. **Development Environment Provisioning**:
   - Create IaC templates for dev environment (scaled-down version of production)
   - Provision resources: `terraform apply` or `cloudformation deploy`
   - Configure environment variables and secrets
   - Deploy monitoring agents and log collectors
   - Validate connectivity and access
   - Document dev environment URLs and credentials

4. **Staging Environment Provisioning**:
   - Create IaC templates for staging (production mirror)
   - Provision resources with production-equivalent configurations
   - Configure SSL/TLS certificates
   - Deploy identical monitoring and alerting
   - Load representative test data
   - Validate staging mirrors production architecture

5. **CI/CD Pipeline Configuration**:
   - Configure build pipeline (GitHub Actions, Jenkins, CircleCI, GitLab CI)
   - Define deployment workflows (dev → staging → production)
   - Configure automated testing stages (unit, integration, E2E)
   - Set up artifact repositories (Docker Registry, ECR, Artifactory)
   - Implement deployment gates and approvals
   - Test pipeline with sample deployment

6. **Network and Security Hardening**:
   - Apply principle of least privilege (IAM roles)
   - Configure network ACLs and security groups (whitelist approach)
   - Enable encryption at rest and in transit
   - Configure VPN/bastion hosts for secure access
   - Enable audit logging (CloudTrail, Activity Log, Cloud Audit Logs)
   - Run security baseline scan (AWS Inspector, Azure Security Center)

7. **Database Provisioning and Migration Setup**:
   - Provision database instances (RDS, Aurora, etc.)
   - Configure backup policies (automated snapshots, retention)
   - Set up read replicas for scalability
   - Configure connection pooling
   - Create migration framework (Alembic, Flyway, Liquibase)
   - Test database connectivity from application tier

8. **Monitoring and Alerting Setup**:
   - Deploy monitoring stack (Prometheus, Grafana, Datadog)
   - Configure metrics collection (CPU, memory, disk, network, application metrics)
   - Set up centralized logging (ELK, CloudWatch Logs, Stackdriver)
   - Define alerting rules (service down, high latency, error rate spikes)
   - Create dashboards for environment health visualization
   - Test alert notifications (Slack, PagerDuty, email)

9. **Environment Validation (Pre-QG-PHASE3)**:
   - Run health checks on all services
   - Verify network connectivity (service-to-service, internet, databases)
   - Test authentication and authorization mechanisms
   - Validate SSL/TLS certificates
   - Confirm monitoring and logging operational
   - Measure baseline performance metrics

10. **Documentation and Handoff**:
    - Create environment runbook (access procedures, troubleshooting)
    - Document IaC repository structure and deployment process
    - Record environment URLs, credentials (store securely in vault)
    - Provide architecture diagrams with deployed resources
    - Hand off to QA-Tester for QG-PHASE3 validation
    - Notify Orchestrator that Phase 3 deliverables ready for gate

## Expected Outputs
- Provisioned environments (development, staging)
- Infrastructure-as-Code repository (Terraform/CloudFormation modules)
- CI/CD pipeline configured and tested
- Environment documentation and runbooks
- Access credentials (stored in Secrets Manager/Vault)
- Network topology diagrams
- Monitoring dashboards and alert configurations
- Environment health baseline metrics

## Failure Handling

### Failure Scenario 1: Infrastructure Provisioning Cascade Failure
- **Symptoms**: Multiple infrastructure components failing during provisioning, dependency chain breakdowns, resource allocation failures
- **Root Cause**: Resource quota limits exceeded, region/zone unavailability, IAM permission issues, circular dependencies in IaC
- **Impact**: Critical - Complete environment unavailable, development workflow blocked, deployment pipeline halted
- **Resolution**:
  1. **Immediate Rollback**: Execute `terraform destroy` to clean up partial infrastructure state
  2. **Resource Quota Analysis**: Check cloud provider quotas and request increases if needed
  3. **Dependency Graph Review**: Analyze IaC dependency chains and resolve circular dependencies
  4. **Alternative Region Deployment**: Deploy to backup region if primary region experiencing issues
  5. **Progressive Provisioning**: Break down large infrastructure deployments into smaller, manageable components
  6. **P-RECOVERY Integration**: Use git-based IaC versioning for infrastructure state recovery
- **Prevention**: Quota monitoring, multi-region strategies, dependency validation, infrastructure testing

### Failure Scenario 2: Network Security Configuration Failure
- **Symptoms**: Network connectivity issues, security group misconfigurations, VPN/bastion access failures, firewall rule conflicts
- **Root Cause**: Incorrect CIDR blocks, overlapping IP ranges, misconfigured security groups, routing table errors
- **Impact**: High - Environments isolated, security posture compromised, access control broken
- **Resolution**:
  1. **Network Topology Analysis**: Validate VPC configurations, subnet allocations, and routing tables
  2. **Security Group Audit**: Review security group rules for least privilege and proper access control
  3. **Connectivity Testing**: Systematic testing of network paths and access controls
  4. **DNS and Routing Verification**: Ensure proper DNS resolution and routing configuration
  5. **Security Baseline Restoration**: Revert to known-good security configuration templates
  6. **Progressive Security Hardening**: Apply security configurations incrementally with validation
- **Prevention**: Network topology validation, security configuration templates, automated testing

### Failure Scenario 3: CI/CD Pipeline Infrastructure Integration Failure
- **Symptoms**: Build agents unable to connect to infrastructure, deployment failures, artifact storage issues
- **Root Cause**: Service account permissions, network connectivity, secret management failures, pipeline configuration errors
- **Impact**: High - Deployment pipeline broken, development velocity halted, release capability compromised
- **Resolution**:
  1. **Service Account Permission Audit**: Verify build agent IAM roles and policy attachments
  2. **Network Connectivity Validation**: Test connectivity from CI/CD runners to target infrastructure
  3. **Secret Management Verification**: Ensure secrets are properly stored and accessible to pipeline
  4. **Pipeline Configuration Review**: Validate pipeline stages and deployment configurations
  5. **Alternative Deployment Strategy**: Implement blue-green or canary deployment as fallback
  6. **Monitoring Integration**: Enhance pipeline monitoring and failure detection
- **Prevention**: Pipeline testing, secret rotation, connectivity validation, deployment strategy redundancy

### Failure Scenario 4: Monitoring and Observability Infrastructure Failure
- **Symptoms**: Monitoring agents failing to deploy, metrics collection stopped, alerting system down, dashboard unavailable
- **Root Cause**: Agent installation failures, network connectivity issues, credential problems, resource constraints
- **Impact**: Medium - Loss of observability, incident detection capability compromised, performance visibility lost
- **Resolution**:
  1. **Monitoring Agent Diagnosis**: Check agent installation logs and network connectivity
  2. **Credential and Permission Verification**: Ensure monitoring services have proper access
  3. **Resource Allocation Assessment**: Verify adequate resources for monitoring infrastructure
  4. **Alternative Monitoring Deployment**: Use backup monitoring stack or external services
  5. **Gradual Monitoring Restoration**: Restore monitoring capabilities incrementally by priority
  6. **Monitoring Infrastructure Hardening**: Implement redundancy and failover for monitoring
- **Prevention**: Monitoring redundancy, health checks, resource monitoring, backup systems

### Failure Scenario 5: Database Infrastructure Performance Degradation
- **Symptoms**: Database connection timeouts, slow query performance, storage capacity issues, backup failures
- **Root Cause**: Inadequate resource allocation, poor configuration, storage limits, backup storage issues
- **Impact**: High - Application performance severely degraded, data persistence at risk, user experience compromised
- **Resolution**:
  1. **Database Performance Analysis**: Identify bottlenecks in CPU, memory, storage, and network
  2. **Resource Scaling**: Increase database instance size or implement read replicas
  3. **Configuration Optimization**: Tune database parameters for workload characteristics
  4. **Storage Management**: Increase storage capacity and optimize storage configuration
  5. **Backup System Restoration**: Repair backup infrastructure and validate backup integrity
  6. **Database Monitoring Enhancement**: Implement comprehensive database monitoring and alerting
- **Prevention**: Capacity planning, performance monitoring, backup testing, resource alerting

## Human-in-the-Loop (HITL) Escalation

### Automatic Escalation Triggers
- **Infrastructure Provisioning Timeout**: Environment provisioning exceeds 75 minutes (development) or 90 minutes (staging) without completion
- **Critical Security Baseline Failure**: Security scan identifies HIGH/CRITICAL vulnerabilities with CVSS score ≥7.0 during baseline validation
- **Multi-Region Deployment Failure**: Infrastructure provisioning fails in ≥2 availability zones or regions simultaneously
- **Resource Quota Exhaustion**: Cloud provider resource limits reached affecting >50% of planned infrastructure components
- **Network Connectivity Black Hole**: Complete loss of network connectivity between application tiers lasting >10 minutes
- **Database Performance Degradation**: Database response time >5 seconds or connection failure rate >20% for ≥15 minutes
- **CI/CD Pipeline Deployment Failure**: Pipeline fails ≥3 consecutive times with different error patterns
- **Monitoring Infrastructure Down**: Primary monitoring systems unavailable for >30 minutes with no fallback capability
- **SSL/TLS Certificate Failure**: Certificate provisioning or validation fails affecting HTTPS endpoints
- **Backup System Failure**: Database backup validation fails or backup storage becomes unavailable
- **IaC Validation Critical Error**: Terraform/CloudFormation validation fails with dependency conflicts
- **Cross-Environment Configuration Drift**: Staging environment configuration deviates >10% from production baseline
- **Resource Cost Anomaly**: Infrastructure costs exceed budget threshold by >25% during provisioning
- **Compliance Control Failure**: Security controls fail to meet SOC2/ISO27001 baseline requirements

### HITL Decision Points
1. **Alternative Architecture Selection**: When primary infrastructure approach fails, human expertise needed for technology stack pivot
2. **Security vs Performance Trade-offs**: Balancing security hardening requirements with application performance needs
3. **Multi-Cloud Strategy Decision**: Choosing between cloud providers when primary provider experiences regional outages
4. **Resource Scaling Strategy**: Determining optimal resource allocation when auto-scaling metrics are inconclusive
5. **Disaster Recovery Prioritization**: Selecting critical systems for DR configuration under budget constraints
6. **Compliance Framework Mapping**: Aligning infrastructure controls with industry-specific compliance requirements
7. **Legacy System Integration**: Architecting connectivity patterns for hybrid cloud/on-premises integration

### Escalation Response Procedures
1. **Immediate Notification**: Slack alert to #infrastructure-critical channel within 2 minutes
2. **Context Package Assembly**: Automated collection of logs, configurations, and error states
3. **Expert Triage**: Senior DevOps/SRE review within 15 minutes during business hours
4. **Decision Timeline**: Resolution path selected within 30 minutes of escalation
5. **Fallback Activation**: Alternative deployment strategy activated if primary resolution exceeds 60 minutes
6. **Post-Incident Learning**: Root cause analysis and protocol refinement within 24 hours

## P-RECOVERY Integration

### Checkpoint Strategy
- **Pre-Provisioning State**: IaC repository state, configuration baselines, resource quotas
- **Component-Level Checkpoints**: After each infrastructure layer deployment (network, compute, data, security)
- **Environment Validation Points**: After health checks, security scans, and connectivity verification
- **Pipeline Configuration State**: CI/CD pipeline settings, deployment configurations, artifact versions

### Rollback Mechanisms
1. **Infrastructure Rollback**: `terraform destroy && terraform apply` with previous state file
2. **Configuration Rollback**: Restore environment variables and secrets from secure backup
3. **Network Rollback**: Revert security group rules and routing table configurations
4. **Database Rollback**: Restore from automated snapshot created pre-deployment
5. **Pipeline Rollback**: Restore previous CI/CD configuration from version control
6. **Monitoring Rollback**: Restore previous alerting rules and dashboard configurations

### Recovery Validation
- Verify all environment health endpoints return HTTP 200 status
- Confirm network connectivity between all service tiers
- Validate security baseline compliance with automated scan
- Test CI/CD pipeline with sample deployment
- Verify monitoring and alerting functionality

## Test Scenarios

### Infrastructure Resilience Testing
1. **Multi-AZ Failure Simulation**
   - **Scenario**: Simulate availability zone failure during staging deployment
   - **Expected**: Infrastructure fails over to secondary AZ within 5 minutes
   - **Validation**: All services remain accessible, data integrity maintained

2. **Resource Exhaustion Testing**
   - **Scenario**: Deliberately exceed CPU/memory limits during load testing
   - **Expected**: Auto-scaling triggers within 3 minutes, alerts generated
   - **Validation**: System maintains performance SLOs during scaling events

3. **Network Segmentation Validation**
   - **Scenario**: Test security group rules and network ACL effectiveness
   - **Expected**: Unauthorized traffic blocked, authorized traffic flows normally
   - **Validation**: Security scan confirms no unintended network exposure

### Security and Compliance Testing
4. **SSL/TLS Certificate Rotation**
   - **Scenario**: Simulate certificate expiration and automatic renewal
   - **Expected**: New certificates deployed without service interruption
   - **Validation**: All HTTPS endpoints maintain valid certificates

5. **Backup and Recovery Validation**
   - **Scenario**: Test database backup restoration in staging environment
   - **Expected**: Complete data restoration within RTO/RPO requirements
   - **Validation**: Data integrity verification and application functionality

### CI/CD Pipeline Integration Testing
6. **Multi-Environment Deployment Flow**
   - **Scenario**: Deploy sample application through dev → staging → production
   - **Expected**: Automated promotion with proper approvals and rollback capability
   - **Validation**: Each environment matches deployment specifications

7. **Pipeline Failure Recovery**
   - **Scenario**: Simulate build agent failure during deployment
   - **Expected**: Pipeline retries on alternate agent within 5 minutes
   - **Validation**: Deployment completes successfully with proper logging

### Monitoring and Observability Testing
8. **Alert Escalation Validation**
   - **Scenario**: Trigger critical infrastructure alerts and verify notification paths
   - **Expected**: Alerts reach appropriate teams within defined SLA
   - **Validation**: All notification channels functional, escalation paths tested

9. **Performance Baseline Establishment**
   - **Scenario**: Load test infrastructure to establish performance baseline
   - **Expected**: System maintains <2s response time under normal load
   - **Validation**: Performance metrics collected and baseline documented

### Disaster Recovery Testing
10. **Infrastructure Recreation**
    - **Scenario**: Complete infrastructure destruction and recreation from IaC
    - **Expected**: Full environment restored within 45 minutes (dev) / 60 minutes (staging)
    - **Validation**: All services operational, data restored, monitoring active

11. **Cross-Region Failover**
    - **Scenario**: Simulate primary region outage requiring failover
    - **Expected**: Services migrate to secondary region within 15 minutes
    - **Validation**: Application functionality maintained with minimal data loss

12. **Security Incident Response**
    - **Scenario**: Simulate security breach requiring infrastructure isolation
    - **Expected**: Compromised resources isolated within 10 minutes
    - **Validation**: Security containment effective, forensic data preserved

## Related Protocols
- **QG-PHASE3**: Infrastructure Setup Validation Quality Gate (validates this protocol's outputs)
- **P-SECURITY**: Security Hardening Protocol (applied during Step 6)
- **P-MONITORING**: Observability Setup Protocol (detailed monitoring configuration)
- **P-CICD**: CI/CD Pipeline Configuration Protocol (detailed pipeline setup)
- **P-RECOVERY**: Failure Recovery Protocol (rollback mechanism)
- **GH-3**: Infrastructure Issue Triage

## Validation Criteria
- All environments (dev, staging) return HTTP 200 on health endpoints
- CI/CD pipeline successfully deploys test application to dev
- Network connectivity verified (all services reachable)
- Security baseline scan passes (zero critical vulnerabilities)
- Monitoring dashboard shows green status for all components
- IaC code passes linting and validation (`terraform validate`, `cfn-lint`)
- QG-PHASE3 quality gate passes
- Orchestrator approves transition to Phase 4 (Backend Development)

## Performance SLOs
- Environment provisioning time: <45 minutes for dev, <60 minutes for staging (95th percentile)
- CI/CD pipeline deployment time: <10 minutes for test application
- Infrastructure drift detection: Daily automated checks
