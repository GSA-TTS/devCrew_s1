# Threat Intelligence Platform Test Suite

Comprehensive test suite for the Threat Intelligence Platform (TOOL-SEC-008) with integration tests, performance benchmarks, and extensive test coverage.

## Overview

This test suite provides:
- **Integration Tests**: End-to-end workflow testing
- **Performance Tests**: Benchmarking key operations
- **Unit Tests**: Individual module testing
- **Mock Data**: Realistic test fixtures
- **90%+ Coverage**: Comprehensive test coverage

## Test Structure

```
tests/
├── __init__.py                    # Test suite initialization
├── conftest.py                    # Pytest configuration and fixtures
├── test_integration.py            # Integration tests
├── test_performance.py            # Performance benchmarks
├── requirements-test.txt          # Test dependencies
├── fixtures/                      # Test data and mock objects
│   ├── __init__.py
│   ├── sample_stix_objects.json   # STIX test data
│   ├── sample_cve_data.json       # CVE test data
│   ├── sample_ioc_data.json       # IOC test data
│   ├── sample_sbom_spdx.json      # SPDX SBOM test data
│   ├── sample_sbom_cyclonedx.json # CycloneDX SBOM test data
│   └── sample_attack_techniques.json  # ATT&CK test data
└── README.md                      # This file
```

## Installation

### Install Test Dependencies

```bash
# Navigate to test directory
cd tools/threat_intelligence/tests/

# Install all test dependencies
pip install -r requirements-test.txt
```

### Dependencies Overview

- **pytest**: Core testing framework
- **pytest-asyncio**: Async test support
- **pytest-mock**: Mocking utilities
- **pytest-cov**: Code coverage reporting
- **pytest-benchmark**: Performance benchmarking
- **responses**: HTTP mocking
- **faker**: Test data generation

## Running Tests

### Run All Tests

```bash
# Run all tests with verbose output
pytest tools/threat_intelligence/tests/ -v

# Run tests with coverage report
pytest tools/threat_intelligence/tests/ --cov=tools/threat_intelligence --cov-report=html

# Run tests in parallel (faster)
pytest tools/threat_intelligence/tests/ -n auto
```

### Run Specific Test Categories

```bash
# Run only integration tests
pytest tools/threat_intelligence/tests/test_integration.py -v

# Run only performance tests
pytest tools/threat_intelligence/tests/test_performance.py -v

# Run tests matching a pattern
pytest tools/threat_intelligence/tests/ -k "stix" -v

# Run tests for a specific class
pytest tools/threat_intelligence/tests/test_integration.py::TestFullThreatIntelligenceWorkflow -v
```

### Run with Coverage

```bash
# Generate HTML coverage report
pytest tools/threat_intelligence/tests/ \
    --cov=tools/threat_intelligence \
    --cov-report=html \
    --cov-report=term

# View coverage report
open htmlcov/index.html

# Generate XML coverage report (for CI/CD)
pytest tools/threat_intelligence/tests/ \
    --cov=tools/threat_intelligence \
    --cov-report=xml
```

### Run Performance Tests

```bash
# Run performance tests with benchmarking
pytest tools/threat_intelligence/tests/test_performance.py -v

# Run with benchmark comparison
pytest tools/threat_intelligence/tests/test_performance.py --benchmark-compare

# Save benchmark results
pytest tools/threat_intelligence/tests/test_performance.py --benchmark-save=baseline

# Compare against baseline
pytest tools/threat_intelligence/tests/test_performance.py --benchmark-compare=baseline
```

## Test Coverage

### Integration Test Coverage

**Test Classes:**
1. `TestFullThreatIntelligenceWorkflow`
   - Complete end-to-end workflow
   - STIX/TAXII feed ingestion
   - CVE sync and correlation
   - VEX document generation

2. `TestAttackMappingWorkflow`
   - ATT&CK technique mapping
   - Coverage analysis
   - Detection gap identification
   - Navigator layer generation

3. `TestIOCWorkflow`
   - IOC extraction from feeds
   - OSINT enrichment
   - Multi-format export (STIX, CSV, MISP)
   - Lifecycle management

4. `TestVEXGeneration`
   - OpenVEX document generation
   - CSAF 2.0 format support
   - SBOM correlation

5. `TestThreatCorrelation`
   - Multi-source correlation
   - Risk score calculation
   - Asset vulnerability matching

6. `TestIntelligenceEnrichment`
   - OSINT enrichment
   - Threat actor tracking
   - Campaign analysis

7. `TestReportGeneration`
   - JSON, PDF, HTML reports
   - Comprehensive threat intelligence reports

### Performance Test Coverage

**Benchmarks:**
1. **Indicator Processing**
   - Target: 10,000 indicators/minute
   - STIX bundle processing
   - Parallel processing

2. **Correlation Performance**
   - Target: <1 second for 1,000 assets
   - Risk scoring
   - SBOM correlation

3. **VEX Generation**
   - Target: <500ms per document
   - OpenVEX format
   - CSAF format

4. **Feed Updates**
   - Target: <15 minutes for full update
   - Incremental updates

5. **Database Operations**
   - Bulk indexing
   - Query performance

6. **IOC Enrichment**
   - Enrichment throughput
   - API call optimization

### Module Coverage

| Module | Coverage Target | Test Count | Status |
|--------|----------------|------------|--------|
| Feed Aggregator | 90%+ | 15+ | ✅ |
| Threat Correlator | 90%+ | 12+ | ✅ |
| ATT&CK Mapper | 90%+ | 10+ | ✅ |
| VEX Generator | 90%+ | 8+ | ✅ |
| IOC Manager | 90%+ | 12+ | ✅ |
| Intelligence Enricher | 90%+ | 8+ | ✅ |
| CLI Interface | 85%+ | 10+ | ✅ |

**Total Tests**: 75+ integration and performance tests

## Test Fixtures

### STIX Objects
- Indicators (IP, domain, file hash)
- Malware objects
- Threat actors
- Attack patterns
- Relationships

### CVE Data
- Critical, High, Medium severity CVEs
- CVSS v3 scores and vectors
- CWE classifications
- Affected products and versions

### IOC Data
- IP addresses with geolocation
- Domains with DNS records
- File hashes with signatures
- URLs and email addresses

### SBOM Data
- SPDX 2.3 format
- CycloneDX 1.5 format
- Package dependencies
- Vulnerability references

### ATT&CK Data
- Techniques with sub-techniques
- Tactics and platforms
- Data sources and mitigations

## Mocking Strategy

### Elasticsearch
```python
mock_elasticsearch.search = Mock(return_value={"hits": {"hits": []}})
mock_elasticsearch.bulk = Mock(return_value={"errors": False})
```

### TAXII Server
```python
mock_taxii_server.get_collections = Mock(return_value=[...])
mock_taxii_server.get_objects = Mock(return_value={...})
```

### External APIs
```python
with patch("module.ExternalAPI") as mock_api:
    mock_api.return_value.fetch = AsyncMock(return_value={...})
```

## Performance Targets

### Processing Targets
- **Indicator Processing**: ≥10,000 indicators/minute
- **Asset Correlation**: <1 second for 1,000 assets
- **VEX Generation**: <500ms per document
- **Feed Updates**: <15 minutes for full update
- **Database Queries**: <50ms average

### Scalability Targets
- Support 10M+ indicators
- Sub-second query response
- Parallel processing with 4+ workers
- Efficient bulk operations

## CI/CD Integration

### GitHub Actions

```yaml
name: Test Suite

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r tests/requirements-test.txt
      - name: Run tests
        run: |
          pytest tools/threat_intelligence/tests/ \
            --cov=tools/threat_intelligence \
            --cov-report=xml \
            --cov-report=term
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

## Writing New Tests

### Integration Test Template

```python
@pytest.mark.asyncio
async def test_new_workflow(
    sample_fixture: Dict[str, Any],
    mock_service: Mock,
) -> None:
    """Test description."""
    # Arrange
    with patch("module.Service") as mock:
        mock.return_value.method = AsyncMock(return_value={...})

        # Act
        result = await mock.return_value.method()

        # Assert
        assert result["status"] == "success"
```

### Performance Test Template

```python
@pytest.mark.asyncio
async def test_new_performance(
    performance_test_data: Dict[str, Any],
) -> None:
    """Test performance description."""
    target_time = 1.0  # seconds

    # Benchmark
    start_time = time.time()
    result = await perform_operation()
    elapsed_time = time.time() - start_time

    # Assert
    assert elapsed_time < target_time
```

## Troubleshooting

### Common Issues

**Issue**: `pytest: command not found`
```bash
pip install pytest
```

**Issue**: `ModuleNotFoundError: No module named 'pytest_asyncio'`
```bash
pip install -r tests/requirements-test.txt
```

**Issue**: Tests hang on async operations
```bash
# Add timeout decorator
@pytest.mark.timeout(30)
async def test_function():
    ...
```

**Issue**: Coverage report not generated
```bash
# Ensure pytest-cov is installed
pip install pytest-cov

# Check coverage configuration in setup.cfg or pyproject.toml
```

## Best Practices

### Test Organization
1. Group related tests in classes
2. Use descriptive test names
3. Follow AAA pattern (Arrange, Act, Assert)
4. Keep tests independent

### Fixtures
1. Use fixtures for reusable test data
2. Define fixtures in conftest.py
3. Scope fixtures appropriately
4. Clean up resources in teardown

### Mocking
1. Mock external dependencies
2. Use AsyncMock for async methods
3. Verify mock calls when necessary
4. Reset mocks between tests

### Performance Testing
1. Set clear performance targets
2. Use warm-up iterations
3. Run multiple iterations
4. Report metrics clearly

### Coverage
1. Aim for 90%+ coverage
2. Test error paths
3. Test edge cases
4. Don't test external libraries

## Contributing

When adding new tests:
1. Follow existing test structure
2. Add fixtures to conftest.py
3. Update this README
4. Ensure tests pass locally
5. Check coverage impact

## Resources

- [pytest Documentation](https://docs.pytest.org/)
- [pytest-asyncio](https://pytest-asyncio.readthedocs.io/)
- [pytest-cov](https://pytest-cov.readthedocs.io/)
- [STIX 2.1 Specification](https://oasis-open.github.io/cti-documentation/)
- [MITRE ATT&CK](https://attack.mitre.org/)

## Support

For issues or questions:
1. Check this README
2. Review test examples
3. Check pytest documentation
4. Open an issue in the repository
