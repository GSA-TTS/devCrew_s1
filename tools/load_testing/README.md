# Issue #37: Load Testing & Performance Benchmarking Platform

**Tool ID**: TOOL-TEST-001
**Category**: Testing & Performance
**Priority**: MEDIUM (Phase 2 - Core Capabilities)

## Overview

A comprehensive load testing and performance benchmarking platform built on k6, providing automated test execution, performance analysis, bottleneck identification, capacity planning, and detailed reporting capabilities.

## Features

### Core Capabilities

1. **k6 Test Execution** (`k6_runner.py`)
   - Execute k6 tests with configurable VU profiles (1-10,000 VUs)
   - Support for multiple test types: load, stress, spike, soak, baseline
   - Protocol support: HTTP/1.1, HTTP/2, WebSocket, gRPC
   - Threshold validation for SLAs
   - Real-time metric collection

2. **Performance Analysis** (`perf_analyzer.py`)
   - Automated metric aggregation and percentile calculation
   - Bottleneck identification (latency, errors, throughput, variability)
   - Capacity planning recommendations with safety margins
   - SLA validation against configurable thresholds
   - Baseline comparison for regression detection

3. **Report Generation** (`report_generator.py`)
   - HTML reports with embedded charts
   - Executive summaries with key findings
   - Performance metrics visualization
   - Bottleneck analysis with recommendations
   - SLA validation results

4. **CLI Interface** (`load_tester.py`)
   - Easy-to-use command-line interface
   - Test orchestration from execution to reporting
   - Multiple commands: run-test, analyze, validate-sla

## Installation

### Prerequisites

1. **k6 Installation** (required - not included)
   ```bash
   # macOS
   brew install k6

   # Linux
   sudo gpg --no-default-keyring --keyring /usr/share/keyrings/k6-archive-keyring.gpg --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys C5AD17C747E3415A3642D57D77C6C491D6AC1D69
   echo "deb [signed-by=/usr/share/keyrings/k6-archive-keyring.gpg] https://dl.k6.io/deb stable main" | sudo tee /etc/apt/sources.list.d/k6.list
   sudo apt-get update
   sudo apt-get install k6

   # Windows
   choco install k6

   # Or download from: https://k6.io/docs/get-started/installation/
   ```

2. **Python 3.10+**
   ```bash
   python --version  # Should be 3.10 or higher
   ```

### Python Dependencies

```bash
# Install all required dependencies
pip install -r requirements.txt
```

Required packages:
- `pydantic>=2.0.0` - Data validation
- `pyyaml>=6.0.1` - Configuration files
- `pandas>=2.0.0` - Data analysis
- `numpy>=1.24.0` - Numerical computing
- `matplotlib>=3.7.0` - Charts and visualization
- `jinja2>=3.1.2` - Report templating
- `structlog>=23.1.0` - Structured logging
- `click>=8.1.0` - CLI framework
- `pytest>=7.4.0` - Testing framework

See `requirements.txt` for complete list.

## Quick Start

### 1. Run a Simple Load Test

```bash
python load_tester.py run-test \
  --script sample_test.js \
  --name my-load-test \
  --vus 50 \
  --duration 2m \
  --test-type load
```

### 2. Run with SLA Validation

Create `sla_config.yaml`:
```yaml
slas:
  - name: "Response Time SLA"
    metric: "p95_response_time"
    threshold: 500
    operator: "less_than"
  - name: "Error Rate SLA"
    metric: "error_rate"
    threshold: 1.0
    operator: "less_than"

latency_threshold_ms: 500
error_rate_threshold: 1.0
target_latency_ms: 400
target_error_rate: 0.5
```

Run with SLA validation:
```bash
python load_tester.py run-test \
  --script sample_test.js \
  --name sla-test \
  --vus 100 \
  --duration 5m \
  --sla-config sla_config.yaml
```

### 3. Analyze Existing Results

```bash
python load_tester.py analyze \
  --results ./load_test_results/my-load-test_raw.json \
  --output ./reports/analysis.html \
  --test-duration 120
```

### 4. Validate SLA Compliance

```bash
python load_tester.py validate-sla \
  --results ./load_test_results/my-load-test_analysis.json \
  --sla-config sla_config.yaml
```

## Usage Guide

### Test Types

The platform supports different test patterns:

#### Load Test
Sustained load over time to validate system performance under expected traffic.
```bash
--test-type load --vus 50 --duration 5m
```

#### Stress Test
Gradually increase load to find system limits.
```javascript
// In k6 script
export const options = {
    stages: [
        { duration: '2m', target: 50 },
        { duration: '5m', target: 100 },
        { duration: '5m', target: 200 },
        { duration: '2m', target: 0 },
    ],
};
```

#### Spike Test
Sudden traffic spike to test system resilience.
```javascript
export const options = {
    stages: [
        { duration: '30s', target: 10 },
        { duration: '10s', target: 500 },  // Sudden spike
        { duration: '1m', target: 500 },
        { duration: '30s', target: 0 },
    ],
};
```

#### Soak Test
Extended duration test to identify memory leaks and stability issues.
```bash
--test-type soak --vus 50 --duration 4h
```

### Creating k6 Test Scripts

Example k6 test script:
```javascript
import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
    vus: 10,
    duration: '30s',
    thresholds: {
        'http_req_duration': ['p(95)<500'],
        'http_req_failed': ['rate<0.01'],
    },
};

export default function () {
    const res = http.get('https://api.example.com/endpoint');

    check(res, {
        'status is 200': (r) => r.status === 200,
        'response time < 500ms': (r) => r.timings.duration < 500,
    });

    sleep(1);
}
```

See `sample_test.js` for a comprehensive example.

### Python API Usage

```python
from pathlib import Path
from load_tester import LoadTestOrchestrator
from k6_runner import K6Options
from perf_analyzer import TestType

# Initialize orchestrator
orchestrator = LoadTestOrchestrator(
    output_dir=Path("./results"),
    k6_binary="k6"
)

# Configure test options
options = K6Options(
    vus=100,
    duration="5m",
    thresholds={
        "http_req_duration": ["p(95)<500", "p(99)<1000"],
        "http_req_failed": ["rate<0.01"],
    }
)

# Define SLA configuration
sla_config = {
    "slas": [
        {
            "name": "Response Time",
            "metric": "p95_response_time",
            "threshold": 500,
            "operator": "less_than"
        }
    ],
    "latency_threshold_ms": 500,
    "error_rate_threshold": 1.0
}

# Run load test
results = orchestrator.run_load_test(
    script=Path("test.js"),
    test_name="api-load-test",
    options=options,
    test_type=TestType.LOAD,
    sla_config=sla_config,
    generate_report=True
)

# Access results
print(f"Test Success: {results['success']}")
print(f"Report: {results['files']['report']}")
print(f"Bottlenecks: {len(results['bottlenecks'])}")
```

## Understanding Results

### Performance Metrics

- **Average Response Time**: Mean response time across all requests
- **P50/P90/P95/P99**: Percentile response times
  - P95 < 500ms means 95% of requests completed under 500ms
- **Throughput (RPS)**: Requests per second
- **Error Rate**: Percentage of failed requests
- **Total Requests**: Total number of requests executed

### Bottleneck Types

1. **HIGH_LATENCY**: Response times exceed thresholds
   - Severity: Based on how much threshold is exceeded
   - Recommendations: Database optimization, caching, scaling

2. **HIGH_ERROR_RATE**: Excessive failures
   - Severity: Based on error rate percentage
   - Recommendations: Resource limits, error handling, stability

3. **THROUGHPUT_LIMIT**: Unable to achieve expected RPS
   - Severity: Based on throughput deficit
   - Recommendations: Horizontal scaling, request optimization

4. **IO_BOUND**: High response time variability
   - Severity: Based on coefficient of variation
   - Recommendations: Network stability, resource contention

### Capacity Planning

The analyzer provides:
- **Max Sustainable Load**: Estimated maximum VUs system can handle
- **Recommended Max Load**: Safe maximum with safety margin (default 20%)
- **Limiting Factor**: Primary constraint (latency, errors, throughput)
- **Confidence Level**: Reliability of recommendation
- **Notes**: Specific recommendations and observations

## Output Files

After running a test, you'll find:

```
load_test_results/
├── my-load-test_raw.json          # Raw k6 metrics
├── my-load-test_analysis.json     # Analyzed metrics with insights
└── my-load-test_report.html       # HTML report with charts
```

## Testing

Run the comprehensive test suite:

```bash
# Run all tests
pytest test_load_tester.py -v

# Run with coverage
pytest test_load_tester.py -v --cov=. --cov-report=html

# Run specific test class
pytest test_load_tester.py::TestK6Runner -v

# Run specific test
pytest test_load_tester.py::TestPerformanceAnalyzer::test_identify_bottlenecks_high_latency -v
```

Test coverage includes:
- K6Runner execution and command building
- Performance metric aggregation and analysis
- Bottleneck identification algorithms
- Capacity recommendation logic
- Report generation and formatting
- Full integration workflow

## Performance Requirements

The platform is designed to meet these requirements:

- **VU Capacity**: Support 10,000+ concurrent virtual users
- **Framework Overhead**: <1% overhead during test execution
- **Report Generation**: <30 seconds for typical test results
- **Metric Accuracy**: ±2% accuracy for percentile calculations
- **Distributed Execution**: Support for multi-node k6 clusters

## Protocol Coverage

This tool supports **18 protocols** (22% of devCrew_s1 protocols):

- P-ARCH-FITNESS (Architecture Fitness Function)
- P-ARCH-INTEGRATION (Architecture Integration)
- P-CFR-INTEGRATION (Cross-Functional Requirements Integration)
- P-API-CONTRACT-VALIDATION (API Contract Validation)
- P-FRONTEND-DEV (Frontend Development)
- P-CAPACITY-PLANNING (Capacity Planning)
- P-PERFORMANCE-OPTIMIZATION (Performance Optimization)
- P-SLA-VALIDATION (SLA Validation)
- QG-PERFORMANCE (Performance Quality Gate)
- QG-SCALABILITY (Scalability Quality Gate)
- And 8 more protocols

## Troubleshooting

### k6 Not Found

```bash
# Verify k6 is installed
k6 version

# If not found, install k6
# See Installation section above
```

### Import Errors

```bash
# Ensure all dependencies are installed
pip install -r requirements.txt

# Verify Python version
python --version  # Must be 3.10+
```

### Test Execution Fails

Check the error message in the output:
- **Connection refused**: Target URL is not accessible
- **Timeout**: Test duration too short or system unresponsive
- **Permission denied**: Check file permissions for output directory

### Empty Metrics

- Ensure k6 script runs successfully: `k6 run sample_test.js`
- Check output file is created and not empty
- Verify JSON format in output file

## Best Practices

### Test Design

1. **Start Small**: Begin with low VU count (10-50) to validate test
2. **Ramp Gradually**: Use stages to gradually increase load
3. **Set Realistic Thresholds**: Base on production SLAs
4. **Add Think Time**: Use `sleep()` to simulate user behavior
5. **Monitor System**: Watch CPU, memory, connections during test

### Performance Optimization

1. **Baseline First**: Establish baseline before making changes
2. **Isolate Changes**: Test one optimization at a time
3. **Compare Results**: Use baseline comparison feature
4. **Focus on P95/P99**: These matter more than averages
5. **Investigate Outliers**: High max values indicate issues

### SLA Definition

```yaml
slas:
  # Critical path endpoints
  - name: "Homepage Load Time"
    metric: "p95_response_time"
    threshold: 300
    operator: "less_than"

  # API endpoints
  - name: "API Response Time"
    metric: "p99_response_time"
    threshold: 1000
    operator: "less_than"

  # Error budget
  - name: "Error Rate"
    metric: "error_rate"
    threshold: 0.1  # 0.1% = 99.9% success rate
    operator: "less_than"
```

## Advanced Features

### Environment Variables in k6 Scripts

```javascript
const BASE_URL = __ENV.BASE_URL || 'https://default.example.com';
const API_KEY = __ENV.API_KEY;
```

Run with environment variables:
```bash
K6_OPTIONS="--env BASE_URL=https://staging.example.com" \
python load_tester.py run-test --script test.js --name env-test
```

### Custom Metrics Export

k6 supports exporting to:
- InfluxDB
- Prometheus
- Grafana Cloud
- JSON file (default)

Configure in k6 script or command line.

### Distributed Execution

For >10k VUs, use k6 cloud or distributed execution:
```bash
# Split load across multiple machines
k6 run --vus 5000 test.js &  # Machine 1
k6 run --vus 5000 test.js &  # Machine 2
```

## Contributing

This implementation is part of Issue #37, located in `tools/load_testing/`.

To contribute:
1. Review the code in the `*.py` files
2. Run tests: `pytest test_load_tester.py -v`
3. Follow Python best practices from global CLAUDE.md
4. Ensure code quality with Black, isort, flake8, mypy

## References

- **k6 Documentation**: https://k6.io/docs/
- **Issue #37**: https://github.com/GSA-TTS/devCrew_s1/issues/37
- **Tool Specification**: devCrew/tools/TOOL-TEST-001_Load-Testing.md

## License

Part of the devCrew_s1 project.

## Support

For questions or issues:
1. Check this README
2. Review test cases in `test_load_tester.py`
3. Check k6 documentation: https://k6.io/docs/
4. Review Issue #37 on GitHub

---

**Status**: Implementation Complete
**Version**: 1.0.0
**Last Updated**: 2025-11-20
