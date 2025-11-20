# Issue #41: Customer Data Management & API Gateway Integration Platform

**Tool ID**: TOOL-API-001
**Priority**: LOW (High Impact - 9 protocols)
**Version**: 1.0.0

## Table of Contents

1. [Overview](#overview)
2. [Features](#features)
3. [Architecture](#architecture)
4. [Installation](#installation)
5. [Quick Start](#quick-start)
6. [API Reference](#api-reference)
7. [Protocol Integration](#protocol-integration)
8. [Privacy Compliance](#privacy-compliance)
9. [Configuration](#configuration)
10. [Testing](#testing)
11. [Deployment](#deployment)
12. [Performance](#performance)
13. [Troubleshooting](#troubleshooting)
14. [Contributing](#contributing)

---

## Overview

The Customer Data Management & API Gateway Integration Platform is a comprehensive solution for managing customer data with built-in privacy compliance, API gateway integration, and multi-format feedback ingestion. It provides enterprise-grade features including JWT/OAuth2 authentication, Redis-based rate limiting, PII detection, GDPR compliance, and Airflow data pipelines.

### Key Capabilities

- **Customer Data CRUD**: Full create, read, update, delete operations with validation
- **API Gateway Integration**: Kong and Tyk support for route management and plugins
- **Privacy Compliance**: PII detection, GDPR compliance, consent management
- **Feedback Ingestion**: Multi-format (JSON, CSV) feedback collection and processing
- **Data Pipelines**: Apache Airflow DAGs for ETL and data enrichment
- **Authentication**: JWT tokens, OAuth2 flows, API key management
- **Rate Limiting**: Per-user, per-IP, and global rate limiting with Redis
- **Audit Logging**: Comprehensive audit trail for compliance

### Technology Stack

- **Framework**: FastAPI 0.104+
- **Database**: PostgreSQL 15.0+
- **Cache**: Redis 7.2+
- **API Gateway**: Kong 3.4+ / Tyk
- **Data Pipelines**: Apache Airflow 2.7+
- **Authentication**: JWT, OAuth2
- **Testing**: pytest, pytest-asyncio, pytest-cov

---

## Features

### Core Features

1. **Customer Data Management**
   - Create, read, update, delete customers
   - Soft and hard delete support
   - Data validation and sanitization
   - Batch operations

2. **Privacy & Compliance**
   - PII detection (email, phone, SSN, credit card)
   - Data anonymization and pseudonymization
   - GDPR consent management
   - Right to erasure implementation

3. **Feedback System**
   - Multi-format ingestion (JSON, CSV)
   - Real-time and batch processing
   - Sentiment analysis
   - Deduplication

4. **Authentication & Authorization**
   - JWT token-based authentication
   - OAuth2 flows
   - API key management
   - Role-based access control (RBAC)

5. **Rate Limiting**
   - Per-user limits (1000/hour)
   - Per-IP limits (100/minute)
   - Global limits (10000/minute)
   - Configurable thresholds

6. **API Gateway Integration**
   - Kong route and service management
   - Tyk API definition support
   - Plugin configuration (JWT, CORS, rate limiting)
   - Health monitoring

7. **Data Pipelines**
   - Customer data ETL
   - Feedback processing with sentiment analysis
   - Data enrichment workflows
   - Quality monitoring

---

## Architecture

### System Architecture

```
┌─────────────┐     ┌──────────────┐     ┌────────────┐
│   Client    │────▶│ API Gateway  │────▶│  FastAPI   │
│             │     │  (Kong/Tyk)  │     │    App     │
└─────────────┘     └──────────────┘     └────────────┘
                                                │
                    ┌───────────────────────────┼────────────────┐
                    │                           │                │
              ┌─────▼──────┐           ┌───────▼────┐   ┌──────▼─────┐
              │ PostgreSQL │           │   Redis    │   │  Airflow   │
              │  Database  │           │   Cache    │   │ Pipelines  │
              └────────────┘           └────────────┘   └────────────┘
```

### Module Structure

- **issue_41_fastapi_app.py**: Main FastAPI application with all endpoints
- **issue_41_customer_data.py**: Customer CRUD operations and SQLAlchemy models
- **issue_41_authentication.py**: JWT/OAuth2/API key authentication
- **issue_41_rate_limiter.py**: Redis-based rate limiting
- **issue_41_privacy_compliance.py**: PII detection and GDPR compliance
- **issue_41_feedback_ingestion.py**: Multi-format feedback processing
- **issue_41_api_gateway.py**: Kong/Tyk integration
- **issue_41_audit_logger.py**: Audit logging for compliance
- **issue_41_data_pipeline.py**: Airflow DAGs for data workflows

---

## Installation

### Prerequisites

- Python 3.11+
- PostgreSQL 15.0+
- Redis 7.2+
- Docker & Docker Compose (for containerized deployment)
- Kong 3.4+ or Tyk (optional, for API gateway)

### Step 1: Clone Repository

```bash
git clone <repository-url>
cd devCrew_s1
```

### Step 2: Install Dependencies

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r issue_41_requirements.txt
```

### Step 3: Configure Environment

```bash
# Copy example configuration
cp issue_41_config.yaml config.yaml

# Edit configuration file
vim config.yaml  # Update database, Redis, and secret keys
```

### Step 4: Initialize Database

```bash
# Create database tables
python -c "from issue_41_customer_data import create_tables; create_tables()"
```

### Step 5: Start Services (Docker)

```bash
# Start all services
docker-compose -f issue_41_docker-compose.yaml up -d

# Check service health
docker-compose -f issue_41_docker-compose.yaml ps
```

---

## Quick Start

### Start FastAPI Application

```bash
# Development mode with hot reload
python issue_41_fastapi_app.py

# Or using uvicorn directly
uvicorn issue_41_fastapi_app:app --host 0.0.0.0 --port 8000 --reload
```

### Access API Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Basic Usage Examples

#### 1. Create a Customer

```bash
curl -X POST http://localhost:8000/api/customers \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john.doe@example.com",
    "full_name": "John Doe",
    "phone": "+1234567890",
    "company": "Acme Corp"
  }'
```

Response:
```json
{
  "customer_id": "CUST_A1B2C3D4E5F6",
  "email": "john.doe@example.com",
  "full_name": "John Doe",
  "created_at": "2024-01-15T10:30:00Z"
}
```

#### 2. Get Customer

```bash
curl -X GET http://localhost:8000/api/customers/CUST_A1B2C3D4E5F6 \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

#### 3. Submit Feedback

```bash
curl -X POST http://localhost:8000/api/feedback \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": "CUST_A1B2C3D4E5F6",
    "feedback_type": "feature_request",
    "subject": "Add dark mode",
    "content": "Would love to see a dark mode option",
    "source": "api",
    "rating": 5
  }'
```

#### 4. Upload Feedback CSV

```bash
curl -X POST http://localhost:8000/api/feedback/upload/csv \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "file=@feedback.csv"
```

---

## API Reference

### Authentication Endpoints

#### POST /auth/login
Login with username and password.

**Request Body:**
```json
{
  "username": "string",
  "password": "string"
}
```

**Response:**
```json
{
  "access_token": "string",
  "refresh_token": "string",
  "token_type": "bearer",
  "expires_in": 1800
}
```

#### POST /auth/refresh
Refresh access token.

**Request Body:**
```json
{
  "refresh_token": "string"
}
```

### Customer Endpoints

#### POST /api/customers
Create a new customer.

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "email": "string",
  "full_name": "string",
  "phone": "string",
  "company": "string",
  "address": "string",
  "metadata": {}
}
```

#### GET /api/customers/{customer_id}
Get customer by ID.

**Headers:** `Authorization: Bearer <token>`

#### GET /api/customers
List customers with pagination.

**Query Parameters:**
- `skip` (int): Number of records to skip (default: 0)
- `limit` (int): Maximum records (default: 100, max: 1000)
- `is_active` (bool): Filter by active status

#### PUT /api/customers/{customer_id}
Update customer information.

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "email": "string",
  "full_name": "string",
  "phone": "string",
  "is_active": true
}
```

#### DELETE /api/customers/{customer_id}
Delete customer (soft delete by default).

**Query Parameters:**
- `hard_delete` (bool): If true, permanently delete (default: false)

### Privacy Endpoints

#### POST /api/privacy/consent
Grant privacy consent.

**Request Body:**
```json
{
  "customer_id": "string",
  "consent_type": "marketing|data_processing|data_sharing"
}
```

#### DELETE /api/privacy/consent
Revoke privacy consent.

#### POST /api/privacy/anonymize/{customer_id}
Anonymize customer PII data.

#### POST /api/privacy/erase/{customer_id}
Erase customer data (GDPR right to erasure).

#### GET /api/privacy/pii-scan
Scan text for PII.

**Query Parameters:**
- `text` (string): Text to scan

### Feedback Endpoints

#### POST /api/feedback
Submit customer feedback.

**Request Body:**
```json
{
  "customer_id": "string",
  "feedback_type": "bug_report|feature_request|general_feedback",
  "subject": "string",
  "content": "string",
  "source": "api|web_form|email",
  "rating": 1-5
}
```

#### POST /api/feedback/batch
Submit batch of feedback.

#### POST /api/feedback/upload/json
Upload feedback from JSON file.

#### POST /api/feedback/upload/csv
Upload feedback from CSV file.

**CSV Format:**
```csv
customer_id,feedback_type,subject,content,source,rating
CUST_123,feature_request,Dark Mode,Add dark mode,api,5
```

#### GET /api/feedback/{feedback_id}
Get feedback by ID.

#### GET /api/feedback
List feedback with filters.

**Query Parameters:**
- `customer_id` (string): Filter by customer
- `status` (string): Filter by status
- `skip` (int): Pagination offset
- `limit` (int): Page size

### Rate Limiting Headers

All responses include rate limit headers:

```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 950
X-RateLimit-Reset: 1705320000
```

---

## Protocol Integration

The platform supports 9 protocols for system integration:

### P-ADR-CREATION
Store Architecture Decision Records as structured customer data.

**Endpoint:** `POST /api/protocols/adr`

### P-BUG-PRIORITIZATION
Ingest bug data with automatic priority scoring.

**Endpoint:** `POST /api/protocols/bug`

### P-FEEDBACK-INGEST
Customer feedback collection and processing (core feature).

**Endpoint:** `POST /api/feedback`

### P-FILE-IO
File upload/download through API gateway.

**Endpoints:** `POST /api/feedback/upload/{format}`

### P-HANDOFF-PO-ARCH
Product-to-architecture data handoff.

**Endpoint:** `POST /api/protocols/handoff`

### P-ROADMAP-SYNC
Roadmap data synchronization.

**Endpoint:** `POST /api/protocols/roadmap-sync`

### P-STAKEHOLDER-COMM
Stakeholder notification via API webhooks.

**Configuration:** `webhooks` section in config.yaml

### P-CACHE-MANAGEMENT
Redis cache management for API responses.

**Endpoints:**
- `DELETE /api/cache/{cache_key}` - Clear specific key
- `DELETE /api/cache` - Clear all cache

### P-KNOW-KG-INTERACTION
Knowledge graph data access via API.

**Configuration:** Set `kg_interaction.endpoint` in config.yaml

---

## Privacy Compliance

### GDPR Compliance

The platform provides comprehensive GDPR compliance features:

1. **Lawful Basis**: Consent management for data processing
2. **Data Minimization**: Only collect necessary data
3. **Right to Access**: API endpoints for customer data retrieval
4. **Right to Rectification**: Update endpoints for data correction
5. **Right to Erasure**: Delete endpoints with audit logging
6. **Data Portability**: Export customer data in JSON format
7. **Privacy by Design**: PII detection and anonymization built-in

### PII Detection

Automatically detects:
- Email addresses
- Phone numbers
- Social Security Numbers (SSN)
- Credit card numbers
- IP addresses
- Names and addresses

### Data Anonymization

Three anonymization methods:

1. **Masking**: Replace characters with asterisks
   - Email: `j***@example.com`
   - Phone: `******7890`
   - SSN: `***-**-6789`

2. **Pseudonymization**: Hash with salt
   - Reversible with salt key
   - Maintains data relationships

3. **Complete Erasure**: Permanent deletion
   - 30-day grace period
   - Audit logging
   - Irreversible

### Consent Management

```python
# Grant consent
POST /api/privacy/consent
{
  "customer_id": "CUST_123",
  "consent_type": "data_processing"
}

# Revoke consent
DELETE /api/privacy/consent?customer_id=CUST_123&consent_type=data_processing

# Check consent status
GET /api/privacy/consent?customer_id=CUST_123
```

---

## Configuration

### Configuration File: issue_41_config.yaml

Key configuration sections:

```yaml
# Database
database:
  postgres:
    host: localhost
    port: 5432
    username: postgres
    password: YOUR_PASSWORD
    database: customer_db

# Redis
redis:
  host: localhost
  port: 6379

# Authentication
authentication:
  jwt:
    secret_key: YOUR_SECRET_KEY
    access_token_expire_minutes: 30

# Rate Limiting
rate_limiting:
  per_user:
    max_requests: 1000
    window_seconds: 3600
```

### Environment Variables

Override configuration with environment variables:

```bash
export DATABASE_HOST=localhost
export DATABASE_PORT=5432
export REDIS_HOST=localhost
export JWT_SECRET_KEY=your_secret_key
```

---

## Testing

### Run All Tests

```bash
# Run all tests with coverage
pytest issue_41_test_api.py -v --cov=. --cov-report=html

# Run specific test class
pytest issue_41_test_api.py::TestCustomerData -v

# Run specific test
pytest issue_41_test_api.py::TestAuthentication::test_jwt_token_creation -v
```

### Test Coverage

Aim for 90%+ test coverage:

```bash
# Generate coverage report
pytest --cov=. --cov-report=html
open htmlcov/index.html  # View report
```

### Mock Testing

Tests use mocked dependencies:
- Mock Redis client
- Mock database sessions
- Mock API gateway responses
- Faker for test data generation

### Integration Testing

```bash
# Start test environment
docker-compose -f issue_41_docker-compose.yaml up -d

# Run integration tests
pytest issue_41_test_api.py::TestIntegration -v

# Cleanup
docker-compose -f issue_41_docker-compose.yaml down -v
```

---

## Deployment

### Docker Deployment

```bash
# Build and start all services
docker-compose -f issue_41_docker-compose.yaml up -d --build

# View logs
docker-compose -f issue_41_docker-compose.yaml logs -f fastapi_app

# Scale application
docker-compose -f issue_41_docker-compose.yaml up -d --scale fastapi_app=3
```

### Production Deployment

1. **Update Configuration**
   - Set strong secret keys
   - Configure production database
   - Enable SSL/TLS
   - Set proper CORS origins

2. **Environment Variables**
```bash
export ENVIRONMENT=production
export DEBUG=false
export DATABASE_PASSWORD=strong_password
export JWT_SECRET_KEY=random_secret_key_here
```

3. **Database Migration**
```bash
# Run Alembic migrations
alembic upgrade head
```

4. **Start with Gunicorn**
```bash
gunicorn issue_41_fastapi_app:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --timeout 120 \
  --access-logfile - \
  --error-logfile -
```

### Kubernetes Deployment

See `k8s/` directory for Kubernetes manifests (coming soon).

---

## Performance

### Performance Targets

- **API Response Time**: <50ms (p95)
- **Throughput**: 1000+ requests/second
- **Database Queries**: <100ms for 90%
- **Cache Hit Rate**: 90%+

### Optimization Techniques

1. **Database Indexing**
   - Index on `customer_id`, `email`
   - Composite indexes for common queries

2. **Redis Caching**
   - Cache customer reads (10min TTL)
   - Cache feedback lists (5min TTL)

3. **Connection Pooling**
   - PostgreSQL: 10-100 connections
   - Redis: Connection pooling enabled

4. **Async Operations**
   - All database operations async
   - Parallel API requests

### Monitoring

```bash
# View metrics
curl http://localhost:9090/metrics

# Health check
curl http://localhost:8000/health/detailed
```

---

## Troubleshooting

### Common Issues

#### Database Connection Failed

```bash
# Check PostgreSQL is running
docker-compose ps postgres

# Check connection
psql -h localhost -U postgres -d customer_db

# Solution: Update DATABASE_HOST in config
```

#### Redis Connection Error

```bash
# Check Redis is running
redis-cli ping

# Solution: Start Redis
docker-compose up -d redis
```

#### Rate Limit Exceeded

```
HTTP 429 Too Many Requests
```

**Solution**: Wait for rate limit window to reset or contact admin to reset limit.

#### JWT Token Expired

```
HTTP 401 Unauthorized
```

**Solution**: Use refresh token to get new access token.

### Logs

```bash
# View application logs
docker-compose logs -f fastapi_app

# View Airflow logs
docker-compose logs -f airflow

# View audit logs
tail -f /var/log/customer_api/audit.log
```

### Debug Mode

```bash
# Enable debug mode
export DEBUG=true
export LOG_LEVEL=DEBUG

# Restart application
docker-compose restart fastapi_app
```

---

## Contributing

### Development Setup

1. Fork repository
2. Create feature branch: `git checkout -b feature/my-feature`
3. Install dev dependencies: `pip install -r issue_41_requirements.txt`
4. Make changes and add tests
5. Run tests: `pytest issue_41_test_api.py -v`
6. Run linters: `black . && flake8 && mypy .`
7. Commit changes: `git commit -m "Add feature"`
8. Push branch: `git push origin feature/my-feature`
9. Create Pull Request

### Code Quality

Run pre-commit checks:

```bash
# Install pre-commit
pip install pre-commit
pre-commit install

# Run all checks
pre-commit run --all-files
```

### Documentation

- Add docstrings to all functions
- Update README for new features
- Include usage examples
- Update API reference

---

## License

Copyright 2024. All rights reserved.

---

## Support

For issues and questions:
- Open GitHub issue
- Email: support@example.com
- Documentation: http://docs.example.com

---

## Changelog

### Version 1.0.0 (2024-01-15)
- Initial release
- Customer CRUD operations
- Privacy compliance features
- Feedback ingestion
- API gateway integration
- Airflow data pipelines
- Comprehensive test suite

---

**Built with FastAPI, PostgreSQL, Redis, Kong, and Apache Airflow**
