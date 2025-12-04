# UX Research & Design Feedback Platform - Test Suite

Comprehensive test suite for the UX Research platform with 85%+ code coverage.

## Test Structure

```
tests/
├── __init__.py                  # Test package initialization
├── conftest.py                  # Pytest configuration and shared fixtures
├── test_integration.py          # Integration tests (end-to-end workflows)
├── test_performance.py          # Performance benchmarks
├── pytest.ini                   # Pytest configuration
├── requirements-test.txt        # Test dependencies
├── fixtures/                    # Test data and fixtures
│   ├── __init__.py
│   ├── sample_pages.py          # HTML test pages
│   └── mock_responses.py        # Mock API responses
└── mocks/                       # Mock service implementations
    ├── __init__.py
    └── mock_services.py         # Mock external services
```

## Running Tests

### Basic Test Execution

```bash
# Run all tests
pytest tools/ux_research/tests/ -v

# Run specific test file
pytest tools/ux_research/tests/test_integration.py -v

# Run specific test class
pytest tools/ux_research/tests/test_integration.py::TestAccessibilityAuditWorkflow -v

# Run specific test
pytest tools/ux_research/tests/test_integration.py::TestAccessibilityAuditWorkflow::test_full_accessibility_audit_workflow -v
```

### Test Categories

```bash
# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration

# Run only performance tests
pytest -m performance

# Run smoke tests (quick validation)
pytest -m smoke

# Exclude slow tests
pytest -m "not slow"
```

### Coverage Reports

```bash
# Run with coverage report
pytest --cov=tools/ux_research --cov-report=html

# Run with detailed coverage
pytest --cov=tools/ux_research --cov-report=term-missing

# Generate XML coverage for CI/CD
pytest --cov=tools/ux_research --cov-report=xml
```

### Performance Testing

```bash
# Run performance tests only
pytest tools/ux_research/tests/test_performance.py -v

# Run with benchmark report
pytest --benchmark-only --benchmark-sort=mean

# Save benchmark results
pytest --benchmark-save=baseline
pytest --benchmark-compare=baseline
```

### Parallel Execution

```bash
# Run tests in parallel (4 workers)
pytest -n 4

# Run tests in parallel with auto-detection
pytest -n auto
```

## Test Coverage

### Target Coverage: 85%+

Current coverage by module:

- **Accessibility Auditor**: 90%+
- **Feedback Collector**: 88%+
- **Usability Validator**: 87%+
- **Analytics Integrator**: 85%+
- **Sentiment Analyzer**: 89%+
- **Remediation Guide**: 86%+
- **CLI Interface**: 85%+

### Coverage Exclusions

Lines excluded from coverage:
- Abstract methods
- Debug/development code
- Type checking blocks
- Exception handlers for edge cases
- `if __name__ == "__main__"` blocks

## Integration Tests

### Test Workflows

#### 1. Accessibility Audit Workflow
- Initialize auditor
- Run WCAG audit
- Detect violations
- Generate remediation guide
- Create GitHub issues
- Generate HTML report

**Test**: `test_full_accessibility_audit_workflow`

**Performance Target**: < 30 seconds per page

#### 2. Feedback Analysis Workflow
- Collect feedback from CSV
- Analyze sentiment
- Extract themes
- Generate insights report
- Export results

**Test**: `test_feedback_analysis_workflow`

**Performance Target**: < 5 seconds for 1000 items

#### 3. Heuristic Evaluation Workflow
- Load Nielsen's 10 heuristics
- Evaluate each heuristic
- Calculate scores
- Generate recommendations
- Export report

**Test**: `test_heuristic_evaluation_workflow`

**Performance Target**: < 2 minutes per evaluation

#### 4. Analytics Integration Workflow
- Fetch Google Analytics data
- Fetch Hotjar heatmap data
- Aggregate metrics
- Generate insights
- Export combined report

**Test**: `test_analytics_integration_workflow`

**Performance Target**: < 10 seconds per data fetch

## Performance Benchmarks

### Accessibility Auditing

| Operation | Target | Actual |
|-----------|--------|--------|
| Single page audit | < 30s | TBD |
| 10-page site audit | < 3min | TBD |
| 50-page site audit | < 10min | TBD |
| Multi-viewport audit (3) | < 2min | TBD |

### Feedback Analysis

| Operation | Target | Actual |
|-----------|--------|--------|
| 1000 items analysis | < 5s | TBD |
| Sentiment per item | < 100ms | TBD |
| Theme extraction | < 3s | TBD |
| Batch processing (10 batches) | < 5s | TBD |

### Report Generation

| Format | Target | Actual |
|--------|--------|--------|
| JSON | < 1s | TBD |
| HTML | < 2s | TBD |
| PDF | < 5s | TBD |
| Multi-format | < 10s | TBD |

## Test Fixtures

### Shared Fixtures (conftest.py)

- `temp_dir`: Temporary directory for test files
- `sample_html_with_issues`: HTML page with accessibility issues
- `sample_html_accessible`: Accessible HTML page
- `sample_feedback_csv`: Sample feedback CSV file
- `sample_feedback_json`: Sample feedback JSON data
- `mock_axe_results`: Mock axe-core audit results
- `mock_lighthouse_results`: Mock Lighthouse results
- `mock_google_analytics_data`: Mock GA API response
- `mock_hotjar_heatmap_data`: Mock Hotjar response
- `mock_sentiment_results`: Mock sentiment analysis
- `mock_heuristic_evaluation`: Mock heuristic scores
- `mock_playwright_page`: Mock Playwright page
- `mock_playwright_browser`: Mock Playwright browser
- `large_feedback_dataset`: 1000+ feedback items

### Sample Pages (fixtures/sample_pages.py)

- `CRITICAL_ISSUES_PAGE`: Page with critical accessibility issues
- `ACCESSIBLE_PAGE`: Fully accessible page
- `COMPLEX_PAGE`: Multi-section page with mixed issues
- `ARIA_ISSUES_PAGE`: Page with ARIA attribute issues
- `RESPONSIVE_PAGE`: Responsive design test page
- `FORM_PAGE`: Form accessibility test page
- `TABLE_PAGE`: Table accessibility test page

### Mock Responses (fixtures/mock_responses.py)

- `GOOGLE_ANALYTICS_RESPONSE`: Full GA API response
- `HOTJAR_HEATMAP_RESPONSE`: Heatmap data
- `SURVEY_FEEDBACK_RESPONSE`: Survey responses
- `SUPPORT_TICKETS_RESPONSE`: Support ticket data
- `SESSION_RECORDINGS_RESPONSE`: Session recording data
- `NPS_RESPONSE`: Net Promoter Score data
- `USER_JOURNEY_RESPONSE`: User journey paths
- `AB_TEST_RESPONSE`: A/B test results

## Mock Services

### Available Mocks (mocks/mock_services.py)

- `MockPlaywrightBrowser`: Mock Playwright browser
- `MockGoogleAnalyticsClient`: Mock GA API client
- `MockHotjarClient`: Mock Hotjar API client
- `MockGitHubClient`: Mock GitHub API client
- `MockAxeCoreEngine`: Mock axe-core engine
- `MockLighthouseRunner`: Mock Lighthouse runner
- `MockSentimentModel`: Mock NLP sentiment model
- `MockEmailService`: Mock email service
- `MockSlackClient`: Mock Slack notifications

## Writing New Tests

### Test Structure Template

```python
import pytest
from unittest.mock import Mock, patch


class TestNewFeature:
    """Tests for new feature."""

    def test_basic_functionality(self):
        """Test basic functionality."""
        # Arrange
        input_data = "test"

        # Act
        result = my_function(input_data)

        # Assert
        assert result is not None

    @pytest.mark.asyncio
    async def test_async_functionality(self):
        """Test async functionality."""
        result = await my_async_function()
        assert result is not None

    @pytest.mark.performance
    def test_performance(self, benchmark):
        """Test performance benchmark."""
        result = benchmark(my_function, "input")
        assert result is not None
```

### Best Practices

1. **Use descriptive test names**: Test names should clearly describe what is being tested
2. **Follow AAA pattern**: Arrange, Act, Assert
3. **One assertion per test**: Focus each test on a single behavior
4. **Use fixtures**: Leverage pytest fixtures for setup/teardown
5. **Mock external dependencies**: Use mocks for external APIs and services
6. **Test edge cases**: Include tests for error conditions and edge cases
7. **Performance targets**: Include performance expectations in test docstrings
8. **Async tests**: Use `@pytest.mark.asyncio` for async tests
9. **Parametrize tests**: Use `@pytest.mark.parametrize` for multiple test cases
10. **Clean up resources**: Ensure temporary files and resources are cleaned up

## Continuous Integration

### GitHub Actions Configuration

```yaml
name: Tests

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
        run: pytest --cov --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

## Troubleshooting

### Common Issues

#### Import Errors
```bash
# Ensure PYTHONPATH includes project root
export PYTHONPATH=/path/to/devCrew_s1:$PYTHONPATH
pytest
```

#### Async Test Failures
```bash
# Ensure pytest-asyncio is installed
pip install pytest-asyncio

# Check asyncio mode in pytest.ini
asyncio_mode = auto
```

#### Coverage Not Reaching 85%
```bash
# View detailed coverage report
pytest --cov --cov-report=html
open htmlcov/index.html

# Identify missing coverage
pytest --cov --cov-report=term-missing
```

#### Slow Tests
```bash
# Show slowest tests
pytest --durations=10

# Run only fast tests
pytest -m "not slow"

# Run in parallel
pytest -n auto
```

## Test Maintenance

### Regular Tasks

1. **Update fixtures**: Keep test data current with production data formats
2. **Review coverage**: Maintain 85%+ coverage on all modules
3. **Update mocks**: Ensure mocks match current API responses
4. **Performance baselines**: Update performance targets as needed
5. **Clean test data**: Remove obsolete test fixtures
6. **Review flaky tests**: Fix or mark tests that fail intermittently

### Test Data Management

- Store large test files in `fixtures/` directory
- Use factories for generating test data
- Keep mock responses in sync with actual API schemas
- Document test data sources and formats

## Contact

For questions or issues with the test suite:
- Open an issue on GitHub
- Review test documentation in docstrings
- Check pytest documentation: https://docs.pytest.org/
