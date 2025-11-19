# **Tool Name**: Application Performance Monitoring (APM) Platform

**Tool ID**: `TOOL-MON-001`
**Version**: 1.0.0
**Status**: Active
**Owner**: SRE, DevOps Engineer, Performance Engineer
**Priority**: High (Used in 28/83 protocols - 34%)

---

## **Part I: Tool Identity & Purpose**

### Tool Category
Monitoring & Observability

### Tool Capability
Enables real-time application performance monitoring, health checks, metrics collection, alerting, and SLO tracking across distributed systems. Provides comprehensive visibility into system behavior, performance trends, and anomaly detection with proactive alerting capabilities.

### Use Cases
- **Use Case 1**: Health Monitoring - Continuous service health checks with automatic failover triggers and degradation detection across microservices
- **Use Case 2**: Performance Tracking - Monitor API endpoint latency (P50/P95/P99), throughput, and error rates with automatic SLA violation alerting
- **Use Case 3**: SLO Validation - Track service level objectives for availability (99.9%), latency (<500ms), and error budget consumption with burn rate alerts
- **Use Case 4**: Incident Alerting - Real-time alerts on anomalies, threshold breaches, and cascading failures with multi-channel notifications
- **Use Case 5**: Capacity Planning - Analyze resource utilization trends, predict saturation points, and optimize infrastructure costs based on actual usage patterns

### Strategic Value
- **Business Value**: Reduces MTTR from hours to minutes, prevents revenue loss from performance issues, enables proactive capacity planning reducing costs by 20-30%, maintains customer trust through reliability
- **Technical Value**: Provides end-to-end system visibility, enables data-driven optimization, supports deployment validation, facilitates root cause analysis, enables continuous improvement through metrics
- **Risk Mitigation**: Detects issues before customer impact, prevents cascading failures, validates SLA compliance, provides audit trail for incidents, enables predictive maintenance

---

## **Part II: Functional Requirements**

### Core Capabilities

1. **Health Checks**:
   - **Requirement**: Execute periodic health checks for services, databases, APIs, and infrastructure components with configurable intervals
   - **Acceptance Criteria**: Support HTTP/TCP/gRPC health checks, <100ms check execution, automatic retry logic, dependency health tracking, graceful degradation detection

2. **Metrics Collection**:
   - **Requirement**: Collect, aggregate, and store time-series metrics from applications, infrastructure, and custom sources
   - **Acceptance Criteria**: Prometheus exposition format support, 1-second granularity, support for counters/gauges/histograms/summaries, automatic service discovery, <1% CPU overhead

3. **Alerting**:
   - **Requirement**: Define alert rules with threshold-based, rate-based, and anomaly detection conditions with multi-channel notifications
   - **Acceptance Criteria**: Evaluate alerts within 60 seconds, support alert routing and escalation, deduplicate similar alerts, integrate with Slack/PagerDuty/email, provide alert history

4. **Performance Tracking**:
   - **Requirement**: Track application performance metrics including latency, throughput, error rates, and resource utilization over time
   - **Acceptance Criteria**: Calculate percentiles (P50/P90/P95/P99) accurately, support custom business metrics, aggregate across service instances, retain data for 90 days minimum

5. **SLO Monitoring**:
   - **Requirement**: Track Service Level Objectives (availability, latency, error rate) with error budget calculation and burn rate alerting
   - **Acceptance Criteria**: Support multi-window SLOs (1h/6h/24h/30d), calculate error budget consumption, alert on burn rate thresholds, generate compliance reports

### Input/Output Specifications

#### Input Requirements
- **Input Format**: Prometheus metrics (exposition format), OpenTelemetry metrics, StatsD, custom exporters, health check endpoints
- **Input Parameters**: Service name, environment tags, metric labels, scrape intervals, health check URLs, alert rule definitions
- **Input Constraints**: Maximum 10,000 unique time series per service, metric names follow naming conventions, label cardinality <100 per metric

#### Output Requirements
- **Output Format**: PromQL query results (JSON), Grafana dashboards, alert notifications (JSON/webhook), CSV reports
- **Output Schema**: Time-series data with timestamps and labels, alert events with severity/description/context, health status with uptime percentages
- **Output Artifacts**: Daily performance reports, SLO compliance reports, incident timelines, capacity planning recommendations

### Performance Requirements
- **Throughput**: Ingest 100,000 metrics per second, handle 10,000+ active time series, support 1,000+ concurrent queries
- **Latency**: Query response <1 second for 24-hour range, alert evaluation <60 seconds, dashboard refresh <5 seconds
- **Scalability**: Support 1,000+ services, 10,000+ hosts, horizontal scaling for high-availability setups
- **Reliability**: 99.9% platform uptime, automatic failover, data retention policies, backup and recovery

### Integration Requirements
- **API Integration**: Prometheus HTTP API, Grafana REST API, webhook endpoints for alerts, exporters for various services
- **Authentication**: Basic auth, bearer tokens, OAuth2 for Grafana, API keys for external integrations
- **Data Exchange**: Prometheus remote write protocol, JSON over HTTP, webhook payloads
- **Event Handling**: Alert manager for routing, silencing, and grouping alerts; notification channels for incident response

---

## **Part III: Non-Functional Requirements**

### Security Requirements
- **Authentication & Authorization**: Basic authentication, bearer token authentication, role-based access control (RBAC) in Grafana
- **Data Encryption**: TLS 1.3 for data in transit, encrypted storage for sensitive metrics, secure credential management
- **Secret Management**: Store credentials in environment variables or secrets management systems (Vault, AWS Secrets Manager)
- **Audit Logging**: Log configuration changes, alert rule modifications, dashboard access, query execution
- **Compliance**: Support data retention policies, GDPR-compliant data handling, audit trails for compliance reporting

### Operational Requirements
- **Deployment Models**: Self-hosted (Docker, Kubernetes), cloud solutions (Datadog, New Relic), hybrid deployments
- **Platform Support**: Linux (primary), macOS, Windows (via exporters), containerized environments (Docker/Kubernetes)
- **Resource Requirements**: Prometheus: 2-4 GB RAM, 50-100 GB storage per million samples; Grafana: 512 MB RAM, minimal storage
- **Backup & Recovery**: Automated snapshots of Prometheus data, Grafana dashboard backup, configuration version control

### Observability Requirements
- **Logging**: Structured logs for Prometheus/Grafana, error logs for failed scrapes, query logs for performance analysis
- **Metrics**: Platform health metrics (ingestion rate, query latency, storage usage), self-monitoring dashboards
- **Tracing**: Not typically applicable for metrics platforms, but integration with distributed tracing systems
- **Alerting**: Meta-alerts for platform health (scrape failures, disk space, high query latency)

### Governance Requirements
- **Licensing**: Open source (Prometheus/Grafana - Apache 2.0/AGPL), commercial cloud solutions (per-host or per-metric pricing)
- **Vendor Lock-in**: Prometheus format is industry standard, exportable data, standardized PromQL query language
- **Support**: Community support for OSS, commercial support available from Grafana Labs, cloud provider support for managed services
- **Deprecation Policy**: Follow Prometheus/Grafana versioning and LTS releases, 12-month deprecation notice for major changes

---

## **Part IV: Integration Patterns**

### CLI Integration
**CLI Available**: Yes (Prometheus CLI, Grafana CLI, promtool)

**Command Structure**:
```bash
# Prometheus queries via promtool
promtool query instant http://localhost:9090 'up'
promtool query range http://localhost:9090 \
  'rate(http_requests_total[5m])' \
  --start="2025-01-01T00:00:00Z" \
  --end="2025-01-01T12:00:00Z"

# Validate Prometheus configuration
promtool check config prometheus.yml
promtool check rules alerts.yml

# Grafana CLI for dashboard management
grafana-cli plugins install grafana-piechart-panel
grafana-cli admin reset-admin-password newpassword

# Query Prometheus via curl
curl 'http://localhost:9090/api/v1/query?query=up'
curl 'http://localhost:9090/api/v1/query_range?query=rate(http_requests_total[5m])&start=1609459200&end=1609545600&step=300'

# Alert testing
promtool test rules alerts.yml
amtool alert query --alertmanager.url=http://localhost:9093
```

**Common Operations**:
```bash
# Health check
curl http://localhost:9090/-/healthy

# Query instant metrics
promtool query instant http://localhost:9090 \
  'rate(http_requests_total{job="api-server"}[5m])'

# Validate alert rules
promtool check rules /etc/prometheus/alerts/*.yml

# Reload Prometheus configuration
curl -X POST http://localhost:9090/-/reload

# Check targets
curl http://localhost:9090/api/v1/targets | jq '.data.activeTargets[] | {job: .labels.job, health: .health}'
```

### Python API Integration
**Python Library**: `prometheus-client`, `requests` for API calls

**Installation**:
```bash
pip install prometheus-client requests
```

**Example Code**:

```python
from prometheus_client import Counter, Histogram, Gauge, start_http_server
import time
import requests

# Define metrics
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

REQUEST_LATENCY = Histogram(
    'http_request_duration_seconds',
    'HTTP request latency',
    ['method', 'endpoint']
)

ACTIVE_CONNECTIONS = Gauge(
    'active_connections',
    'Number of active connections'
)

# Instrument application code
def handle_request(method, endpoint):
    REQUEST_COUNT.labels(method=method, endpoint=endpoint, status='200').inc()

    with REQUEST_LATENCY.labels(method=method, endpoint=endpoint).time():
        # Simulate request processing
        time.sleep(0.1)

    ACTIVE_CONNECTIONS.inc()
    # Process request
    ACTIVE_CONNECTIONS.dec()

# Start metrics server
if __name__ == '__main__':
    start_http_server(8000)  # Expose metrics on :8000/metrics
    while True:
        handle_request('GET', '/api/users')
        time.sleep(1)
```

**Querying Prometheus via Python**:
```python
import requests
from datetime import datetime, timedelta

class PrometheusClient:
    def __init__(self, base_url='http://localhost:9090'):
        self.base_url = base_url

    def query_instant(self, query, time_param=None):
        """Execute instant query"""
        url = f"{self.base_url}/api/v1/query"
        params = {'query': query}
        if time_param:
            params['time'] = time_param

        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()['data']['result']

    def query_range(self, query, start, end, step='15s'):
        """Execute range query"""
        url = f"{self.base_url}/api/v1/query_range"
        params = {
            'query': query,
            'start': start.timestamp(),
            'end': end.timestamp(),
            'step': step
        }

        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()['data']['result']

    def get_targets(self):
        """Get scrape targets status"""
        url = f"{self.base_url}/api/v1/targets"
        response = requests.get(url)
        response.raise_for_status()
        return response.json()['data']['activeTargets']

    def check_health(self):
        """Check Prometheus health"""
        url = f"{self.base_url}/-/healthy"
        response = requests.get(url)
        return response.status_code == 200

# Example usage
client = PrometheusClient()

# Check service health
results = client.query_instant('up{job="api-server"}')
for result in results:
    print(f"Service: {result['metric']}, Status: {result['value'][1]}")

# Get request rate over last hour
end = datetime.now()
start = end - timedelta(hours=1)
results = client.query_range(
    'rate(http_requests_total[5m])',
    start, end, step='1m'
)

# Calculate SLO compliance
slo_query = '''
(
  sum(rate(http_requests_total{status=~"2.."}[30d]))
  /
  sum(rate(http_requests_total[30d]))
) * 100
'''
slo_result = client.query_instant(slo_query)
availability = float(slo_result[0]['value'][1])
print(f"30-day availability: {availability:.3f}%")
```

### Alert Rule Examples
**Alert Rules Configuration** (`alerts.yml`):
```yaml
groups:
  - name: api_alerts
    interval: 30s
    rules:
      # High error rate alert
      - alert: HighErrorRate
        expr: |
          (
            sum(rate(http_requests_total{status=~"5.."}[5m])) by (job)
            /
            sum(rate(http_requests_total[5m])) by (job)
          ) > 0.05
        for: 5m
        labels:
          severity: critical
          team: backend
        annotations:
          summary: "High error rate on {{ $labels.job }}"
          description: "Error rate is {{ $value | humanizePercentage }} (threshold: 5%)"

      # Service down alert
      - alert: ServiceDown
        expr: up{job="api-server"} == 0
        for: 2m
        labels:
          severity: critical
          team: sre
        annotations:
          summary: "Service {{ $labels.instance }} is down"
          description: "{{ $labels.job }} on {{ $labels.instance }} has been down for more than 2 minutes"

      # High latency alert
      - alert: HighLatency
        expr: |
          histogram_quantile(0.95,
            sum(rate(http_request_duration_seconds_bucket[5m])) by (le, endpoint)
          ) > 0.5
        for: 10m
        labels:
          severity: warning
          team: backend
        annotations:
          summary: "High latency on {{ $labels.endpoint }}"
          description: "P95 latency is {{ $value }}s (threshold: 0.5s)"

      # SLO burn rate alert
      - alert: ErrorBudgetBurnRateTooFast
        expr: |
          (
            1 - (
              sum(rate(http_requests_total{status=~"2.."}[1h]))
              /
              sum(rate(http_requests_total[1h]))
            )
          ) > 0.001 * 14.4  # 14.4x burn rate
        for: 5m
        labels:
          severity: critical
          team: sre
        annotations:
          summary: "Error budget burning too fast"
          description: "At current rate, 30-day error budget will be exhausted in {{ $value }} hours"

      # High memory usage
      - alert: HighMemoryUsage
        expr: |
          (
            node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes
          ) / node_memory_MemTotal_bytes > 0.9
        for: 5m
        labels:
          severity: warning
          team: infrastructure
        annotations:
          summary: "High memory usage on {{ $labels.instance }}"
          description: "Memory usage is {{ $value | humanizePercentage }} (threshold: 90%)"
```

### Error Handling

**Common Error Scenarios**:

1. **Missing Metrics**:
```python
def safe_query(client, query, default=None):
    """Query with fallback for missing metrics"""
    try:
        results = client.query_instant(query)
        if not results:
            print(f"No data found for query: {query}")
            return default
        return results
    except requests.exceptions.HTTPError as e:
        print(f"Query failed: {e}")
        return default
```

2. **Scrape Failures**:
```yaml
# Alert on failed scrapes
- alert: ScrapeFailed
  expr: up == 0
  for: 5m
  labels:
    severity: warning
  annotations:
    summary: "Scrape failed for {{ $labels.job }}"
    description: "Target {{ $labels.instance }} has been down for 5 minutes"
```

3. **Data Retention**:
```yaml
# Prometheus configuration for retention
global:
  scrape_interval: 15s
  evaluation_interval: 15s

storage:
  tsdb:
    retention.time: 90d
    retention.size: 100GB
```

4. **Alert Fatigue**:
```yaml
# Group similar alerts
route:
  group_by: ['alertname', 'cluster', 'service']
  group_wait: 30s
  group_interval: 5m
  repeat_interval: 12h

  routes:
    - match:
        severity: critical
      receiver: pagerduty
      continue: true

    - match:
        severity: warning
      receiver: slack
```

---

## **Part V: Implementation Plan**

### Prerequisites
- Docker and Docker Compose installed (or Kubernetes cluster)
- Network access for scraping targets
- Storage for time-series data (50-100 GB recommended)
- Understanding of PromQL query language
- Access to services to be monitored

### Installation

**Option 1: Docker Compose (Recommended for local/development)**:

Create `docker-compose.yml`:
```yaml
version: '3.8'

services:
  prometheus:
    image: prom/prometheus:latest
    container_name: prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - ./alerts.yml:/etc/prometheus/alerts.yml
      - prometheus-data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--storage.tsdb.retention.time=90d'
      - '--web.enable-lifecycle'
    restart: unless-stopped

  grafana:
    image: grafana/grafana:latest
    container_name: grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_USER=admin
      - GF_SECURITY_ADMIN_PASSWORD=admin
      - GF_USERS_ALLOW_SIGN_UP=false
    volumes:
      - grafana-data:/var/lib/grafana
      - ./grafana/provisioning:/etc/grafana/provisioning
    restart: unless-stopped

  alertmanager:
    image: prom/alertmanager:latest
    container_name: alertmanager
    ports:
      - "9093:9093"
    volumes:
      - ./alertmanager.yml:/etc/alertmanager/alertmanager.yml
      - alertmanager-data:/alertmanager
    command:
      - '--config.file=/etc/alertmanager/alertmanager.yml'
      - '--storage.path=/alertmanager'
    restart: unless-stopped

  node-exporter:
    image: prom/node-exporter:latest
    container_name: node-exporter
    ports:
      - "9100:9100"
    command:
      - '--path.procfs=/host/proc'
      - '--path.sysfs=/host/sys'
      - '--collector.filesystem.mount-points-exclude=^/(sys|proc|dev|host|etc)($$|/)'
    volumes:
      - /proc:/host/proc:ro
      - /sys:/host/sys:ro
      - /:/rootfs:ro
    restart: unless-stopped

volumes:
  prometheus-data:
  grafana-data:
  alertmanager-data:
```

**Option 2: Cloud Solutions**:
- **Datadog**: Sign up at datadog.com, install agent, configure integrations
- **New Relic**: Sign up at newrelic.com, install agent, instrument applications
- **AWS CloudWatch**: Native AWS service, configure metrics and alarms

### Configuration

**Prometheus Configuration** (`prometheus.yml`):
```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s
  external_labels:
    cluster: 'production'
    environment: 'prod'

# Alertmanager configuration
alerting:
  alertmanagers:
    - static_configs:
        - targets:
            - alertmanager:9093

# Load alert rules
rule_files:
  - 'alerts.yml'

# Scrape configurations
scrape_configs:
  # Prometheus self-monitoring
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  # Node exporter for infrastructure metrics
  - job_name: 'node'
    static_configs:
      - targets: ['node-exporter:9100']

  # Application metrics
  - job_name: 'api-server'
    static_configs:
      - targets: ['api-server:8000']
    metric_relabel_configs:
      - source_labels: [__name__]
        regex: 'go_.*'
        action: drop  # Drop Go runtime metrics

  # Service discovery (Kubernetes example)
  - job_name: 'kubernetes-pods'
    kubernetes_sd_configs:
      - role: pod
    relabel_configs:
      - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_scrape]
        action: keep
        regex: true
      - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_path]
        action: replace
        target_label: __metrics_path__
        regex: (.+)
      - source_labels: [__address__, __meta_kubernetes_pod_annotation_prometheus_io_port]
        action: replace
        regex: ([^:]+)(?::\d+)?;(\d+)
        replacement: $1:$2
        target_label: __address__
```

**Alertmanager Configuration** (`alertmanager.yml`):
```yaml
global:
  resolve_timeout: 5m
  slack_api_url: 'https://hooks.slack.com/services/YOUR/WEBHOOK/URL'

route:
  group_by: ['alertname', 'cluster', 'service']
  group_wait: 30s
  group_interval: 5m
  repeat_interval: 12h
  receiver: 'default'

  routes:
    - match:
        severity: critical
      receiver: pagerduty
      continue: true

    - match:
        severity: warning
      receiver: slack

receivers:
  - name: 'default'
    email_configs:
      - to: 'team@example.com'
        from: 'alertmanager@example.com'
        smarthost: 'smtp.gmail.com:587'
        auth_username: 'alertmanager@example.com'
        auth_password: 'password'

  - name: 'slack'
    slack_configs:
      - channel: '#alerts'
        title: 'Alert: {{ .GroupLabels.alertname }}'
        text: '{{ range .Alerts }}{{ .Annotations.description }}{{ end }}'

  - name: 'pagerduty'
    pagerduty_configs:
      - service_key: 'YOUR_PAGERDUTY_SERVICE_KEY'

inhibit_rules:
  - source_match:
      severity: 'critical'
    target_match:
      severity: 'warning'
    equal: ['alertname', 'cluster', 'service']
```

### Testing

**Metric Validation**:
```bash
# Start the stack
docker-compose up -d

# Wait for services to start
sleep 30

# Check Prometheus targets
curl http://localhost:9090/api/v1/targets | jq '.data.activeTargets[] | {job: .labels.job, health: .health}'

# Validate metrics are being collected
curl 'http://localhost:9090/api/v1/query?query=up' | jq '.data.result'

# Test alert rules
promtool check rules alerts.yml

# Trigger test alert
curl -X POST http://localhost:9093/api/v1/alerts \
  -H 'Content-Type: application/json' \
  -d '[{"labels":{"alertname":"TestAlert","severity":"critical"},"annotations":{"summary":"Test alert"}}]'

# Check alert status
curl http://localhost:9093/api/v1/alerts | jq '.data[] | {name: .labels.alertname, state: .status.state}'
```

**Load Testing**:
```python
# Generate test metrics
from prometheus_client import Counter, start_http_server
import time
import random

test_counter = Counter('test_requests_total', 'Test requests', ['status'])

start_http_server(8001)

for i in range(1000):
    status = '200' if random.random() > 0.1 else '500'
    test_counter.labels(status=status).inc()
    time.sleep(0.1)
```

### Documentation

**Creating Dashboards in Grafana**:
1. Access Grafana at http://localhost:3000 (admin/admin)
2. Add Prometheus data source (URL: http://prometheus:9090)
3. Create dashboard with panels:
   - Request rate: `rate(http_requests_total[5m])`
   - Error rate: `rate(http_requests_total{status=~"5.."}[5m])`
   - Latency (P95): `histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))`
   - Service uptime: `avg_over_time(up[24h])`

**Alert Rule Best Practices**:
- Use `for` clause to avoid flapping alerts (e.g., `for: 5m`)
- Include meaningful annotations with context
- Set appropriate severity levels
- Group related alerts
- Use inhibit rules to reduce noise
- Test alerts before deploying to production

---

## **Part VI: Protocol Integrations**

### Key Protocol Integrations (10 of 28)

1. **P-HEALTH-CHECK** - Service Health Monitoring
   - **Integration Point**: Periodic health checks with automatic alerting
   - **Workflow**: Schedule health checks → Execute probes → Collect metrics → Evaluate thresholds → Trigger alerts on failures
   - **Metrics**: `up{job="service"}`, `probe_success`, `probe_duration_seconds`

2. **P-DEPLOY-VALIDATION** - Deployment Verification
   - **Integration Point**: Post-deployment health and performance validation
   - **Workflow**: Deploy service → Wait for stabilization → Compare metrics against baseline → Alert on regressions → Rollback if critical failures
   - **Metrics**: Error rate comparison, latency percentile changes, resource usage

3. **P-SLO-TRACKING** - Service Level Objective Monitoring
   - **Integration Point**: Continuous SLO compliance tracking and error budget management
   - **Workflow**: Define SLOs → Calculate error budget → Monitor burn rate → Alert on budget exhaustion → Generate compliance reports
   - **SLO Calculation**: `(good_requests / total_requests) * 100 >= 99.9%`

4. **P-INCIDENT-RESPONSE** - Automated Incident Detection
   - **Integration Point**: Real-time anomaly detection and incident alerting
   - **Workflow**: Monitor metrics → Detect anomalies → Create incident → Notify on-call → Track resolution → Post-mortem analysis
   - **Integration**: AlertManager → PagerDuty/Slack → Incident management system

5. **P-CAPACITY-PLANNING** - Resource Utilization Analysis
   - **Integration Point**: Trend analysis and capacity forecasting
   - **Workflow**: Collect resource metrics → Analyze growth trends → Predict saturation → Recommend scaling actions
   - **Metrics**: CPU/memory utilization, disk space, network bandwidth, request volume trends

6. **P-PERFORMANCE-TESTING** - Load Test Validation
   - **Integration Point**: Metrics collection during performance tests
   - **Workflow**: Start load test → Monitor real-time metrics → Compare against SLOs → Generate performance report
   - **Validation**: Latency under load, throughput limits, error rate stability

7. **P-SECURITY-MONITORING** - Security Metrics Tracking
   - **Integration Point**: Monitor security-related metrics and anomalies
   - **Workflow**: Track authentication failures, rate limiting, suspicious patterns → Alert on threshold breaches
   - **Metrics**: `auth_failures_total`, `rate_limit_exceeded_total`, `suspicious_activity_count`

8. **P-COST-OPTIMIZATION** - Resource Cost Tracking
   - **Integration Point**: Monitor resource usage for cost optimization
   - **Workflow**: Collect resource metrics → Calculate cost attribution → Identify optimization opportunities
   - **Analysis**: Idle resources, oversized instances, unused capacity

9. **P-DEPENDENCY-HEALTH** - Third-Party Service Monitoring
   - **Integration Point**: Monitor external dependencies and APIs
   - **Workflow**: Health check external services → Track latency and error rates → Alert on degradation
   - **Metrics**: External API response times, error rates, timeout counts

10. **P-ROLLBACK-TRIGGER** - Automated Rollback Detection
    - **Integration Point**: Detect deployment issues for automatic rollback
    - **Workflow**: Monitor post-deployment metrics → Compare against thresholds → Trigger rollback on critical failures
    - **Conditions**: Error rate spike, latency degradation, availability drop

### Health Check Workflows

**Basic Health Check Pattern**:
```yaml
# Prometheus scrape config for health checks
scrape_configs:
  - job_name: 'blackbox'
    metrics_path: /probe
    params:
      module: [http_2xx]
    static_configs:
      - targets:
          - https://api.example.com/health
          - https://db.example.com:5432
    relabel_configs:
      - source_labels: [__address__]
        target_label: __param_target
      - source_labels: [__param_target]
        target_label: instance
      - target_label: __address__
        replacement: blackbox-exporter:9115
```

**Health Check Alert**:
```yaml
- alert: ServiceHealthCheckFailed
  expr: probe_success == 0
  for: 2m
  labels:
    severity: critical
  annotations:
    summary: "Health check failed for {{ $labels.instance }}"
    description: "Service has been unhealthy for 2 minutes"
```

### SLO Validation Patterns

**SLO Definition Example** (99.9% availability, <500ms latency):
```yaml
# Availability SLO
- record: slo:availability:ratio_30d
  expr: |
    sum(rate(http_requests_total{status=~"2.."}[30d]))
    /
    sum(rate(http_requests_total[30d]))

# Latency SLO (P95 < 500ms)
- record: slo:latency:p95_30d
  expr: |
    histogram_quantile(0.95,
      sum(rate(http_request_duration_seconds_bucket[30d])) by (le)
    )

# Error budget calculation
- record: slo:error_budget:remaining_30d
  expr: |
    1 - (
      (1 - slo:availability:ratio_30d) / (1 - 0.999)
    )

# Burn rate alert (fast burn: 1h window)
- alert: ErrorBudgetFastBurn
  expr: |
    (
      1 - slo:availability:ratio_30d
    ) > 0.001 * 14.4  # 14.4x burn rate
  for: 5m
  labels:
    severity: critical
  annotations:
    summary: "Error budget burning too fast"
    description: "At current rate, monthly budget exhausted in {{ $value | humanizeDuration }}"
```

**SLO Dashboard Queries**:
- Current availability: `slo:availability:ratio_30d * 100`
- Error budget remaining: `slo:error_budget:remaining_30d * 100`
- Current latency P95: `slo:latency:p95_30d * 1000` (in ms)
- Error budget burn rate: `(1 - slo:availability:ratio_30d) / 0.001`

### Integration with CI/CD

**Deployment Validation**:
```bash
#!/bin/bash
# validate_deployment.sh

SERVICE_NAME="api-server"
PROMETHEUS_URL="http://prometheus:9090"
THRESHOLD_ERROR_RATE=0.05
THRESHOLD_LATENCY_P95=0.5

# Wait for deployment to stabilize
sleep 60

# Check error rate
ERROR_RATE=$(curl -s "${PROMETHEUS_URL}/api/v1/query?query=rate(http_requests_total{job=\"${SERVICE_NAME}\",status=~\"5..\"}[5m])/rate(http_requests_total{job=\"${SERVICE_NAME}\"}[5m])" | jq -r '.data.result[0].value[1]')

if (( $(echo "$ERROR_RATE > $THRESHOLD_ERROR_RATE" | bc -l) )); then
    echo "ERROR: Error rate ${ERROR_RATE} exceeds threshold ${THRESHOLD_ERROR_RATE}"
    exit 1
fi

# Check latency
LATENCY_P95=$(curl -s "${PROMETHEUS_URL}/api/v1/query?query=histogram_quantile(0.95,rate(http_request_duration_seconds_bucket{job=\"${SERVICE_NAME}\"}[5m]))" | jq -r '.data.result[0].value[1]')

if (( $(echo "$LATENCY_P95 > $THRESHOLD_LATENCY_P95" | bc -l) )); then
    echo "ERROR: P95 latency ${LATENCY_P95}s exceeds threshold ${THRESHOLD_LATENCY_P95}s"
    exit 1
fi

echo "Deployment validation passed"
exit 0
```

---

## **Appendix: Additional Resources**

### Useful PromQL Queries

```promql
# Top 5 endpoints by request count
topk(5, sum by (endpoint) (rate(http_requests_total[5m])))

# Error rate by service
sum by (service) (rate(http_requests_total{status=~"5.."}[5m]))
/
sum by (service) (rate(http_requests_total[5m]))

# Memory usage percentage
(node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes)
/ node_memory_MemTotal_bytes * 100

# Disk space remaining
(node_filesystem_avail_bytes / node_filesystem_size_bytes) * 100

# Request rate comparison (current vs 1 hour ago)
rate(http_requests_total[5m])
/
rate(http_requests_total[5m] offset 1h)

# Apdex score (T=100ms)
(
  sum(rate(http_request_duration_seconds_bucket{le="0.1"}[5m]))
  + sum(rate(http_request_duration_seconds_bucket{le="0.4"}[5m])) / 2
)
/ sum(rate(http_request_duration_seconds_count[5m]))
```

### References
- Prometheus Documentation: https://prometheus.io/docs/
- Grafana Documentation: https://grafana.com/docs/
- PromQL Guide: https://prometheus.io/docs/prometheus/latest/querying/basics/
- AlertManager Configuration: https://prometheus.io/docs/alerting/latest/configuration/
- SLO Best Practices: https://sre.google/workbook/implementing-slos/
- Prometheus Exporters: https://prometheus.io/docs/instrumenting/exporters/

### Best Practices Summary
- Keep metric cardinality low (<10,000 unique series per service)
- Use recording rules for frequently queried complex expressions
- Set appropriate retention periods based on storage capacity
- Use alert inhibit rules to reduce noise
- Monitor the monitoring system itself (meta-monitoring)
- Regular dashboard and alert rule reviews
- Document SLOs and alert runbooks
- Test alerts before production deployment
- Use consistent naming conventions for metrics and labels
