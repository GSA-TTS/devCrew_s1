# P-ENV-SETUP: Environment Setup Configuration Protocol

## Objective
Define standardized workflow for configuring application environments (development, staging, production) ensuring consistency, security, and proper isolation across deployment targets.

## Tool Requirements

- **TOOL-INFRA-001** (Infrastructure): Environment provisioning, configuration management, and infrastructure orchestration
  - Execute: Environment provisioning, infrastructure configuration, resource management, deployment orchestration, environment isolation
  - Integration: Infrastructure platforms, configuration management tools, deployment systems, resource orchestration, environment management
  - Usage: Environment setup, infrastructure configuration, deployment coordination, resource management, environment orchestration

- **TOOL-SEC-010** (Secrets Management): Secret provisioning, credential management, and security configuration
  - Execute: Secret provisioning, credential management, security configuration, access control, sensitive data protection
  - Integration: Secrets management platforms, credential systems, security tools, access control systems, encryption services
  - Usage: Secret management, credential provisioning, security configuration, access control, sensitive data handling

- **TOOL-CICD-001** (Pipeline Platform): Environment deployment, configuration validation, and deployment automation
  - Execute: Environment deployment, configuration validation, deployment automation, pipeline management, release coordination
  - Integration: CI/CD platforms, deployment tools, automation systems, pipeline management, release orchestration
  - Usage: Environment deployment, configuration automation, deployment validation, pipeline coordination, release management

- **TOOL-COLLAB-001** (GitHub Integration): Configuration documentation, environment tracking, and team coordination
  - Execute: Configuration documentation, environment tracking, team coordination, version control, configuration management
  - Integration: CLI commands (gh, git), API calls, repository operations, documentation systems, configuration tracking
  - Usage: Environment documentation, configuration tracking, team coordination, version control, configuration management

## Agent
Primary: DevOps-Engineer
Participants: Backend-Engineer, Frontend-Engineer, Database-Administrator, SRE

## Trigger
- After infrastructure provisioned (P-INFRASTRUCTURE-SETUP complete)
- When new environment required (new region, disaster recovery)
- During environment updates or configuration changes
- Before application deployment

## Prerequisites
- Infrastructure provisioned via **TOOL-INFRA-001** (servers, databases, networking)
- Application code ready for deployment
- Environment-specific requirements documented
- Secrets management system available via **TOOL-SEC-010** (Vault, AWS Secrets Manager)

## Steps

1. **Environment Configuration Planning**:
   - Define environment-specific parameters:
     - **Development**: Lower resources, verbose logging, hot-reload enabled
     - **Staging**: Production-equivalent, representative data, full monitoring
     - **Production**: Optimized resources, minimal logging, high availability
   - Document configuration differences (config-matrix.md)
   - Identify secrets and sensitive data (API keys, database passwords, tokens)

2. **Environment Variables Configuration**:
   - Create environment-specific `.env` files (never commit to git):
     - `.env.development`
     - `.env.staging`
     - `.env.production`
   - Define required environment variables:
     - `NODE_ENV` / `RAILS_ENV` / `FLASK_ENV` (development/staging/production)
     - `DATABASE_URL` (connection string)
     - `API_BASE_URL` (backend endpoint)
     - `LOG_LEVEL` (debug/info/warn/error)
     - `FEATURE_FLAGS` (enable/disable features per environment)
   - Use .env.example template for documentation (safe to commit)

3. **Secrets Management**:
   - Store secrets in secrets management system:
     - **AWS**: AWS Secrets Manager, Parameter Store
     - **Azure**: Azure Key Vault
     - **GCP**: Secret Manager
     - **Self-hosted**: HashiCorp Vault
   - Never hardcode secrets in code or config files
   - Rotate secrets periodically (90-day rotation policy)
   - Use secret rotation automation where available
   - Grant least-privilege access (only services needing secret can access)

4. **Database Configuration**:
   - Configure database connection pooling:
     - Min connections: 5 (dev), 10 (staging), 20 (production)
     - Max connections: 10 (dev), 50 (staging), 100 (production)
     - Connection timeout: 30 seconds
     - Idle timeout: 10 minutes
   - Set up database migrations:
     - Development: Auto-run migrations on startup
     - Staging: Manual migration approval
     - Production: Gated migration with rollback plan
   - Configure read replicas (staging, production only):
     - Write traffic → primary database
     - Read traffic → read replicas (load balanced)

5. **Logging Configuration**:
   - Configure log levels per environment:
     - Development: DEBUG (verbose, includes query logs)
     - Staging: INFO (detailed, excludes debug)
     - Production: WARN (errors and warnings only)
   - Set up centralized logging:
     - Development: Local file or console
     - Staging/Production: CloudWatch, ELK, Datadog
   - Configure log retention:
     - Development: 7 days
     - Staging: 30 days
     - Production: 90 days (compliance requirement)
   - Implement structured logging (JSON format for parsing)

6. **Caching Configuration**:
   - Configure caching layers:
     - Application cache: Redis, Memcached
     - CDN cache: CloudFront, Cloudflare (production only)
     - Browser cache: Cache-Control headers
   - Set cache TTL (time-to-live):
     - Static assets: 1 year (with cache busting)
     - API responses: 5 minutes (frequently changing data)
     - Database queries: 1 hour (rarely changing data)
   - Configure cache invalidation strategies

7. **Feature Flags Configuration**:
   - Use feature flag service (LaunchDarkly, Unleash, custom):
     - Development: All features enabled for testing
     - Staging: Production-equivalent flags for validation
     - Production: Gradual rollouts, A/B testing
   - Document feature flag usage (feature-flags.md)
   - Implement flag cleanup (remove obsolete flags quarterly)

8. **CORS and Security Headers Configuration**:
   - Configure CORS (Cross-Origin Resource Sharing):
     - Development: Permissive (allow localhost origins)
     - Staging: Restrictive (allow staging frontend domain)
     - Production: Strict (allow production frontend domain only)
   - Set security headers:
     - `Content-Security-Policy` (CSP)
     - `X-Frame-Options: DENY`
     - `X-Content-Type-Options: nosniff`
     - `Strict-Transport-Security` (HSTS, production only)
   - Configure rate limiting (per environment):
     - Development: No limits
     - Staging: 100 requests/minute per IP
     - Production: 60 requests/minute per IP

9. **Monitoring and Alerts Configuration**:
   - Configure environment-specific monitoring:
     - Development: Basic health checks only
     - Staging: Full monitoring, test alert channels
     - Production: Full monitoring, critical alerts to PagerDuty
   - Set alert thresholds per environment:
     - CPU usage: >80% (staging/production)
     - Memory usage: >85% (staging/production)
     - Error rate: >1% (staging/production)
     - Response time: >2s p95 (staging/production)
   - Configure alert notification channels

10. **Environment Validation**:
    - Run environment validation tests:
      - Health check endpoints return 200
      - Database connectivity verified
      - Secrets accessible from application
      - Logging flowing to centralized system
      - Caching operational
      - Feature flags service reachable
      - Monitoring dashboards show data
    - Document validation results (env-validation-report.md)
    - Obtain sign-off from Backend-Engineer, Frontend-Engineer, SRE

## Expected Outputs
- Environment configuration files (.env templates, config files)
- Secrets stored in secrets management system
- Database connection pooling configured
- Logging and monitoring configured
- Caching layers operational
- Feature flags configured
- CORS and security headers set
- Environment validation report (all checks passed)
- Configuration documentation (config-matrix.md)

## Failure Handling
- **Missing Environment Variables**: Document required vars in .env.example. Provide clear error messages if missing at runtime.
- **Secrets Not Found**: Verify secrets exist in secrets manager. Check IAM permissions. Re-create secrets if needed.
- **Database Connection Failure**: Verify connection string. Check network access. Validate credentials. Test connection pooling.
- **Logging Not Working**: Check centralized logging credentials. Verify network access to logging service. Test log ingestion.
- **Cache Unreachable**: Verify Redis/Memcached running. Check connection string. Validate network access.
- **Feature Flags Unavailable**: Gracefully degrade (use default values). Log warning. Alert DevOps-Engineer.
- **Monitoring Gaps**: Identify missing metrics. Configure additional collectors. Verify data flowing to dashboards.

## Related Protocols
- **P-INFRASTRUCTURE-SETUP**: Environment Provisioning (provides infrastructure, this protocol configures it)
- **QG-PHASE3**: Infrastructure Setup Validation (validates this protocol's outputs)
- **P-DEPLOYMENT**: Deployment Protocol (uses configurations from this protocol)
- **P-SECURITY**: Security Hardening (security headers, secrets management)

## Validation Criteria
- All required environment variables documented and configured
- Secrets stored securely (zero hardcoded secrets)
- Database connections tested (pooling operational)
- Logging configured and centralized (logs flowing)
- Caching layers operational (Redis/CDN reachable)
- Feature flags configured (service accessible)
- CORS and security headers set correctly
- Monitoring and alerts operational (dashboards show data)
- Environment validation tests pass (100% health checks)
- Configuration documentation complete

## Performance SLOs
- Environment configuration time: <4 hours per environment (dev/staging/production)
- Secrets rotation time: <30 minutes (automated rotation)
- Configuration update deployment time: <15 minutes (apply new configs)
- Environment validation time: <30 minutes (run all checks)
