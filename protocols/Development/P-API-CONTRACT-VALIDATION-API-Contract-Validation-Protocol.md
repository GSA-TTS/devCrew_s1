# P-API-CONTRACT-VALIDATION: API Contract Validation Protocol

## Objective
Define standardized workflow for validating API contracts between backend providers and frontend consumers, ensuring compatibility through consumer-driven contract testing and preventing integration failures.

## Tool Requirements

- **TOOL-DEV-003** (API Testing): API contract testing, validation, and compliance verification
  - Execute: Consumer-driven contract testing, API endpoint validation, schema verification, compatibility testing, contract compliance checking
  - Integration: Contract testing frameworks (Pact, Dredd, Spring Cloud Contract), API testing tools, mock servers, validation engines
  - Usage: Contract validation, API compatibility testing, consumer expectation verification, breaking change detection

- **TOOL-DEV-004** (API Documentation): OpenAPI specification management and contract documentation
  - Execute: OpenAPI/Swagger specification generation, contract documentation, API versioning, specification validation
  - Integration: OpenAPI tools, specification validators, documentation generators, version management systems
  - Usage: Contract specification management, API documentation automation, version control, specification validation

- **TOOL-COLLAB-001** (GitHub Integration): Contract specification management, collaboration, and approval workflows
  - Execute: Contract specification version control, team collaboration, approval workflows, change tracking, specification sharing
  - Integration: CLI commands (gh, git), API calls, repository operations, collaboration workflows, documentation management
  - Usage: Contract specification coordination, team collaboration, approval tracking, change management

- **TOOL-CICD-001** (Pipeline Platform): Contract testing automation and deployment coordination
  - Execute: Automated contract testing, pipeline integration, deployment validation, contract compliance enforcement
  - Integration: CI/CD platforms, automated testing, deployment pipelines, validation frameworks, quality gates
  - Usage: Contract testing automation, deployment validation, quality gate integration, compliance enforcement

- **TOOL-TEST-001** (Load Testing): Integration testing, performance validation, and regression testing
  - Execute: API integration testing, performance testing, regression testing, compatibility validation, load testing
  - Integration: Testing frameworks, integration testing tools, performance testing platforms, regression testing systems
  - Usage: Integration validation, performance impact assessment, regression prevention, compatibility verification

## Agent
Primary: Backend-Engineer (provider), Frontend-Engineer (consumer)
Participants: QA-Tester, Code-Reviewer, System-Architect

## Trigger
- After backend API implementation (before QG-PHASE4)
- After frontend API integration (before QG-PHASE5)
- During P-ARCH-INTEGRATION (Step 2)
- When API contract changes proposed
- Before deployment to prevent breaking changes

## Prerequisites
- OpenAPI/Swagger specification documented via **TOOL-DEV-004**
- Backend API implemented and deployed to test environment using **TOOL-CICD-001**
- Frontend integration code implemented with testing frameworks via **TOOL-TEST-001**
- Contract testing framework configured (Pact, Dredd, Spring Cloud Contract) through **TOOL-DEV-003**
- Contract specification version control and collaboration established via **TOOL-COLLAB-001**
- API testing and validation tools operational through **TOOL-DEV-003**
- Documentation and specification management systems configured using **TOOL-DEV-004**
- Integration testing and validation infrastructure ready via **TOOL-TEST-001**

## Steps

1. **Contract Definition**:
   - Backend-Engineer creates OpenAPI/Swagger specification:
     - API endpoints and HTTP methods (GET, POST, PUT, DELETE, PATCH)
     - Request parameters (path, query, header, body)
     - Request body schemas (JSON, XML, form data)
     - Response schemas (success responses, error responses)
     - Authentication requirements (Bearer token, API key, OAuth)
     - Response status codes (200, 201, 400, 401, 403, 404, 500)
   - Document contract in `api-contract.yaml` or `swagger.json`
   - Version contract (e.g., v1, v2) for breaking changes
   - Store contract in shared repository (accessible to Frontend-Engineer)

2. **Consumer Contract Creation** (Frontend-Engineer):
   - Frontend-Engineer defines consumer expectations using Pact:
     - Expected request format (endpoint, method, headers, body)
     - Expected response format (status code, headers, body)
     - Edge cases and error scenarios
   - Create Pact contract files (JSON format)
   - Example Pact contract:
     ```json
     {
       "consumer": {"name": "FrontendApp"},
       "provider": {"name": "BackendAPI"},
       "interactions": [
         {
           "description": "Get user by ID",
           "request": {
             "method": "GET",
             "path": "/api/v1/users/123"
           },
           "response": {
             "status": 200,
             "body": {
               "id": 123,
               "name": "John Doe",
               "email": "john@example.com"
             }
           }
         }
       ]
     }
     ```
   - Store Pact contracts in contract repository

3. **Provider Contract Testing** (Backend-Engineer):
   - Backend runs provider verification tests:
     - Load Pact contracts from repository
     - Replay consumer requests against backend API
     - Verify backend responses match consumer expectations
   - Run Pact verification:
     ```bash
     pact-provider-verifier --provider-base-url http://localhost:8080 \
       --pact-urls ./pacts/frontend-backend.json
     ```
   - If verification fails:
     - Identify mismatches (missing fields, incorrect types, wrong status codes)
     - Fix backend implementation to match contract
     - Rerun verification until passing
   - Publish verification results to Pact Broker

4. **Consumer Contract Testing** (Frontend-Engineer):
   - Frontend runs consumer tests:
     - Mock backend using Pact mock server
     - Execute frontend API calls
     - Verify frontend handles responses correctly
   - Run consumer tests:
     ```bash
     jest --testPathPattern=pact
     ```
   - If tests fail:
     - Fix frontend API integration code
     - Update Pact contract if consumer expectations changed
     - Rerun tests until passing
   - Publish Pact contract to Pact Broker

5. **Contract Compatibility Validation**:
   - Use Pact Broker to validate compatibility:
     - Can-i-deploy check: `pact-broker can-i-deploy --pacticipant FrontendApp --version 1.2.3`
     - Verifies provider verified all consumer contracts
   - Check for breaking changes:
     - Compare new contract version with previous version
     - Identify removed endpoints or fields
     - Identify changed response schemas
   - If breaking changes detected:
     - Communicate with Frontend-Engineer
     - Plan coordinated deployment (backend first, then frontend)
     - Or maintain backward compatibility (versioned APIs)

6. **Schema Validation Testing**:
   - Validate request/response schemas using JSON Schema:
     - Extract schemas from OpenAPI spec
     - Validate actual API responses against schemas
   - Use tools like Dredd for schema validation:
     ```bash
     dredd api-contract.yaml http://localhost:8080
     ```
   - Check for:
     - Required fields present
     - Data types correct (string, integer, boolean, array, object)
     - Enum values valid
     - Nested object structures match
     - Array item schemas correct
   - If schema violations found:
     - Fix backend implementation
     - Or update OpenAPI spec if spec was incorrect
     - Rerun validation

7. **Error Contract Validation**:
   - Validate error response contracts:
     - 400 Bad Request (validation errors)
     - 401 Unauthorized (missing/invalid authentication)
     - 403 Forbidden (insufficient permissions)
     - 404 Not Found (resource doesn't exist)
     - 500 Internal Server Error (server failures)
   - Test error scenarios:
     - Send invalid requests (missing required fields, invalid types)
     - Send unauthorized requests (no auth token)
     - Send forbidden requests (valid auth, insufficient permissions)
     - Send requests for non-existent resources
   - Verify error responses include:
     - Appropriate status code
     - Error message (user-friendly, not exposing internals)
     - Error code (for frontend error handling)
     - Validation details (which fields failed validation)

8. **Versioning and Deprecation Validation**:
   - If API versioning used (e.g., `/api/v1/`, `/api/v2/`):
     - Test all supported versions still work
     - Verify deprecated endpoints return deprecation headers:
       ```
       Deprecation: true
       Sunset: Wed, 11 Nov 2025 11:11:11 GMT
       Link: <https://api.example.com/v2/users>; rel="successor-version"
       ```
   - Test sunset timeline (deprecated endpoints still functional until sunset date)
   - Validate migration path (v1 → v2) documented

9. **Contract Test Automation**:
   - Integrate contract tests into CI/CD pipeline:
     - Run provider tests on backend PRs
     - Run consumer tests on frontend PRs
     - Run compatibility checks before deployment
   - Configure Pact Broker webhooks:
     - Trigger provider verification when consumer publishes new contract
     - Notify team when contract verification fails
   - Fail builds if contract tests fail:
     - Prevent breaking changes from merging
     - Enforce contract-first development

10. **Contract Validation Report**:
    - Generate contract validation report:
      - Contract version
      - Provider verification status (PASSED/FAILED)
      - Consumer test status (PASSED/FAILED)
      - Schema validation results
      - Error contract validation results
      - Breaking changes detected
      - Compatibility status (can-i-deploy result)
    - Share report with System-Architect and QA-Tester
    - Include in QG-PHASE4 (Backend) and QG-PHASE5 (Frontend) submissions

## Expected Outputs
- OpenAPI/Swagger specification (api-contract.yaml)
- Pact consumer contracts (JSON files)
- Provider verification results (Pact Broker)
- Consumer test results (Jest/Mocha output)
- Schema validation results (Dredd report)
- Error contract validation results
- Versioning and deprecation validation results
- Contract validation report (comprehensive summary)
- Can-i-deploy compatibility check results

## Failure Handling
- **Provider Verification Failure**: Backend-Engineer fixes implementation to match consumer contracts. Reruns verification until passing.
- **Consumer Test Failure**: Frontend-Engineer fixes integration code or updates consumer contract. Reruns tests until passing.
- **Schema Violations**: Backend-Engineer fixes response schemas to match OpenAPI spec. Or updates spec if spec incorrect. Reruns validation.
- **Breaking Changes Detected**: Coordinate with Frontend-Engineer for deployment plan. Maintain backward compatibility or version API.
- **Error Contract Missing**: Backend-Engineer implements proper error responses. Frontend-Engineer updates error handling code.
- **Can-i-Deploy Failure**: Do not deploy. Fix contract incompatibilities first. Rerun can-i-deploy check.

## Related Protocols
- **QG-PHASE4**: Backend Development Review (includes contract validation)
- **QG-PHASE5**: Frontend Development Review (includes contract validation)
- **P-ARCH-INTEGRATION**: Architecture Integration (Step 2 runs this protocol)
- **P-FRONTEND-DEV**: Frontend Development Workflow (Step 2 uses contracts)
- **P-HANDOFF**: Agent Handoff (coordinates Backend-Engineer ↔ Frontend-Engineer)

## Validation Criteria
- OpenAPI/Swagger specification complete and versioned
- Pact consumer contracts published to Pact Broker
- Provider verification tests pass (100%)
- Consumer tests pass (100%)
- Schema validation passes (zero violations)
- Error contracts validated (4xx, 5xx responses tested)
- Versioning and deprecation validated (if applicable)
- Can-i-deploy check passes
- Contract validation report generated

## Performance SLOs
- Contract creation time: <2 hours (backend creates OpenAPI spec)
- Consumer contract creation time: <4 hours (frontend defines Pact contracts)
- Provider verification time: <10 minutes (run Pact verification tests)
- Consumer test time: <5 minutes (run Pact consumer tests)
- Schema validation time: <5 minutes (run Dredd validation)
- Total contract validation time: <1 day (creation to report, 95th percentile)
