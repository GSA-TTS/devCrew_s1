/**
 * Issue #37: Sample k6 Load Test Script
 *
 * This is a sample load test script demonstrating various k6 features:
 * - HTTP GET and POST requests
 * - Custom metrics and checks
 * - Load stages (ramp-up/down)
 * - Performance thresholds
 *
 * Usage:
 *   k6 run issue_37_sample_test.js
 *   k6 run --vus 50 --duration 2m issue_37_sample_test.js
 */

import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend, Counter } from 'k6/metrics';

// Custom metrics
const errorRate = new Rate('custom_error_rate');
const responseTimeTrend = new Trend('custom_response_time');
const requestCounter = new Counter('custom_request_count');

// Test configuration
export const options = {
    // Load stages - gradually ramp up to test capacity
    stages: [
        { duration: '30s', target: 10 },   // Ramp up to 10 VUs over 30s
        { duration: '1m', target: 10 },    // Stay at 10 VUs for 1 minute
        { duration: '30s', target: 50 },   // Ramp up to 50 VUs over 30s
        { duration: '2m', target: 50 },    // Stay at 50 VUs for 2 minutes
        { duration: '30s', target: 100 },  // Spike to 100 VUs over 30s
        { duration: '1m', target: 100 },   // Stay at 100 VUs for 1 minute
        { duration: '30s', target: 0 },    // Ramp down to 0
    ],

    // Performance thresholds (SLAs)
    thresholds: {
        // 95% of requests should complete within 500ms
        'http_req_duration': ['p(95)<500', 'p(99)<1000'],

        // Error rate should be less than 1%
        'http_req_failed': ['rate<0.01'],

        // Custom metrics thresholds
        'custom_error_rate': ['rate<0.01'],

        // Request rate should be at least 10 RPS
        'http_reqs': ['rate>10'],
    },

    // Additional options
    noConnectionReuse: false,
    userAgent: 'k6-devCrew-LoadTester/1.0',

    // HTTP/2 support
    insecureSkipTLSVerify: true,

    // Tags for grouping and filtering
    tags: {
        testType: 'sample',
        environment: 'development',
    },
};

// Base URL - can be overridden with environment variable
const BASE_URL = __ENV.BASE_URL || 'https://test-api.k6.io';

/**
 * Setup function - runs once before the test starts
 */
export function setup() {
    console.log('Starting load test...');
    console.log(`Target URL: ${BASE_URL}`);
    console.log(`VUs: ${__VU}`);

    // Perform any setup actions (e.g., authentication)
    return {
        timestamp: new Date().toISOString(),
        baseUrl: BASE_URL,
    };
}

/**
 * Main test function - executed by each virtual user
 */
export default function(data) {
    // Scenario 1: GET request to list endpoint
    const listResponse = http.get(`${BASE_URL}/public/crocodiles/`);

    // Check response status and content
    const listSuccess = check(listResponse, {
        'list status is 200': (r) => r.status === 200,
        'list response has data': (r) => r.json().length > 0,
        'list response time < 500ms': (r) => r.timings.duration < 500,
    });

    // Record metrics
    errorRate.add(!listSuccess);
    responseTimeTrend.add(listResponse.timings.duration);
    requestCounter.add(1);

    // Scenario 2: GET request to detail endpoint
    if (listSuccess && listResponse.json().length > 0) {
        const firstId = listResponse.json()[0].id;
        const detailResponse = http.get(`${BASE_URL}/public/crocodiles/${firstId}/`);

        const detailSuccess = check(detailResponse, {
            'detail status is 200': (r) => r.status === 200,
            'detail has name': (r) => r.json().name !== undefined,
            'detail response time < 300ms': (r) => r.timings.duration < 300,
        });

        errorRate.add(!detailSuccess);
        responseTimeTrend.add(detailResponse.timings.duration);
        requestCounter.add(1);
    }

    // Scenario 3: POST request (requires authentication in real scenario)
    const postPayload = JSON.stringify({
        name: `Test Crocodile ${__VU}-${__ITER}`,
        sex: 'M',
        date_of_birth: '2020-01-01',
    });

    const postParams = {
        headers: {
            'Content-Type': 'application/json',
        },
    };

    // Note: This will fail without authentication - that's expected for demo
    const postResponse = http.post(
        `${BASE_URL}/public/crocodiles/`,
        postPayload,
        postParams
    );

    // We expect 401 or 403 without authentication
    check(postResponse, {
        'post requires auth': (r) => r.status === 401 || r.status === 403,
    });

    requestCounter.add(1);

    // Scenario 4: Batch requests
    const batchRequests = [
        ['GET', `${BASE_URL}/public/crocodiles/1/`, null, {}],
        ['GET', `${BASE_URL}/public/crocodiles/2/`, null, {}],
        ['GET', `${BASE_URL}/public/crocodiles/3/`, null, {}],
    ];

    const batchResponses = http.batch(batchRequests);

    batchResponses.forEach((response) => {
        const batchSuccess = check(response, {
            'batch status is 200 or 404': (r) => r.status === 200 || r.status === 404,
        });
        errorRate.add(!batchSuccess);
        requestCounter.add(1);
    });

    // Think time - simulate user reading/processing
    sleep(Math.random() * 2 + 1); // Random sleep between 1-3 seconds
}

/**
 * Teardown function - runs once after the test completes
 */
export function teardown(data) {
    console.log('Load test completed.');
    console.log(`Started at: ${data.timestamp}`);
}

/**
 * Handle summary - customize the end-of-test summary
 */
export function handleSummary(data) {
    console.log('Preparing test summary...');

    // You can process data.metrics here to create custom reports
    return {
        'stdout': textSummary(data, { indent: ' ', enableColors: true }),
    };
}

/**
 * Helper function for text summary (simplified version)
 */
function textSummary(data, options = {}) {
    const indent = options.indent || '';
    let summary = '\n';

    summary += `${indent}Test Summary:\n`;
    summary += `${indent}  Duration: ${data.state.testRunDurationMs / 1000}s\n`;

    if (data.metrics.http_reqs) {
        summary += `${indent}  Total Requests: ${data.metrics.http_reqs.values.count}\n`;
    }

    if (data.metrics.http_req_duration) {
        const duration = data.metrics.http_req_duration.values;
        summary += `${indent}  Response Times:\n`;
        summary += `${indent}    avg: ${duration.avg.toFixed(2)}ms\n`;
        summary += `${indent}    p95: ${duration['p(95)'].toFixed(2)}ms\n`;
        summary += `${indent}    p99: ${duration['p(99)'].toFixed(2)}ms\n`;
    }

    if (data.metrics.http_req_failed) {
        const failRate = data.metrics.http_req_failed.values.rate * 100;
        summary += `${indent}  Error Rate: ${failRate.toFixed(2)}%\n`;
    }

    return summary;
}
