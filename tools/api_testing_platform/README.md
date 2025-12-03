# API Testing & Contract Validation Platform

![Python](https://img.shields.io/badge/python-3.10+-blue.svg)
![OpenAPI](https://img.shields.io/badge/OpenAPI-3.0%2F3.1-green.svg)
![Status](https://img.shields.io/badge/status-production-brightgreen.svg)

## Overview

The API Testing & Contract Validation Platform is a comprehensive automated testing solution that validates API contracts, performs schema validation, executes automated API tests, and ensures API consistency across microservices through consumer-driven contract testing. This platform integrates seamlessly with OpenAPI/Swagger specifications to auto-generate tests, validate request/response schemas, and detect breaking changes before they reach production.

The platform implements property-based testing using Schemathesis to generate test cases automatically from OpenAPI specifications, testing edge cases and boundary conditions that manual testing often misses. It supports consumer-driven contract testing with the Pact framework, enabling independent service development while maintaining API compatibility. The platform provides comprehensive reporting with detailed failure analysis, performance metrics, and contract violation detection.

Built as part of the devCrew_s1 initiative, this tool provides critical capabilities for modern microservices architectures and API-driven development workflows, supporting both internal development teams and external API consumers.

### Key Capabilities

- **OpenAPI 3.0/3.1 Validation & Linting** - Validate and lint API specifications with customizable rules and backward compatibility checking
- **Automatic Test Generation** - Generate comprehensive pytest test cases from OpenAPI specs with property-based testing strategies
- **Consumer-Driven Contract Testing** - Implement Pact-based contract testing for independent microservices development
- **API Regression Testing** - Detect breaking changes by comparing current responses against historical baselines
- **Schema Validation** - Validate request/response schemas with detailed error reporting and custom format validators
- **Multiple Authentication Methods** - Support Bearer tokens, OAuth2, API keys, Basic Auth, and mTLS
- **Performance Testing** - Measure API latency, throughput, and detect performance regressions
- **CI/CD Integration** - Seamless integration with GitHub Actions, GitLab CI, Jenkins, and other CI/CD platforms

### Protocol Support

**P-API-CONTRACT-VALIDATION (API Contract Testing)**
- Consumer-driven contract testing for microservices independence
- Automated provider verification on deployment
- Contract versioning and compatibility management
- Can-I-Deploy safety checks before production releases
- Cross-team collaboration through shared contract specifications

**P-FRONTEND-DEV (Frontend API Integration)**
- Mock API generation for frontend development without backends
- Type-safe API client generation for TypeScript/JavaScript
- Early API integration testing in frontend pipelines
- Contract validation for frontend API consumers
- Realistic test data generation from schemas

## Features

### OpenAPI 3.0/3.1 Validation and Linting

- Full support for OpenAPI 3.0 and 3.1 specifications
- Syntax and semantic validation with detailed error reporting
- Custom linting rules for organizational standards
- Backward compatibility checking for API versioning
- Multi-file specification resolution with `$ref` dereferencing
- Spectral-based linting for security and naming conventions

### Auto-Test Generation from Specs

- Generate pytest test cases automatically from OpenAPI definitions
- Property-based testing with Hypothesis strategies for edge cases
- Boundary value analysis (min/max values, empty strings, null values)
- Negative test case generation (invalid inputs, authentication failures)
- Parametrized tests for multiple input combinations
- Customizable test templates for organization-specific patterns

### Consumer-Driven Contract Testing (Pact)

- Create and manage Pact contracts between consumers and providers
- Pact broker integration (PactFlow, local broker)
- Automated provider verification workflow
- Contract versioning and tagging
- Can-I-Deploy checks for safe deployments
- Webhook configuration for continuous verification

### API Regression Testing

- Baseline response capture and storage
- Automatic response diff detection (structure and data changes)
- Performance regression detection with latency thresholds
- Breaking change identification and alerting
- Historical trend analysis and reporting
- Automated baseline updates with approval workflow

### Schema Validation

- Request schema validation against OpenAPI definitions
- Response schema validation with detailed error messages
- JSON Schema Draft 7/2019-09/2020-12 support
- Custom format validators (email, UUID, date-time, custom patterns)
- Strict vs. lenient validation modes
- Schema evolution compatibility checking

### Multiple Authentication Methods

- Bearer token authentication
- OAuth2 flows (authorization code, client credentials)
- API key authentication (header and query parameter)
- Basic authentication
- Mutual TLS (mTLS) support
- Session management with connection pooling
- Automatic token refresh and retry logic

### CI/CD Integration

- Exit codes for pipeline integration
- JUnit XML output for test reporting
- GitHub Actions annotations
- Parallel test execution with pytest-xdist
- HTML and Allure test reports
- Integration with test management systems (TestRail, Zephyr)

## Prerequisites

### Required

- **Python**: 3.10 or higher
- **pip**: Latest version (23.0+)

### Core Dependencies

The platform requires the following Python packages (automatically installed):

- **pytest**: 7.4+ - Test framework with fixture support
- **requests**: 2.31+ - HTTP client library
- **schemathesis**: 3.19+ - Property-based API testing from OpenAPI specs
- **pact-python**: 2.1+ - Consumer-driven contract testing
- **openapi-spec-validator**: 0.7+ - OpenAPI 3.0/3.1 validation
- **jsonschema**: 4.20+ - JSON Schema validation
- **hypothesis**: 6.92+ - Property-based testing strategies
- **pyyaml**: 6.0+ - YAML parsing for configurations
- **click**: 8.1+ - CLI framework
- **rich**: 13.7+ - Terminal formatting and output

### Optional Tools

- **Pact Broker**: For centralized contract management (can be run via Docker)
- **Git**: 2.40+ for version control of test suites
- **Docker**: For running Pact broker locally

## Installation

### Install from Source

```bash
# Navigate to the platform directory
cd /Users/tamnguyen/Documents/GitHub/devCrew_s1/tools/api_testing_platform

# Install dependencies (will be available in requirements.txt)
pip install -r requirements.txt

# Verify installation
python -c "from tools.api_testing_platform import ContractValidator; print('Installation successful!')"
```

### Install as Package

```bash
# Install from devCrew_s1 repository root
cd /Users/tamnguyen/Documents/GitHub/devCrew_s1
pip install -e .
```

### Optional: Set up Pact Broker (Docker)

```bash
# Run local Pact broker for contract testing
docker-compose up -d pact-broker

# Verify broker is running
curl http://localhost:9292
```

## Quick Start

### Validate OpenAPI Spec

```bash
# Validate an OpenAPI specification file
python -m tools.api_testing_platform.contract_validator --spec openapi.yaml

# Validate with linting rules
python -m tools.api_testing_platform.contract_validator --spec openapi.yaml --lint
```

### Generate Tests

```bash
# Generate pytest tests from OpenAPI spec
python -m tools.api_testing_platform.test_generator --spec openapi.yaml --output tests/generated/

# Generate with authentication templates
python -m tools.api_testing_platform.test_generator --spec openapi.yaml --output tests/ --auth bearer
```

### Run API Tests

```bash
# Execute API tests against a live environment
pytest tests/generated/ --base-url https://api.example.com

# Run with authentication
export API_TOKEN="your-bearer-token"
pytest tests/generated/ --base-url https://api.example.com --auth-token $API_TOKEN
```

### Quick Python API Example

```python
from tools.api_testing_platform import ContractValidator, APIClient

# Validate OpenAPI specification
validator = ContractValidator()
result = validator.validate_spec("openapi.yaml")

if not result.is_valid:
    for error in result.errors:
        print(f"Error: {error.message} at {error.path}")
else:
    print("OpenAPI spec is valid!")

# Test API endpoint
client = APIClient(base_url="https://api.example.com")
response = client.get("/api/v1/users/123")
assert response.status_code == 200
```

## Usage

### Validate OpenAPI Specs

#### Basic Validation

```python
from tools.api_testing_platform import ContractValidator

# Initialize validator
validator = ContractValidator()

# Validate a specification file
result = validator.validate_spec("openapi.yaml")

if result.is_valid:
    print("✓ OpenAPI specification is valid")
    print(f"  Endpoints: {result.endpoint_count}")
    print(f"  Version: {result.openapi_version}")
else:
    print("✗ Validation failed:")
    for error in result.errors:
        print(f"  - {error.message} at {error.path}")
```

#### Validation with Linting

```python
from tools.api_testing_platform import ContractValidator

validator = ContractValidator()

# Validate with linting rules
result = validator.validate_spec(
    spec_file="openapi.yaml",
    lint=True,
    lint_rules={
        "operation-operationId": "error",
        "operation-description": "warn",
        "operation-tags": "error"
    }
)

# Display linting warnings
for warning in result.warnings:
    print(f"Warning: {warning.message} at {warning.path}")
```

#### Backward Compatibility Check

```python
from tools.api_testing_platform import ContractValidator

validator = ContractValidator()

# Check backward compatibility between versions
compatibility = validator.check_compatibility(
    old_spec="openapi-v1.yaml",
    new_spec="openapi-v2.yaml"
)

if compatibility.is_compatible:
    print("✓ New version is backward compatible")
else:
    print("✗ Breaking changes detected:")
    for change in compatibility.breaking_changes:
        print(f"  - {change.description} in {change.endpoint}")
```

#### Multi-File Spec Validation

```python
from tools.api_testing_platform import ContractValidator

validator = ContractValidator()

# Validate spec with $ref references
result = validator.validate_spec(
    spec_file="openapi.yaml",
    resolve_refs=True,
    base_path="/path/to/specs"
)

print(f"Resolved {result.ref_count} references")
```

### Generate Tests

#### Generate Pytest Tests

```python
from tools.api_testing_platform import TestGenerator

# Initialize test generator
generator = TestGenerator()

# Generate test cases from OpenAPI spec
tests = generator.generate_from_spec(
    spec_file="openapi.yaml",
    output_dir="tests/generated/",
    template="pytest"
)

print(f"Generated {len(tests)} test files")
for test in tests:
    print(f"  - {test.file_path} ({test.test_count} tests)")
```

#### Generate with Property-Based Testing

```python
from tools.api_testing_platform import TestGenerator

generator = TestGenerator()

# Generate tests with property-based strategies
tests = generator.generate_from_spec(
    spec_file="openapi.yaml",
    output_dir="tests/property_based/",
    template="pytest",
    property_based=True,
    hypothesis_strategies={
        "string": "text",
        "integer": "integers",
        "array": "lists"
    }
)
```

#### Generate Negative Tests

```python
from tools.api_testing_platform import TestGenerator

generator = TestGenerator()

# Generate negative test cases
tests = generator.generate_from_spec(
    spec_file="openapi.yaml",
    output_dir="tests/negative/",
    template="pytest",
    include_negative_tests=True,
    negative_scenarios=[
        "invalid_input",
        "missing_required_fields",
        "auth_failures",
        "rate_limiting"
    ]
)
```

#### Custom Test Templates

```python
from tools.api_testing_platform import TestGenerator

generator = TestGenerator()

# Use custom Jinja2 template
tests = generator.generate_from_spec(
    spec_file="openapi.yaml",
    output_dir="tests/custom/",
    template_file="custom_test_template.j2",
    template_vars={
        "base_url": "https://api.example.com",
        "auth_header": "X-API-Key"
    }
)
```

### Run API Tests

#### Basic API Testing

```python
from tools.api_testing_platform import APIClient

# Initialize API client
client = APIClient(base_url="https://api.example.com")

# Test GET endpoint
response = client.get("/api/v1/users/123")
assert response.status_code == 200
assert response.json()["id"] == 123

# Test POST endpoint
user_data = {"name": "John Doe", "email": "john@example.com"}
response = client.post("/api/v1/users", json=user_data)
assert response.status_code == 201
assert "id" in response.json()
```

#### Authentication Examples

##### Bearer Token Authentication

```python
from tools.api_testing_platform import APIClient

# Initialize with bearer token
client = APIClient(base_url="https://api.example.com")
client.set_bearer_token("your-api-token-here")

# Make authenticated request
response = client.get("/api/v1/protected/resource")
assert response.status_code == 200
```

##### API Key Authentication (Header)

```python
from tools.api_testing_platform import APIClient

client = APIClient(base_url="https://api.example.com")
client.set_api_key("your-api-key", location="header", name="X-API-Key")

response = client.get("/api/v1/data")
assert response.status_code == 200
```

##### API Key Authentication (Query Parameter)

```python
from tools.api_testing_platform import APIClient

client = APIClient(base_url="https://api.example.com")
client.set_api_key("your-api-key", location="query", name="api_key")

response = client.get("/api/v1/data")
assert response.status_code == 200
```

##### Basic Authentication

```python
from tools.api_testing_platform import APIClient

client = APIClient(base_url="https://api.example.com")
client.set_basic_auth(username="user", password="password")

response = client.get("/api/v1/secure/data")
assert response.status_code == 200
```

##### OAuth2 Authentication

```python
from tools.api_testing_platform import APIClient

client = APIClient(base_url="https://api.example.com")

# OAuth2 client credentials flow
client.set_oauth2(
    token_url="https://auth.example.com/oauth/token",
    client_id="your-client-id",
    client_secret="your-client-secret",
    scope="read write"
)

response = client.get("/api/v1/protected/resource")
assert response.status_code == 200
```

#### Filtering and Test Selection

```python
from tools.api_testing_platform import APIClient

# Test specific endpoints only
client = APIClient(base_url="https://api.example.com")

# Test only GET methods
endpoints = client.discover_endpoints("openapi.yaml", methods=["GET"])
for endpoint in endpoints:
    response = client.get(endpoint.path)
    print(f"{endpoint.path}: {response.status_code}")

# Test endpoints matching pattern
endpoints = client.discover_endpoints("openapi.yaml", path_pattern="/api/v1/users/*")
for endpoint in endpoints:
    response = client.request(endpoint.method, endpoint.path)
    print(f"{endpoint.method} {endpoint.path}: {response.status_code}")
```

#### Schema Validation

```python
from tools.api_testing_platform import APIClient, SchemaValidator

client = APIClient(base_url="https://api.example.com")
validator = SchemaValidator()

# Load OpenAPI spec
validator.load_spec("openapi.yaml")

# Make request and validate response
response = client.get("/api/v1/users/123")
assert response.status_code == 200

# Validate response against schema
validation_result = validator.validate_response(
    response=response,
    endpoint="/api/v1/users/{id}",
    method="GET",
    status_code=200
)

if not validation_result.is_valid:
    for error in validation_result.errors:
        print(f"Schema error: {error.message} at {error.path}")
```

### Pact Contract Testing

#### Consumer Side - Create Contract

```python
from tools.api_testing_platform import PactManager
import requests

# Initialize Pact for consumer
pact = PactManager(
    consumer="frontend-app",
    provider="user-service",
    pact_dir="pacts/"
)

# Define expected interaction
pact.given("User exists with ID 123") \
    .upon_receiving("A request for user details") \
    .with_request(method="GET", path="/api/v1/users/123") \
    .will_respond_with(
        status=200,
        headers={"Content-Type": "application/json"},
        body={"id": 123, "name": "John Doe", "email": "john@example.com"}
    )

# Execute consumer test
with pact:
    response = requests.get(f"{pact.uri}/api/v1/users/123")
    assert response.status_code == 200
    user = response.json()
    assert user["id"] == 123
    assert user["name"] == "John Doe"

    print("✓ Consumer test passed - Pact contract created")

# Pact file is automatically saved to pacts/frontend-app-user-service.json
```

#### Publish Contract to Broker

```python
from tools.api_testing_platform import PactManager

pact = PactManager(
    consumer="frontend-app",
    provider="user-service"
)

# Publish pact to broker
result = pact.publish_to_broker(
    pact_file="pacts/frontend-app-user-service.json",
    broker_url="https://pact-broker.example.com",
    version="1.2.3",
    tags=["main", "production"],
    broker_username="user",
    broker_password="password"
)

if result.success:
    print(f"✓ Contract published: {result.pact_url}")
else:
    print(f"✗ Publish failed: {result.error}")
```

#### Provider Side - Verify Contract

```python
from tools.api_testing_platform import PactManager

# Initialize provider verifier
pact = PactManager(
    consumer="frontend-app",
    provider="user-service"
)

# Define state handlers
def setup_user_exists():
    # Set up test database with user ID 123
    create_test_user(id=123, name="John Doe", email="john@example.com")

state_handlers = {
    "User exists with ID 123": setup_user_exists
}

# Verify provider against contracts
verification = pact.verify_provider(
    provider_base_url="https://api.example.com",
    broker_url="https://pact-broker.example.com",
    broker_username="user",
    broker_password="password",
    provider_version="2.1.0",
    publish_verification=True,
    state_handlers=state_handlers
)

if verification.success:
    print("✓ All contracts verified successfully")
else:
    print("✗ Contract verification failed:")
    for failure in verification.failures:
        print(f"  - {failure.interaction}: {failure.error}")
```

#### Can-I-Deploy Check

```python
from tools.api_testing_platform import PactManager

pact = PactManager()

# Check if version can be deployed to production
can_deploy = pact.can_i_deploy(
    participant="frontend-app",
    version="1.2.3",
    to_environment="production",
    broker_url="https://pact-broker.example.com",
    broker_username="user",
    broker_password="password"
)

if can_deploy.deployable:
    print(f"✓ Safe to deploy frontend-app@1.2.3 to production")
    print(f"  Reason: {can_deploy.reason}")
else:
    print(f"✗ Cannot deploy frontend-app@1.2.3 to production")
    print(f"  Reason: {can_deploy.reason}")
    print(f"  Missing verifications:")
    for missing in can_deploy.missing_verifications:
        print(f"    - {missing.provider}@{missing.version}")
    exit(1)
```

#### Complete Pact Workflow Example

```python
from tools.api_testing_platform import PactManager
import requests

# --- CONSUMER SIDE ---
print("Step 1: Creating consumer contract...")
consumer_pact = PactManager(
    consumer="mobile-app",
    provider="payment-service",
    pact_dir="pacts/"
)

# Define payment processing interaction
consumer_pact.given("User has valid payment method") \
    .upon_receiving("Process payment request") \
    .with_request(
        method="POST",
        path="/api/v1/payments",
        body={"amount": 100.00, "currency": "USD", "user_id": 123}
    ) \
    .will_respond_with(
        status=201,
        body={"transaction_id": "txn_123", "status": "completed"}
    )

# Run consumer test
with consumer_pact:
    response = requests.post(
        f"{consumer_pact.uri}/api/v1/payments",
        json={"amount": 100.00, "currency": "USD", "user_id": 123}
    )
    assert response.status_code == 201
    assert response.json()["status"] == "completed"

print("✓ Consumer test passed")

# Publish to broker
print("\nStep 2: Publishing contract to broker...")
consumer_pact.publish_to_broker(
    pact_file="pacts/mobile-app-payment-service.json",
    broker_url="https://pact-broker.example.com",
    version="3.2.1",
    tags=["main", "feat-payments"],
    broker_username="user",
    broker_password="password"
)
print("✓ Contract published")

# --- PROVIDER SIDE ---
print("\nStep 3: Verifying provider against contract...")
provider_pact = PactManager(
    consumer="mobile-app",
    provider="payment-service"
)

# Verify provider
verification = provider_pact.verify_provider(
    provider_base_url="https://payment-api.example.com",
    broker_url="https://pact-broker.example.com",
    broker_username="user",
    broker_password="password",
    provider_version="1.5.0",
    publish_verification=True,
    state_handlers={
        "User has valid payment method": lambda: setup_test_payment_method()
    }
)

if verification.success:
    print("✓ Provider verified successfully")
else:
    print("✗ Provider verification failed")
    exit(1)

# --- DEPLOYMENT CHECK ---
print("\nStep 4: Checking if deployment is safe...")
can_deploy = provider_pact.can_i_deploy(
    participant="mobile-app",
    version="3.2.1",
    to_environment="production",
    broker_url="https://pact-broker.example.com",
    broker_username="user",
    broker_password="password"
)

if can_deploy.deployable:
    print("✓ Safe to deploy to production!")
else:
    print(f"✗ Cannot deploy: {can_deploy.reason}")
    exit(1)
```

### Regression Testing

#### Create Baseline

```python
from tools.api_testing_platform import RegressionEngine, APIClient

# Initialize regression engine
regression = RegressionEngine(baseline_dir="baselines/")

# Create API client
client = APIClient(base_url="https://api.example.com")

# Capture baseline responses
print("Capturing baseline responses...")
endpoints = [
    {"method": "GET", "path": "/api/v1/users"},
    {"method": "GET", "path": "/api/v1/users/123"},
    {"method": "GET", "path": "/api/v1/products"}
]

for endpoint in endpoints:
    response = client.request(endpoint["method"], endpoint["path"])
    regression.save_baseline(
        endpoint=endpoint["path"],
        method=endpoint["method"],
        response=response,
        version="v1.0.0"
    )

print(f"✓ Saved {len(endpoints)} baseline responses")
```

#### Run Regression Tests

```python
from tools.api_testing_platform import RegressionEngine, APIClient

regression = RegressionEngine(baseline_dir="baselines/")
client = APIClient(base_url="https://api.example.com")

# Run regression tests
print("Running regression tests...")
results = regression.run_regression_tests(
    client=client,
    baseline_version="v1.0.0",
    current_version="v1.1.0"
)

print(f"\nRegression Test Results:")
print(f"  Total: {results.total_tests}")
print(f"  Passed: {results.passed}")
print(f"  Failed: {results.failed}")

if results.failed > 0:
    print("\nFailures detected:")
    for failure in results.failures:
        print(f"  {failure.method} {failure.endpoint}")
        print(f"    Type: {failure.failure_type}")
        print(f"    Details: {failure.details}")
```

#### Detect Breaking Changes

```python
from tools.api_testing_platform import RegressionEngine

regression = RegressionEngine(baseline_dir="baselines/")

# Compare response structures
comparison = regression.compare_responses(
    baseline_response=baseline_data,
    current_response=current_data,
    strict_mode=True
)

if comparison.has_breaking_changes:
    print("✗ Breaking changes detected:")
    for change in comparison.breaking_changes:
        print(f"  - {change.type}: {change.description}")
        print(f"    Path: {change.json_path}")
        print(f"    Expected: {change.expected}")
        print(f"    Actual: {change.actual}")
else:
    print("✓ No breaking changes detected")
```

#### Update Baseline with Approval

```python
from tools.api_testing_platform import RegressionEngine

regression = RegressionEngine(baseline_dir="baselines/")

# Get pending baseline updates
pending = regression.get_pending_updates()

print(f"Found {len(pending)} pending baseline updates:")
for update in pending:
    print(f"\n{update.method} {update.endpoint}")
    print(f"  Changes: {len(update.changes)}")

    # Display changes
    for change in update.changes:
        print(f"    - {change.description}")

    # Approve or reject
    approve = input("Approve this update? (y/n): ")
    if approve.lower() == 'y':
        regression.approve_baseline_update(
            endpoint=update.endpoint,
            method=update.method,
            version="v1.1.0"
        )
        print("  ✓ Baseline updated")
    else:
        print("  ✗ Update rejected")
```

### Performance Testing

#### Basic Performance Test

```python
from tools.api_testing_platform import APIClient, RegressionEngine
import time

client = APIClient(base_url="https://api.example.com")
regression = RegressionEngine()

# Performance test configuration
endpoint = "/api/v1/users"
num_requests = 100

# Execute performance test
print(f"Running performance test: {num_requests} requests to {endpoint}")
start_time = time.time()
latencies = []

for i in range(num_requests):
    request_start = time.time()
    response = client.get(endpoint)
    request_end = time.time()

    latency_ms = (request_end - request_start) * 1000
    latencies.append(latency_ms)

    if response.status_code != 200:
        print(f"Request {i+1} failed: {response.status_code}")

total_time = time.time() - start_time

# Calculate metrics
import statistics
metrics = {
    "total_requests": num_requests,
    "total_time_sec": total_time,
    "throughput_rps": num_requests / total_time,
    "avg_latency_ms": statistics.mean(latencies),
    "median_latency_ms": statistics.median(latencies),
    "p95_latency_ms": statistics.quantiles(latencies, n=20)[18],
    "p99_latency_ms": statistics.quantiles(latencies, n=100)[98],
    "max_latency_ms": max(latencies),
    "min_latency_ms": min(latencies)
}

print("\nPerformance Metrics:")
print(f"  Throughput: {metrics['throughput_rps']:.2f} req/sec")
print(f"  Avg Latency: {metrics['avg_latency_ms']:.2f} ms")
print(f"  Median Latency: {metrics['median_latency_ms']:.2f} ms")
print(f"  P95 Latency: {metrics['p95_latency_ms']:.2f} ms")
print(f"  P99 Latency: {metrics['p99_latency_ms']:.2f} ms")
print(f"  Max Latency: {metrics['max_latency_ms']:.2f} ms")

# Check performance regression
threshold_p95 = 100  # ms
if metrics['p95_latency_ms'] > threshold_p95:
    print(f"\n✗ Performance regression detected!")
    print(f"  P95 latency {metrics['p95_latency_ms']:.2f}ms exceeds threshold {threshold_p95}ms")
else:
    print(f"\n✓ Performance within acceptable range")
```

#### Load Testing with Concurrency

```python
from tools.api_testing_platform import APIClient
import concurrent.futures
import time

def execute_request(client, endpoint):
    """Execute single API request and return latency."""
    start = time.time()
    try:
        response = client.get(endpoint)
        latency = (time.time() - start) * 1000
        return {
            "success": response.status_code == 200,
            "status": response.status_code,
            "latency_ms": latency
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "latency_ms": (time.time() - start) * 1000
        }

# Load test configuration
client = APIClient(base_url="https://api.example.com")
endpoint = "/api/v1/users"
concurrent_users = 10
requests_per_user = 100

print(f"Load Test: {concurrent_users} concurrent users, {requests_per_user} requests each")

# Execute concurrent requests
start_time = time.time()
results = []

with concurrent.futures.ThreadPoolExecutor(max_workers=concurrent_users) as executor:
    futures = []
    for user in range(concurrent_users):
        for req in range(requests_per_user):
            future = executor.submit(execute_request, client, endpoint)
            futures.append(future)

    for future in concurrent.futures.as_completed(futures):
        results.append(future.result())

total_time = time.time() - start_time

# Analyze results
successful = [r for r in results if r["success"]]
failed = [r for r in results if not r["success"]]
latencies = [r["latency_ms"] for r in successful]

print(f"\nLoad Test Results:")
print(f"  Total Requests: {len(results)}")
print(f"  Successful: {len(successful)} ({len(successful)/len(results)*100:.1f}%)")
print(f"  Failed: {len(failed)} ({len(failed)/len(results)*100:.1f}%)")
print(f"  Total Time: {total_time:.2f} sec")
print(f"  Throughput: {len(results)/total_time:.2f} req/sec")

if latencies:
    import statistics
    print(f"\nLatency Metrics:")
    print(f"  Avg: {statistics.mean(latencies):.2f} ms")
    print(f"  Median: {statistics.median(latencies):.2f} ms")
    print(f"  P95: {statistics.quantiles(latencies, n=20)[18]:.2f} ms")
    print(f"  Max: {max(latencies):.2f} ms")
```

## Configuration

### api-test-config.yaml

Complete configuration file with all available options:

```yaml
# Base API configuration
base_url: https://api.example.com
api_version: v1
timeout: 30  # Request timeout in seconds
verify_ssl: true

# Retry configuration
retry:
  max_attempts: 3
  backoff_factor: 2  # Exponential backoff multiplier
  retry_on_status: [500, 502, 503, 504]  # HTTP status codes to retry

# Authentication configuration
auth:
  type: bearer  # Options: bearer, api_key, basic, oauth2, none

  # Bearer token (when type: bearer)
  bearer:
    token_env: API_TOKEN  # Environment variable name
    # OR
    token_file: /path/to/token.txt  # File containing token

  # API Key (when type: api_key)
  api_key:
    key_env: API_KEY
    location: header  # Options: header, query
    name: X-API-Key  # Header name or query parameter name

  # Basic Auth (when type: basic)
  basic:
    username_env: API_USERNAME
    password_env: API_PASSWORD

  # OAuth2 (when type: oauth2)
  oauth2:
    token_url: https://auth.example.com/oauth/token
    client_id_env: OAUTH_CLIENT_ID
    client_secret_env: OAUTH_CLIENT_SECRET
    scope: read write
    grant_type: client_credentials

# Test execution configuration
test_execution:
  parallel: true
  workers: 8  # Number of parallel workers
  fail_fast: false  # Stop on first failure
  verbose: true

  # Test filtering
  filters:
    endpoints:
      include: ["/api/v1/*"]  # Include patterns
      exclude: ["/api/v1/internal/*"]  # Exclude patterns
    methods: [GET, POST, PUT, DELETE]  # HTTP methods to test
    tags: [smoke, regression]  # OpenAPI tags to test

# Schema validation configuration
schema_validation:
  strict_mode: true  # Fail on unexpected fields
  validate_formats: true  # Validate string formats (email, uuid, etc.)
  custom_formats:
    - name: phone
      pattern: '^\+?[1-9]\d{1,14}$'
    - name: ssn
      pattern: '^\d{3}-\d{2}-\d{4}$'

# Regression testing configuration
regression:
  baseline_dir: baselines/
  auto_update: false  # Automatically update baselines on changes
  ignore_fields:  # Fields to ignore in comparisons
    - timestamp
    - _metadata.generated_at
    - request_id
  performance_thresholds:
    p95_latency_ms: 100
    p99_latency_ms: 200
    error_rate_percent: 1.0

# Performance testing configuration
performance:
  enabled: true
  concurrent_users: 10
  requests_per_user: 100
  ramp_up_time: 5  # Seconds to ramp up to full load
  thresholds:
    avg_latency_ms: 50
    p95_latency_ms: 100
    throughput_rps: 100
    error_rate_percent: 0.5

# Reporting configuration
reporting:
  formats: [json, html, junit]  # Output formats
  output_dir: reports/
  include_request_details: true
  include_response_bodies: false  # Don't include large response bodies
  screenshot_on_failure: false

# Logging configuration
logging:
  level: INFO  # DEBUG, INFO, WARNING, ERROR
  log_file: api_tests.log
  log_requests: true
  log_responses: true
  mask_sensitive_data: true
  sensitive_headers:
    - Authorization
    - X-API-Key
    - Cookie

# Environment-specific overrides
environments:
  staging:
    base_url: https://staging.api.example.com
    timeout: 60
    auth:
      type: bearer
      bearer:
        token_env: STAGING_API_TOKEN

  production:
    base_url: https://api.example.com
    timeout: 30
    verify_ssl: true
    auth:
      type: bearer
      bearer:
        token_env: PROD_API_TOKEN
```

### contract-config.yaml

Pact broker configuration:

```yaml
# Pact Broker configuration
pact_broker:
  url: https://pact-broker.example.com

  # Authentication
  auth:
    username_env: PACT_BROKER_USERNAME
    password_env: PACT_BROKER_PASSWORD
    # OR use bearer token
    # token_env: PACT_BROKER_TOKEN

  # SSL verification
  verify_ssl: true

# Consumer configuration
consumer:
  name: frontend-app
  version_env: APP_VERSION  # Environment variable with version
  # OR
  # version_file: VERSION.txt  # File containing version
  tags:
    - main
    - production

  # Consumer test configuration
  pact_dir: pacts/  # Directory to save pact files
  log_level: INFO

# Provider configuration
provider:
  name: user-service
  base_url_env: PROVIDER_BASE_URL  # Provider API base URL
  version_env: SERVICE_VERSION

  # State handlers
  state_handlers_module: tests.pact_states  # Python module with state handlers

  # Verification configuration
  publish_verification: true
  provider_version_tags:
    - main
    - staging

# Can-I-Deploy configuration
deployment:
  to_environment: production  # Target environment
  retry_while_unknown: 5  # Retry count if verification status unknown
  retry_interval: 10  # Seconds between retries

# Webhook configuration (optional)
webhooks:
  enabled: true
  provider_verification_url: https://ci.example.com/verify-pact
  events:
    - contract_content_changed
    - provider_verification_published

# Tagging strategy
tagging:
  auto_tag_branch: true  # Automatically tag with git branch name
  auto_tag_commit: false  # Tag with git commit SHA
  custom_tags:
    - ci-build
    - automated-test
```

## Authentication

### Bearer Token Authentication

```python
from tools.api_testing_platform import APIClient
import os

# From environment variable
client = APIClient(base_url="https://api.example.com")
client.set_bearer_token(os.getenv("API_TOKEN"))

# From file
with open("token.txt") as f:
    token = f.read().strip()
client.set_bearer_token(token)

# Direct token
client.set_bearer_token("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...")

# Make authenticated request
response = client.get("/api/v1/protected/resource")
```

### API Key (Header)

```python
from tools.api_testing_platform import APIClient

client = APIClient(base_url="https://api.example.com")

# API key in header
client.set_api_key(
    api_key="your-api-key-here",
    location="header",
    name="X-API-Key"
)

response = client.get("/api/v1/data")
print(f"Status: {response.status_code}")
```

### API Key (Query Parameter)

```python
from tools.api_testing_platform import APIClient

client = APIClient(base_url="https://api.example.com")

# API key as query parameter
client.set_api_key(
    api_key="your-api-key-here",
    location="query",
    name="api_key"
)

# Request URL will be: https://api.example.com/api/v1/data?api_key=your-api-key-here
response = client.get("/api/v1/data")
```

### Basic Authentication

```python
from tools.api_testing_platform import APIClient

client = APIClient(base_url="https://api.example.com")

# Basic auth
client.set_basic_auth(
    username="admin",
    password="secure-password"
)

response = client.get("/api/v1/admin/users")
```

### OAuth2 Client Credentials

```python
from tools.api_testing_platform import APIClient

client = APIClient(base_url="https://api.example.com")

# OAuth2 client credentials flow
client.set_oauth2(
    token_url="https://auth.example.com/oauth/token",
    client_id="your-client-id",
    client_secret="your-client-secret",
    scope="read write"
)

# Token is automatically fetched and refreshed
response = client.get("/api/v1/protected/resource")
```

### OAuth2 Authorization Code Flow

```python
from tools.api_testing_platform import APIClient

client = APIClient(base_url="https://api.example.com")

# OAuth2 authorization code flow (with manual authorization)
client.set_oauth2(
    token_url="https://auth.example.com/oauth/token",
    authorization_url="https://auth.example.com/oauth/authorize",
    client_id="your-client-id",
    client_secret="your-client-secret",
    redirect_uri="http://localhost:8080/callback",
    scope="read write"
)

# This will open browser for authorization
# After authorization, token is stored and automatically refreshed
response = client.get("/api/v1/user/profile")
```

## Output Formats

### Test Results (JSON)

```json
{
  "test_run_id": "run-2025-12-03-abc123",
  "timestamp": "2025-12-03T10:30:00Z",
  "spec_file": "openapi.yaml",
  "environment": "staging",
  "summary": {
    "total": 156,
    "passed": 148,
    "failed": 6,
    "skipped": 2,
    "duration_seconds": 45.3,
    "success_rate": 94.9
  },
  "failures": [
    {
      "test_id": "test_create_user_invalid_email",
      "endpoint": "/api/v1/users",
      "method": "POST",
      "expected_status": 400,
      "actual_status": 200,
      "error_type": "schema_validation_failed",
      "error_message": "Schema validation failed: email format not validated",
      "details": {
        "request": {
          "headers": {"Content-Type": "application/json"},
          "body": {"name": "Test User", "email": "invalid-email"}
        },
        "response": {
          "headers": {"Content-Type": "application/json"},
          "status": 200,
          "body": {"id": 123, "email": "invalid-email"}
        },
        "schema_errors": [
          {
            "path": "$.email",
            "message": "Invalid email format",
            "expected": "email",
            "actual": "invalid-email"
          }
        ]
      },
      "timestamp": "2025-12-03T10:30:15Z"
    }
  ],
  "performance": {
    "avg_latency_ms": 45.2,
    "p95_latency_ms": 92.4,
    "p99_latency_ms": 156.8,
    "max_latency_ms": 324.1,
    "min_latency_ms": 12.3
  },
  "coverage": {
    "endpoints_tested": 45,
    "endpoints_total": 52,
    "coverage_percent": 86.5
  }
}
```

### Contract Validation Report (Pact)

```json
{
  "pact_version": "3.0.0",
  "consumer": "frontend-app",
  "provider": "user-service",
  "verification_timestamp": "2025-12-03T10:30:00Z",
  "provider_version": "2.1.0",
  "verification_status": "passed",
  "interactions": [
    {
      "description": "Get user by ID",
      "provider_state": "user exists with ID 123",
      "status": "passed",
      "request": {
        "method": "GET",
        "path": "/api/v1/users/123",
        "headers": {
          "Authorization": "Bearer ***"
        }
      },
      "response": {
        "status": 200,
        "headers": {
          "Content-Type": "application/json"
        },
        "body": {
          "id": 123,
          "name": "John Doe",
          "email": "john@example.com"
        }
      },
      "duration_ms": 45
    },
    {
      "description": "Create new user",
      "provider_state": "no users exist",
      "status": "passed",
      "request": {
        "method": "POST",
        "path": "/api/v1/users",
        "body": {
          "name": "Jane Smith",
          "email": "jane@example.com"
        }
      },
      "response": {
        "status": 201,
        "body": {
          "id": 124,
          "name": "Jane Smith",
          "email": "jane@example.com"
        }
      },
      "duration_ms": 67
    }
  ],
  "summary": {
    "total_interactions": 2,
    "passed": 2,
    "failed": 0,
    "pending": 0
  }
}
```

### Schema Validation Report

```json
{
  "spec_file": "openapi.yaml",
  "validation_timestamp": "2025-12-03T10:30:00Z",
  "spec_valid": true,
  "openapi_version": "3.1.0",
  "endpoints_tested": 45,
  "schema_violations": [
    {
      "endpoint": "/api/v1/users",
      "method": "POST",
      "status_code": 201,
      "violation_type": "response_schema_mismatch",
      "severity": "error",
      "expected_schema": {
        "type": "object",
        "required": ["id", "name", "email", "created_at"],
        "properties": {
          "id": {"type": "integer"},
          "name": {"type": "string"},
          "email": {"type": "string", "format": "email"},
          "created_at": {"type": "string", "format": "date-time"}
        }
      },
      "actual_response": {
        "id": 123,
        "name": "John Doe",
        "email": "john@example.com"
      },
      "missing_fields": ["created_at"],
      "error_path": "$.created_at",
      "error_message": "Required field 'created_at' is missing",
      "timestamp": "2025-12-03T10:30:15Z"
    },
    {
      "endpoint": "/api/v1/products/search",
      "method": "GET",
      "status_code": 200,
      "violation_type": "unexpected_field",
      "severity": "warning",
      "unexpected_fields": ["_debug_info"],
      "error_path": "$._debug_info",
      "error_message": "Response contains unexpected field '_debug_info' not defined in schema",
      "timestamp": "2025-12-03T10:30:22Z"
    }
  ],
  "summary": {
    "total_violations": 2,
    "errors": 1,
    "warnings": 1,
    "info": 0
  }
}
```

## CI/CD Integration

### GitHub Actions

Complete workflow for API testing in CI/CD:

```yaml
name: API Contract Testing

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  validate-spec:
    name: Validate OpenAPI Spec
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'

      - name: Install dependencies
        run: |
          cd tools/api_testing_platform
          pip install -r requirements.txt

      - name: Validate OpenAPI specification
        run: |
          python -m tools.api_testing_platform.contract_validator \
            --spec openapi.yaml \
            --lint \
            --output validation-report.json

      - name: Upload validation report
        uses: actions/upload-artifact@v3
        if: always()
        with:
          name: validation-report
          path: validation-report.json

  generate-tests:
    name: Generate API Tests
    needs: validate-spec
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'

      - name: Install dependencies
        run: |
          cd tools/api_testing_platform
          pip install -r requirements.txt

      - name: Generate tests from OpenAPI spec
        run: |
          python -m tools.api_testing_platform.test_generator \
            --spec openapi.yaml \
            --output tests/generated/ \
            --auth bearer

      - name: Upload generated tests
        uses: actions/upload-artifact@v3
        with:
          name: generated-tests
          path: tests/generated/

  api-tests:
    name: Run API Tests
    needs: generate-tests
    runs-on: ubuntu-latest
    strategy:
      matrix:
        environment: [staging, production]
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'

      - name: Install dependencies
        run: |
          cd tools/api_testing_platform
          pip install -r requirements.txt
          pip install pytest pytest-xdist pytest-html

      - name: Download generated tests
        uses: actions/download-artifact@v3
        with:
          name: generated-tests
          path: tests/generated/

      - name: Run API tests
        env:
          API_TOKEN: ${{ secrets[format('{0}_API_TOKEN', matrix.environment)] }}
          BASE_URL: ${{ secrets[format('{0}_BASE_URL', matrix.environment)] }}
        run: |
          pytest tests/generated/ \
            --base-url=$BASE_URL \
            --auth-token=$API_TOKEN \
            -n 8 \
            --html=report.html \
            --junit-xml=junit.xml

      - name: Upload test results
        uses: actions/upload-artifact@v3
        if: always()
        with:
          name: test-results-${{ matrix.environment }}
          path: |
            report.html
            junit.xml

      - name: Publish test results
        uses: EnricoMi/publish-unit-test-result-action@v2
        if: always()
        with:
          files: junit.xml

  pact-consumer:
    name: Pact Consumer Tests
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'

      - name: Install dependencies
        run: |
          cd tools/api_testing_platform
          pip install -r requirements.txt

      - name: Run consumer tests
        run: |
          pytest tests/pact/consumer/ -v

      - name: Publish pacts to broker
        env:
          PACT_BROKER_URL: ${{ secrets.PACT_BROKER_URL }}
          PACT_BROKER_TOKEN: ${{ secrets.PACT_BROKER_TOKEN }}
        run: |
          python -m tools.api_testing_platform.pact_manager publish \
            --pact-dir pacts/ \
            --broker-url $PACT_BROKER_URL \
            --broker-token $PACT_BROKER_TOKEN \
            --version ${{ github.sha }} \
            --tag ${{ github.ref_name }}

  pact-provider:
    name: Pact Provider Verification
    needs: pact-consumer
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'

      - name: Install dependencies
        run: |
          cd tools/api_testing_platform
          pip install -r requirements.txt

      - name: Start provider service
        run: |
          # Start your API service here
          docker-compose up -d api-service
          sleep 10

      - name: Verify provider contracts
        env:
          PACT_BROKER_URL: ${{ secrets.PACT_BROKER_URL }}
          PACT_BROKER_TOKEN: ${{ secrets.PACT_BROKER_TOKEN }}
        run: |
          python -m tools.api_testing_platform.pact_manager verify \
            --provider user-service \
            --provider-base-url http://localhost:8080 \
            --broker-url $PACT_BROKER_URL \
            --broker-token $PACT_BROKER_TOKEN \
            --publish-verification \
            --provider-version ${{ github.sha }}

  can-i-deploy:
    name: Can I Deploy Check
    needs: [api-tests, pact-provider]
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'

      - name: Install dependencies
        run: |
          cd tools/api_testing_platform
          pip install -r requirements.txt

      - name: Check deployment readiness
        env:
          PACT_BROKER_URL: ${{ secrets.PACT_BROKER_URL }}
          PACT_BROKER_TOKEN: ${{ secrets.PACT_BROKER_TOKEN }}
        run: |
          python -m tools.api_testing_platform.pact_manager can-i-deploy \
            --participant frontend-app \
            --version ${{ github.sha }} \
            --to-environment production \
            --broker-url $PACT_BROKER_URL \
            --broker-token $PACT_BROKER_TOKEN
```

### GitLab CI

```yaml
stages:
  - validate
  - test
  - verify
  - deploy-check

variables:
  PYTHON_VERSION: "3.10"
  PIP_CACHE_DIR: "$CI_PROJECT_DIR/.cache/pip"

cache:
  paths:
    - .cache/pip

validate_spec:
  stage: validate
  image: python:$PYTHON_VERSION
  script:
    - cd tools/api_testing_platform
    - pip install -r requirements.txt
    - python -m tools.api_testing_platform.contract_validator
        --spec openapi.yaml
        --lint
        --output validation-report.json
  artifacts:
    reports:
      junit: validation-report.json
    paths:
      - validation-report.json
    expire_in: 1 week

api_tests:
  stage: test
  image: python:$PYTHON_VERSION
  parallel:
    matrix:
      - ENVIRONMENT: [staging, production]
  script:
    - cd tools/api_testing_platform
    - pip install -r requirements.txt pytest pytest-xdist
    - pytest tests/generated/
        --base-url=$BASE_URL
        --auth-token=$API_TOKEN
        -n 8
        --junit-xml=junit.xml
  artifacts:
    reports:
      junit: junit.xml
    paths:
      - junit.xml
    expire_in: 1 week

pact_consumer:
  stage: test
  image: python:$PYTHON_VERSION
  script:
    - cd tools/api_testing_platform
    - pip install -r requirements.txt
    - pytest tests/pact/consumer/ -v
    - python -m tools.api_testing_platform.pact_manager publish
        --pact-dir pacts/
        --broker-url $PACT_BROKER_URL
        --broker-token $PACT_BROKER_TOKEN
        --version $CI_COMMIT_SHA
        --tag $CI_COMMIT_REF_NAME
  artifacts:
    paths:
      - pacts/
    expire_in: 1 week

pact_provider:
  stage: verify
  image: python:$PYTHON_VERSION
  services:
    - name: api-service:latest
      alias: api
  script:
    - cd tools/api_testing_platform
    - pip install -r requirements.txt
    - python -m tools.api_testing_platform.pact_manager verify
        --provider user-service
        --provider-base-url http://api:8080
        --broker-url $PACT_BROKER_URL
        --broker-token $PACT_BROKER_TOKEN
        --publish-verification
        --provider-version $CI_COMMIT_SHA
  dependencies:
    - pact_consumer

can_i_deploy:
  stage: deploy-check
  image: python:$PYTHON_VERSION
  script:
    - cd tools/api_testing_platform
    - pip install -r requirements.txt
    - python -m tools.api_testing_platform.pact_manager can-i-deploy
        --participant frontend-app
        --version $CI_COMMIT_SHA
        --to-environment production
        --broker-url $PACT_BROKER_URL
        --broker-token $PACT_BROKER_TOKEN
  only:
    - main
  dependencies:
    - pact_provider
```

### Jenkins

```groovy
pipeline {
    agent any

    environment {
        PYTHON_VERSION = '3.10'
        PACT_BROKER_URL = credentials('pact-broker-url')
        PACT_BROKER_TOKEN = credentials('pact-broker-token')
    }

    stages {
        stage('Setup') {
            steps {
                sh '''
                    python${PYTHON_VERSION} -m venv venv
                    . venv/bin/activate
                    cd tools/api_testing_platform
                    pip install -r requirements.txt
                '''
            }
        }

        stage('Validate OpenAPI Spec') {
            steps {
                sh '''
                    . venv/bin/activate
                    python -m tools.api_testing_platform.contract_validator \
                        --spec openapi.yaml \
                        --lint \
                        --output validation-report.json
                '''
            }
            post {
                always {
                    archiveArtifacts artifacts: 'validation-report.json'
                }
            }
        }

        stage('Generate Tests') {
            steps {
                sh '''
                    . venv/bin/activate
                    python -m tools.api_testing_platform.test_generator \
                        --spec openapi.yaml \
                        --output tests/generated/ \
                        --auth bearer
                '''
            }
        }

        stage('Run API Tests') {
            parallel {
                stage('Staging') {
                    environment {
                        BASE_URL = credentials('staging-api-url')
                        API_TOKEN = credentials('staging-api-token')
                    }
                    steps {
                        sh '''
                            . venv/bin/activate
                            pytest tests/generated/ \
                                --base-url=$BASE_URL \
                                --auth-token=$API_TOKEN \
                                -n 8 \
                                --junit-xml=junit-staging.xml
                        '''
                    }
                    post {
                        always {
                            junit 'junit-staging.xml'
                        }
                    }
                }
                stage('Production') {
                    environment {
                        BASE_URL = credentials('prod-api-url')
                        API_TOKEN = credentials('prod-api-token')
                    }
                    steps {
                        sh '''
                            . venv/bin/activate
                            pytest tests/generated/ \
                                --base-url=$BASE_URL \
                                --auth-token=$API_TOKEN \
                                -n 8 \
                                --junit-xml=junit-prod.xml
                        '''
                    }
                    post {
                        always {
                            junit 'junit-prod.xml'
                        }
                    }
                }
            }
        }

        stage('Pact Consumer Tests') {
            steps {
                sh '''
                    . venv/bin/activate
                    pytest tests/pact/consumer/ -v
                    python -m tools.api_testing_platform.pact_manager publish \
                        --pact-dir pacts/ \
                        --broker-url $PACT_BROKER_URL \
                        --broker-token $PACT_BROKER_TOKEN \
                        --version $GIT_COMMIT \
                        --tag $GIT_BRANCH
                '''
            }
        }

        stage('Pact Provider Verification') {
            steps {
                sh '''
                    . venv/bin/activate
                    docker-compose up -d api-service
                    sleep 10
                    python -m tools.api_testing_platform.pact_manager verify \
                        --provider user-service \
                        --provider-base-url http://localhost:8080 \
                        --broker-url $PACT_BROKER_URL \
                        --broker-token $PACT_BROKER_TOKEN \
                        --publish-verification \
                        --provider-version $GIT_COMMIT
                '''
            }
            post {
                always {
                    sh 'docker-compose down'
                }
            }
        }

        stage('Can I Deploy') {
            when {
                branch 'main'
            }
            steps {
                sh '''
                    . venv/bin/activate
                    python -m tools.api_testing_platform.pact_manager can-i-deploy \
                        --participant frontend-app \
                        --version $GIT_COMMIT \
                        --to-environment production \
                        --broker-url $PACT_BROKER_URL \
                        --broker-token $PACT_BROKER_TOKEN
                '''
            }
        }
    }

    post {
        always {
            cleanWs()
        }
        failure {
            mail to: 'team@example.com',
                 subject: "Failed Pipeline: ${currentBuild.fullDisplayName}",
                 body: "Pipeline failed. Check ${env.BUILD_URL}"
        }
    }
}
```

## Python API

### Complete Usage Example

```python
"""
Complete example demonstrating all features of the API Testing Platform.
"""
import os
from tools.api_testing_platform import (
    ContractValidator,
    TestGenerator,
    APIClient,
    PactManager,
    SchemaValidator,
    RegressionEngine
)

def main():
    # 1. Validate OpenAPI Specification
    print("Step 1: Validating OpenAPI specification...")
    validator = ContractValidator()
    result = validator.validate_spec("openapi.yaml", lint=True)

    if not result.is_valid:
        print("✗ OpenAPI validation failed:")
        for error in result.errors:
            print(f"  - {error.message}")
        return

    print(f"✓ OpenAPI spec is valid ({result.endpoint_count} endpoints)")

    # 2. Generate Test Cases
    print("\nStep 2: Generating test cases...")
    generator = TestGenerator()
    tests = generator.generate_from_spec(
        spec_file="openapi.yaml",
        output_dir="tests/generated/",
        template="pytest",
        include_negative_tests=True
    )
    print(f"✓ Generated {len(tests)} test files")

    # 3. Initialize API Client
    print("\nStep 3: Setting up API client...")
    client = APIClient(base_url="https://api.example.com")
    client.set_bearer_token(os.getenv("API_TOKEN"))
    print("✓ API client configured")

    # 4. Run API Tests with Schema Validation
    print("\nStep 4: Running API tests...")
    schema_validator = SchemaValidator()
    schema_validator.load_spec("openapi.yaml")

    test_endpoints = [
        {"method": "GET", "path": "/api/v1/users"},
        {"method": "GET", "path": "/api/v1/users/123"},
        {"method": "POST", "path": "/api/v1/users"}
    ]

    passed = 0
    failed = 0

    for endpoint in test_endpoints:
        try:
            response = client.request(endpoint["method"], endpoint["path"])

            # Validate response schema
            validation = schema_validator.validate_response(
                response=response,
                endpoint=endpoint["path"],
                method=endpoint["method"],
                status_code=response.status_code
            )

            if validation.is_valid:
                print(f"  ✓ {endpoint['method']} {endpoint['path']}: {response.status_code}")
                passed += 1
            else:
                print(f"  ✗ {endpoint['method']} {endpoint['path']}: Schema validation failed")
                failed += 1
        except Exception as e:
            print(f"  ✗ {endpoint['method']} {endpoint['path']}: {str(e)}")
            failed += 1

    print(f"\nTest Results: {passed} passed, {failed} failed")

    # 5. Create Pact Contract
    print("\nStep 5: Creating Pact contract...")
    pact = PactManager(
        consumer="frontend-app",
        provider="user-service",
        pact_dir="pacts/"
    )

    pact.given("User exists") \
        .upon_receiving("Get user request") \
        .with_request(method="GET", path="/api/v1/users/123") \
        .will_respond_with(status=200, body={"id": 123, "name": "John Doe"})

    print("✓ Pact contract created")

    # 6. Publish to Pact Broker
    print("\nStep 6: Publishing contract to broker...")
    publish_result = pact.publish_to_broker(
        pact_file="pacts/frontend-app-user-service.json",
        broker_url=os.getenv("PACT_BROKER_URL"),
        version="1.0.0",
        tags=["main"]
    )

    if publish_result.success:
        print(f"✓ Contract published: {publish_result.pact_url}")
    else:
        print(f"✗ Publish failed: {publish_result.error}")

    # 7. Run Regression Tests
    print("\nStep 7: Running regression tests...")
    regression = RegressionEngine(baseline_dir="baselines/")

    # Create baseline if it doesn't exist
    if not regression.baseline_exists(endpoint="/api/v1/users", method="GET"):
        response = client.get("/api/v1/users")
        regression.save_baseline(
            endpoint="/api/v1/users",
            method="GET",
            response=response,
            version="v1.0.0"
        )
        print("  ✓ Baseline created")
    else:
        # Run regression test
        regression_result = regression.run_regression_tests(
            client=client,
            baseline_version="v1.0.0",
            current_version="v1.1.0"
        )

        if regression_result.has_regressions:
            print(f"  ✗ {regression_result.regression_count} regressions detected")
        else:
            print("  ✓ No regressions detected")

    print("\n✓ API Testing Platform demo completed successfully!")

if __name__ == "__main__":
    main()
```

### Advanced Example - Custom Workflow

```python
"""
Advanced example with custom validation rules and error handling.
"""
from tools.api_testing_platform import (
    ContractValidator,
    APIClient,
    SchemaValidator
)
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CustomAPITester:
    """Custom API testing workflow with organization-specific rules."""

    def __init__(self, base_url: str, spec_file: str):
        self.client = APIClient(base_url=base_url)
        self.validator = SchemaValidator()
        self.validator.load_spec(spec_file)
        self.spec_file = spec_file

    def setup_auth(self, auth_type: str, **kwargs):
        """Configure authentication based on type."""
        if auth_type == "bearer":
            self.client.set_bearer_token(kwargs.get("token"))
        elif auth_type == "api_key":
            self.client.set_api_key(
                kwargs.get("key"),
                location=kwargs.get("location", "header"),
                name=kwargs.get("name", "X-API-Key")
            )
        elif auth_type == "oauth2":
            self.client.set_oauth2(**kwargs)
        else:
            raise ValueError(f"Unsupported auth type: {auth_type}")

    def test_endpoint(self, method: str, path: str, **kwargs):
        """
        Test single endpoint with comprehensive validation.

        Args:
            method: HTTP method
            path: Endpoint path
            **kwargs: Additional request parameters

        Returns:
            dict: Test result with status and details
        """
        result = {
            "endpoint": f"{method} {path}",
            "success": False,
            "status_code": None,
            "errors": []
        }

        try:
            # Make request
            response = self.client.request(method, path, **kwargs)
            result["status_code"] = response.status_code

            # Validate response schema
            validation = self.validator.validate_response(
                response=response,
                endpoint=path,
                method=method,
                status_code=response.status_code
            )

            if not validation.is_valid:
                result["errors"].extend([
                    f"Schema error: {e.message}" for e in validation.errors
                ])

            # Custom validation rules
            self._apply_custom_rules(response, result)

            # Mark as success if no errors
            result["success"] = len(result["errors"]) == 0

        except Exception as e:
            result["errors"].append(f"Request failed: {str(e)}")
            logger.error(f"Test failed for {method} {path}: {str(e)}")

        return result

    def _apply_custom_rules(self, response, result):
        """Apply organization-specific validation rules."""
        # Rule 1: All responses must have request_id
        if response.status_code < 400:
            data = response.json()
            if "_metadata" not in data or "request_id" not in data["_metadata"]:
                result["errors"].append(
                    "Response missing required _metadata.request_id field"
                )

        # Rule 2: Check response time
        if hasattr(response, "elapsed"):
            latency_ms = response.elapsed.total_seconds() * 1000
            if latency_ms > 1000:
                result["errors"].append(
                    f"Response time {latency_ms:.2f}ms exceeds 1000ms threshold"
                )

        # Rule 3: Validate security headers
        required_headers = ["X-Content-Type-Options", "X-Frame-Options"]
        for header in required_headers:
            if header not in response.headers:
                result["errors"].append(f"Missing security header: {header}")

    def test_crud_workflow(self, resource_path: str, create_data: dict):
        """
        Test complete CRUD workflow for a resource.

        Args:
            resource_path: Base path for resource (e.g., /api/v1/users)
            create_data: Data for creating new resource

        Returns:
            dict: Workflow test results
        """
        results = {}

        # 1. CREATE
        logger.info(f"Testing CREATE: POST {resource_path}")
        create_result = self.test_endpoint("POST", resource_path, json=create_data)
        results["create"] = create_result

        if not create_result["success"]:
            logger.error("CREATE failed, aborting workflow")
            return results

        # Extract created resource ID
        response_data = self.client.last_response.json()
        resource_id = response_data.get("id")

        if not resource_id:
            logger.error("Created resource has no ID")
            return results

        # 2. READ
        logger.info(f"Testing READ: GET {resource_path}/{resource_id}")
        read_result = self.test_endpoint("GET", f"{resource_path}/{resource_id}")
        results["read"] = read_result

        # 3. UPDATE
        logger.info(f"Testing UPDATE: PUT {resource_path}/{resource_id}")
        update_data = create_data.copy()
        update_data["name"] = f"{update_data.get('name', 'Test')} Updated"
        update_result = self.test_endpoint(
            "PUT",
            f"{resource_path}/{resource_id}",
            json=update_data
        )
        results["update"] = update_result

        # 4. DELETE
        logger.info(f"Testing DELETE: DELETE {resource_path}/{resource_id}")
        delete_result = self.test_endpoint("DELETE", f"{resource_path}/{resource_id}")
        results["delete"] = delete_result

        # 5. Verify deletion
        logger.info(f"Testing deletion verification: GET {resource_path}/{resource_id}")
        verify_result = self.test_endpoint("GET", f"{resource_path}/{resource_id}")
        results["verify_delete"] = verify_result

        # Should return 404
        if verify_result["status_code"] != 404:
            verify_result["errors"].append(
                f"Expected 404 after deletion, got {verify_result['status_code']}"
            )
            verify_result["success"] = False

        return results

# Usage
if __name__ == "__main__":
    tester = CustomAPITester(
        base_url="https://api.example.com",
        spec_file="openapi.yaml"
    )

    # Setup authentication
    tester.setup_auth("bearer", token=os.getenv("API_TOKEN"))

    # Test CRUD workflow
    results = tester.test_crud_workflow(
        resource_path="/api/v1/users",
        create_data={"name": "Test User", "email": "test@example.com"}
    )

    # Print results
    for operation, result in results.items():
        status = "✓" if result["success"] else "✗"
        print(f"{status} {operation.upper()}: {result['endpoint']}")
        if result["errors"]:
            for error in result["errors"]:
                print(f"    - {error}")
```

## Protocol Support

### P-API-CONTRACT-VALIDATION

The platform provides comprehensive support for API contract testing through consumer-driven contracts using the Pact framework.

#### Consumer-Driven Contract Testing

Consumer-driven contract testing enables independent service development while maintaining API compatibility. The consumer defines expectations, and the provider verifies against those expectations.

**Benefits:**
- Independent development of consumers and providers
- Early detection of breaking changes
- Confidence in deployments through Can-I-Deploy checks
- Version compatibility across microservices
- Reduced need for end-to-end integration tests

#### Complete Workflow Example

```python
from tools.api_testing_platform import PactManager
import requests

# === CONSUMER SIDE ===
# Define what the consumer expects from the provider
consumer_pact = PactManager(
    consumer="shopping-cart-frontend",
    provider="product-catalog-api",
    pact_dir="pacts/"
)

# Interaction 1: Get product details
consumer_pact.given("Product with ID 456 exists") \
    .upon_receiving("Request for product details") \
    .with_request(
        method="GET",
        path="/api/v1/products/456",
        headers={"Accept": "application/json"}
    ) \
    .will_respond_with(
        status=200,
        headers={"Content-Type": "application/json"},
        body={
            "id": 456,
            "name": "Laptop",
            "price": 999.99,
            "in_stock": True
        }
    )

# Interaction 2: Add product to cart
consumer_pact.given("Cart is empty") \
    .upon_receiving("Request to add product to cart") \
    .with_request(
        method="POST",
        path="/api/v1/cart/items",
        headers={"Content-Type": "application/json"},
        body={"product_id": 456, "quantity": 1}
    ) \
    .will_respond_with(
        status=201,
        body={"cart_id": "cart-123", "item_count": 1}
    )

# Run consumer tests
with consumer_pact:
    # Test interaction 1
    response = requests.get(
        f"{consumer_pact.uri}/api/v1/products/456",
        headers={"Accept": "application/json"}
    )
    assert response.status_code == 200
    product = response.json()
    assert product["id"] == 456
    assert product["name"] == "Laptop"

    # Test interaction 2
    response = requests.post(
        f"{consumer_pact.uri}/api/v1/cart/items",
        json={"product_id": 456, "quantity": 1},
        headers={"Content-Type": "application/json"}
    )
    assert response.status_code == 201
    cart = response.json()
    assert cart["item_count"] == 1

print("✓ Consumer tests passed - Contract created")

# Publish contract to broker
consumer_pact.publish_to_broker(
    pact_file="pacts/shopping-cart-frontend-product-catalog-api.json",
    broker_url="https://pact-broker.example.com",
    version="2.3.0",
    tags=["main", "release"],
    broker_token="pact-broker-token"
)

# === PROVIDER SIDE ===
# Verify provider meets consumer expectations
provider_pact = PactManager(
    consumer="shopping-cart-frontend",
    provider="product-catalog-api"
)

# Define state handlers to set up provider state
def setup_product_exists():
    """Set up test database with product ID 456."""
    from test_helpers import create_test_product
    create_test_product(id=456, name="Laptop", price=999.99, in_stock=True)

def setup_empty_cart():
    """Ensure cart is empty for test."""
    from test_helpers import clear_cart
    clear_cart("cart-123")

state_handlers = {
    "Product with ID 456 exists": setup_product_exists,
    "Cart is empty": setup_empty_cart
}

# Verify provider against all consumer contracts
verification = provider_pact.verify_provider(
    provider_base_url="https://staging-api.example.com",
    broker_url="https://pact-broker.example.com",
    broker_token="pact-broker-token",
    provider_version="1.8.2",
    publish_verification=True,
    state_handlers=state_handlers,
    enable_pending=True  # Don't fail on pending pacts
)

if not verification.success:
    print("✗ Provider verification failed:")
    for failure in verification.failures:
        print(f"  - {failure.interaction}: {failure.error}")
    exit(1)

print("✓ Provider verified successfully")

# === DEPLOYMENT CHECK ===
# Check if consumer can be safely deployed
can_deploy = provider_pact.can_i_deploy(
    participant="shopping-cart-frontend",
    version="2.3.0",
    to_environment="production",
    broker_url="https://pact-broker.example.com",
    broker_token="pact-broker-token"
)

if can_deploy.deployable:
    print(f"✓ Safe to deploy shopping-cart-frontend@2.3.0 to production")
    print(f"  All provider dependencies verified")
else:
    print(f"✗ Cannot deploy to production")
    print(f"  Reason: {can_deploy.reason}")
    for missing in can_deploy.missing_verifications:
        print(f"  - Missing verification from {missing.provider}@{missing.version}")
    exit(1)
```

#### Advanced Pact Features

**Provider States with Parameters:**
```python
# Consumer side - define state with parameters
pact.given("User has balance of $100.00") \
    .upon_receiving("Purchase request") \
    .with_request(method="POST", path="/api/v1/purchase") \
    .will_respond_with(status=200)

# Provider side - handle parameterized state
def setup_user_balance(params):
    balance = params.get("balance", "100.00")
    user_id = params.get("user_id", 123)
    set_user_balance(user_id, float(balance.replace("$", "")))

state_handlers = {
    "User has balance of $100.00": setup_user_balance
}
```

**Matching Rules for Flexible Contracts:**
```python
from pact import Like, EachLike, Term

# Match type, not specific values
pact.will_respond_with(
    status=200,
    body={
        "id": Like(123),  # Match any integer
        "email": Term(r".+@.+", "test@example.com"),  # Match email pattern
        "items": EachLike({"name": "Product", "price": 9.99}, minimum=1)  # Array matching
    }
)
```

### P-FRONTEND-DEV

The platform supports frontend development through mock API generation and type-safe client generation.

#### Mock API Server

Generate a mock API server from OpenAPI specifications for frontend development without backend dependencies:

```python
from tools.api_testing_platform import MockAPIServer

# Create mock server from OpenAPI spec
mock_server = MockAPIServer.from_openapi("openapi.yaml")

# Configure mock behavior
mock_server.configure(
    port=8080,
    realistic_data=True,  # Generate realistic test data
    response_delay_ms=50,  # Simulate network latency
    error_rate=0.05  # 5% random errors for robustness testing
)

# Start server
mock_server.start()
print("Mock API server running at http://localhost:8080")

# Server automatically provides:
# - All endpoints from OpenAPI spec
# - Realistic response data matching schemas
# - Proper status codes and headers
# - CORS support for frontend development

# Use in frontend development
"""
// Frontend code (JavaScript/TypeScript)
const response = await fetch('http://localhost:8080/api/v1/users/123');
const user = await response.json();
console.log(user);  // Realistic mock data
"""
```

#### TypeScript Type Generation

Generate type-safe API clients and interfaces for TypeScript/JavaScript frontends:

```python
from tools.api_testing_platform import TypeScriptGenerator

# Generate TypeScript types from OpenAPI spec
ts_generator = TypeScriptGenerator()

ts_code = ts_generator.generate_from_spec(
    spec_file="openapi.yaml",
    output_dir="frontend/src/api/",
    client_library="axios",  # Options: axios, fetch, none
    include_validators=True,  # Include runtime validation
    style="zod"  # Options: zod, io-ts, class-validator
)

print(f"Generated TypeScript files:")
for file in ts_code.files:
    print(f"  - {file.path}")
```

**Generated TypeScript Example:**

```typescript
// frontend/src/api/types.ts (generated)
export interface User {
  id: number;
  name: string;
  email: string;
  created_at: string;
}

export interface CreateUserRequest {
  name: string;
  email: string;
}

// frontend/src/api/user-service.ts (generated)
import axios, { AxiosInstance } from 'axios';
import { User, CreateUserRequest } from './types';

export class UserService {
  private client: AxiosInstance;

  constructor(baseURL: string = 'https://api.example.com') {
    this.client = axios.create({ baseURL });
  }

  async getUser(id: number): Promise<User> {
    const response = await this.client.get<User>(`/api/v1/users/${id}`);
    return response.data;
  }

  async createUser(data: CreateUserRequest): Promise<User> {
    const response = await this.client.post<User>('/api/v1/users', data);
    return response.data;
  }

  async listUsers(page?: number, limit?: number): Promise<User[]> {
    const response = await this.client.get<User[]>('/api/v1/users', {
      params: { page, limit }
    });
    return response.data;
  }
}
```

#### Frontend Contract Validation

Validate frontend API calls against contracts:

```python
from tools.api_testing_platform import FrontendContractValidator

validator = FrontendContractValidator()

# Extract API calls from frontend code
frontend_calls = validator.extract_api_calls(
    source_dir="frontend/src",
    patterns=["**/*.ts", "**/*.tsx"]
)

print(f"Found {len(frontend_calls)} API calls in frontend code")

# Validate against OpenAPI spec
violations = validator.validate_against_spec(
    api_calls=frontend_calls,
    spec_file="openapi.yaml"
)

if violations:
    print(f"✗ Found {len(violations)} contract violations:")
    for violation in violations:
        print(f"\n{violation.file}:{violation.line}")
        print(f"  Endpoint: {violation.endpoint}")
        print(f"  Issue: {violation.description}")
        if violation.suggestion:
            print(f"  Suggestion: {violation.suggestion}")
else:
    print("✓ All frontend API calls match contracts")
```

## Architecture

The API Testing & Contract Validation Platform consists of six core modules working together to provide comprehensive API testing capabilities:

### 1. ContractValidator

**Purpose**: OpenAPI specification validation and linting

**Responsibilities:**
- Parse OpenAPI 3.0/3.1 specifications (YAML/JSON)
- Perform syntax and semantic validation
- Apply linting rules for code quality and security
- Check backward compatibility between API versions
- Resolve multi-file specifications with `$ref` references

**Key Methods:**
- `validate_spec(spec_file, lint=False)` - Validate OpenAPI specification
- `check_compatibility(old_spec, new_spec)` - Check version compatibility
- `lint_spec(spec_file, rules)` - Apply linting rules
- `resolve_refs(spec_file)` - Resolve `$ref` references

### 2. TestGenerator

**Purpose**: Automatic test case generation from OpenAPI specifications

**Responsibilities:**
- Generate pytest test cases from OpenAPI definitions
- Implement property-based testing strategies
- Create negative test scenarios
- Generate parametrized tests for multiple inputs
- Support custom test templates

**Key Methods:**
- `generate_from_spec(spec_file, output_dir, template)` - Generate tests
- `generate_property_based_tests(spec_file)` - Property-based test generation
- `generate_negative_tests(spec_file)` - Negative scenario generation
- `customize_template(template_file, vars)` - Custom template rendering

### 3. APIClient

**Purpose**: HTTP client with authentication and retry logic

**Responsibilities:**
- Execute HTTP requests with session management
- Handle multiple authentication methods
- Implement automatic retry with exponential backoff
- Manage request/response logging
- Support rate limiting compliance

**Key Methods:**
- `request(method, path, **kwargs)` - Make HTTP request
- `get/post/put/delete/patch(path, **kwargs)` - Convenience methods
- `set_bearer_token(token)` - Configure bearer authentication
- `set_api_key(key, location, name)` - Configure API key auth
- `set_oauth2(**config)` - Configure OAuth2 authentication

### 4. PactManager

**Purpose**: Consumer-driven contract testing

**Responsibilities:**
- Create and manage Pact contracts
- Integrate with Pact broker for contract storage
- Verify provider implementations against contracts
- Execute Can-I-Deploy safety checks
- Handle contract versioning and tagging

**Key Methods:**
- `given(state).upon_receiving(description).with_request().will_respond_with()` - Define interaction
- `publish_to_broker(pact_file, broker_url, version, tags)` - Publish contract
- `verify_provider(provider_base_url, **config)` - Verify provider
- `can_i_deploy(participant, version, to_environment)` - Deployment check

### 5. SchemaValidator

**Purpose**: Request/response schema validation

**Responsibilities:**
- Validate requests against OpenAPI request schemas
- Validate responses against OpenAPI response schemas
- Support custom format validators
- Provide detailed validation error messages
- Handle strict vs. lenient validation modes

**Key Methods:**
- `load_spec(spec_file)` - Load OpenAPI specification
- `validate_request(request, endpoint, method)` - Validate request
- `validate_response(response, endpoint, method, status_code)` - Validate response
- `add_custom_format(name, validator)` - Register custom format

### 6. RegressionEngine

**Purpose**: API regression testing and change detection

**Responsibilities:**
- Capture and store baseline API responses
- Compare current responses against baselines
- Detect breaking changes in API behavior
- Track performance regressions
- Manage baseline approval workflow

**Key Methods:**
- `save_baseline(endpoint, method, response, version)` - Create baseline
- `run_regression_tests(client, baseline_version, current_version)` - Run tests
- `compare_responses(baseline, current)` - Compare responses
- `detect_breaking_changes(comparison)` - Identify breaking changes
- `approve_baseline_update(endpoint, method, version)` - Approve new baseline

### Module Interactions

```
┌─────────────────────┐
│  ContractValidator  │ ──> Validates OpenAPI specs
└──────────┬──────────┘
           │
           ▼
    ┌──────────────┐
    │TestGenerator │ ──> Generates test cases
    └──────┬───────┘
           │
           ▼
    ┌─────────────┐       ┌────────────────┐
    │  APIClient  │ ◄───> │SchemaValidator │
    └──────┬──────┘       └────────────────┘
           │                    Validates schemas
           ▼
    ┌──────────────────┐
    │ RegressionEngine │ ──> Detects changes
    └──────────────────┘

    ┌──────────────┐
    │ PactManager  │ ──> Contract testing
    └──────────────┘
```

## Troubleshooting

### OpenAPI Validation Errors

**Issue**: `Invalid OpenAPI specification: Missing required field 'paths'`

**Solution**:
```python
# Ensure your OpenAPI spec has required fields
{
  "openapi": "3.0.0",
  "info": {
    "title": "My API",
    "version": "1.0.0"
  },
  "paths": {}  # Required field
}
```

**Issue**: `$ref resolution failed: File not found`

**Solution**:
```python
# Provide base path for multi-file specs
validator = ContractValidator()
result = validator.validate_spec(
    spec_file="openapi.yaml",
    resolve_refs=True,
    base_path="/path/to/specs"  # Directory containing referenced files
)
```

**Issue**: `Linting error: operation-operationId is required`

**Solution**:
```yaml
# Add operationId to all operations in OpenAPI spec
paths:
  /api/v1/users:
    get:
      operationId: listUsers  # Add this
      summary: List all users
      responses:
        200:
          description: Success
```

### Test Generation Failures

**Issue**: `No tests generated from specification`

**Solution**:
```python
# Check that spec has valid endpoints
generator = TestGenerator()
tests = generator.generate_from_spec(
    spec_file="openapi.yaml",
    output_dir="tests/",
    verbose=True  # Enable verbose logging
)

# Check generator logs for specific issues
```

**Issue**: `Template rendering failed`

**Solution**:
```python
# Verify custom template syntax
generator = TestGenerator()
tests = generator.generate_from_spec(
    spec_file="openapi.yaml",
    output_dir="tests/",
    template_file="custom_template.j2",  # Check template syntax
    template_vars={"base_url": "https://api.example.com"}
)
```

**Issue**: `Generated tests have import errors`

**Solution**:
```bash
# Ensure pytest and dependencies are installed
pip install pytest requests jsonschema

# Run generated tests
pytest tests/generated/ -v
```

### Authentication Issues

**Issue**: `401 Unauthorized` errors

**Solution**:
```python
# Verify token is valid and not expired
import os
token = os.getenv("API_TOKEN")
print(f"Token: {token[:10]}...")  # Verify token is loaded

client = APIClient(base_url="https://api.example.com")
client.set_bearer_token(token)

# Test authentication
response = client.get("/api/v1/test")
print(f"Status: {response.status_code}")
```

**Issue**: `OAuth2 token refresh failed`

**Solution**:
```python
# Check OAuth2 configuration
client = APIClient(base_url="https://api.example.com")
client.set_oauth2(
    token_url="https://auth.example.com/oauth/token",  # Verify URL
    client_id="your-client-id",
    client_secret="your-client-secret",
    scope="read write"
)

# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)
```

**Issue**: `API key not being sent in requests`

**Solution**:
```python
# Verify API key configuration
client = APIClient(base_url="https://api.example.com")
client.set_api_key(
    api_key="your-key",
    location="header",  # or "query"
    name="X-API-Key"  # Verify header/param name
)

# Check request headers
response = client.get("/api/v1/data")
print(f"Request headers: {response.request.headers}")
```

### Pact Broker Connectivity

**Issue**: `Connection refused to Pact broker`

**Solution**:
```bash
# Check broker is running
curl https://pact-broker.example.com

# Verify credentials
export PACT_BROKER_USERNAME=user
export PACT_BROKER_PASSWORD=pass

# Test connection
python -c "from tools.api_testing_platform import PactManager; pact = PactManager(); print('Connected')"
```

**Issue**: `Pact publish failed: Unauthorized`

**Solution**:
```python
# Use correct authentication method
pact = PactManager()
pact.publish_to_broker(
    pact_file="pacts/consumer-provider.json",
    broker_url="https://pact-broker.example.com",
    # Use token OR username/password
    broker_token="your-token",  # Preferred
    # OR
    # broker_username="user",
    # broker_password="pass",
    version="1.0.0"
)
```

**Issue**: `Provider verification failed: State handler not found`

**Solution**:
```python
# Define all required state handlers
def setup_user_exists():
    create_test_user(id=123)

def setup_product_available():
    create_test_product(id=456, in_stock=True)

state_handlers = {
    "User exists with ID 123": setup_user_exists,
    "Product is available": setup_product_available
}

# Verify handler names match exactly
verification = pact.verify_provider(
    provider_base_url="http://localhost:8080",
    state_handlers=state_handlers
)
```

### Schema Validation Failures

**Issue**: `Schema validation failed: Additional property not allowed`

**Solution**:
```python
# Use lenient mode for backward compatibility
validator = SchemaValidator()
validator.load_spec("openapi.yaml")

validation = validator.validate_response(
    response=response,
    endpoint="/api/v1/users",
    method="GET",
    status_code=200,
    strict_mode=False  # Allow additional properties
)
```

**Issue**: `Format validation failed for custom format`

**Solution**:
```python
# Register custom format validator
import re

def validate_phone(value):
    pattern = r'^\+?[1-9]\d{1,14}$'
    return bool(re.match(pattern, value))

validator = SchemaValidator()
validator.add_custom_format("phone", validate_phone)
validator.load_spec("openapi.yaml")
```

### Regression Baseline Issues

**Issue**: `Baseline not found for endpoint`

**Solution**:
```python
# Create baseline first
regression = RegressionEngine(baseline_dir="baselines/")
client = APIClient(base_url="https://api.example.com")

# Capture baseline
response = client.get("/api/v1/users")
regression.save_baseline(
    endpoint="/api/v1/users",
    method="GET",
    response=response,
    version="v1.0.0"
)

# Then run regression tests
results = regression.run_regression_tests(
    client=client,
    baseline_version="v1.0.0"
)
```

**Issue**: `False positive: Response differs but no breaking change`

**Solution**:
```python
# Configure fields to ignore
regression = RegressionEngine(
    baseline_dir="baselines/",
    ignore_fields=[
        "timestamp",
        "_metadata.generated_at",
        "request_id"
    ]
)

# Or use lenient comparison mode
comparison = regression.compare_responses(
    baseline_response=baseline,
    current_response=current,
    strict_mode=False  # Ignore non-breaking changes
)
```

### Performance Problems

**Issue**: `Tests running too slowly`

**Solution**:
```bash
# Enable parallel execution
pytest tests/ -n 8  # Use 8 parallel workers

# Or use pytest-xdist auto mode
pytest tests/ -n auto
```

**Issue**: `High memory usage during test generation`

**Solution**:
```python
# Generate tests in batches
generator = TestGenerator()

# Process endpoints in chunks
endpoints = get_all_endpoints("openapi.yaml")
chunk_size = 50

for i in range(0, len(endpoints), chunk_size):
    chunk = endpoints[i:i + chunk_size]
    tests = generator.generate_tests(
        endpoints=chunk,
        output_dir=f"tests/batch_{i}"
    )
```

**Issue**: `Rate limiting errors from API`

**Solution**:
```python
# Configure rate limiting
client = APIClient(
    base_url="https://api.example.com",
    rate_limit=10,  # 10 requests per second
    rate_limit_period=1.0  # 1 second window
)

# Add delays between requests
import time
for endpoint in endpoints:
    response = client.get(endpoint)
    time.sleep(0.1)  # 100ms delay
```

## Contributing

We welcome contributions to the API Testing & Contract Validation Platform! This project is part of the devCrew_s1 initiative.

### How to Contribute

1. **Fork the Repository**
   ```bash
   git clone https://github.com/your-org/devCrew_s1.git
   cd devCrew_s1/tools/api_testing_platform
   ```

2. **Create a Feature Branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make Your Changes**
   - Follow Python best practices (PEP 8)
   - Add type hints to all functions
   - Write comprehensive docstrings (Google style)
   - Add unit tests for new features (85%+ coverage)
   - Update documentation as needed

4. **Run Tests**
   ```bash
   pytest tests/ -v --cov=tools.api_testing_platform --cov-report=html
   ```

5. **Run Code Quality Checks**
   ```bash
   # Format code
   black tools/api_testing_platform/
   isort tools/api_testing_platform/

   # Lint code
   flake8 tools/api_testing_platform/
   pylint tools/api_testing_platform/

   # Type checking
   mypy tools/api_testing_platform/ --ignore-missing-imports

   # Security scanning
   bandit -r tools/api_testing_platform/
   ```

6. **Commit Your Changes**
   ```bash
   git add .
   git commit -m "feat: add new feature"
   ```

7. **Push and Create Pull Request**
   ```bash
   git push origin feature/your-feature-name
   ```

### Development Guidelines

- **Code Style**: Follow PEP 8 and use Black formatter
- **Testing**: Maintain 85%+ test coverage
- **Documentation**: Update README and add docstrings
- **Security**: Never commit sensitive data or credentials
- **Performance**: Consider performance impact of changes

### Reporting Issues

Please report issues on the devCrew_s1 GitHub repository with:
- Clear description of the problem
- Steps to reproduce
- Expected vs. actual behavior
- OpenAPI spec examples (if applicable)
- Error messages and logs

## License

This project is licensed under the Apache License 2.0.

```
Copyright 2025 DevCrew Team

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
```

### Third-Party Licenses

This platform uses the following open-source libraries:
- **Pact Python**: MIT License
- **Schemathesis**: MIT License
- **pytest**: MIT License
- **requests**: Apache 2.0
- **jsonschema**: MIT License
- **OpenAPI Spec Validator**: Apache 2.0

See individual package documentation for full license details.

## References

### OpenAPI Specification
- **OpenAPI 3.0 Specification**: https://spec.openapis.org/oas/v3.0.3.html
- **OpenAPI 3.1 Specification**: https://spec.openapis.org/oas/v3.1.0.html
- **Swagger Editor**: https://editor.swagger.io/
- **OpenAPI Generator**: https://openapi-generator.tech/

### Pact Contract Testing
- **Pact Documentation**: https://docs.pact.io/
- **Pact Python**: https://github.com/pact-foundation/pact-python
- **Pact Broker**: https://docs.pact.io/pact_broker
- **PactFlow**: https://pactflow.io/
- **Can-I-Deploy Guide**: https://docs.pact.io/pact_broker/can_i_deploy

### API Testing Tools
- **Schemathesis**: https://schemathesis.readthedocs.io/
- **pytest**: https://docs.pytest.org/
- **requests**: https://requests.readthedocs.io/
- **Hypothesis**: https://hypothesis.readthedocs.io/
- **Tavern**: https://tavern.readthedocs.io/

### Schema Validation
- **JSON Schema**: https://json-schema.org/
- **JSON Schema Validator**: https://python-jsonschema.readthedocs.io/
- **OpenAPI Core**: https://github.com/p1c2u/openapi-core

### Authentication
- **OAuth 2.0 RFC**: https://oauth.net/2/
- **JWT**: https://jwt.io/
- **requests-oauthlib**: https://requests-oauthlib.readthedocs.io/

### CI/CD Integration
- **GitHub Actions**: https://docs.github.com/en/actions
- **GitLab CI**: https://docs.gitlab.com/ee/ci/
- **Jenkins**: https://www.jenkins.io/doc/

### Related Resources
- **REST API Best Practices**: https://restfulapi.net/
- **API Security Best Practices**: https://owasp.org/www-project-api-security/
- **Microservices Testing**: https://martinfowler.com/articles/microservice-testing/

---

**Tool ID**: TOOL-DEV-003
**Version**: 1.0.0
**Last Updated**: 2025-12-03
**Maintained by**: DevCrew Team (devCrew_s1)
