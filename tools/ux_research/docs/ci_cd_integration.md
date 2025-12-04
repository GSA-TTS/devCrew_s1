# CI/CD Integration Guide

Integrate accessibility testing into your CI/CD pipelines for continuous UX
monitoring and automated quality gates.

## Table of Contents

- [Overview](#overview)
- [GitHub Actions](#github-actions)
- [GitLab CI](#gitlab-ci)
- [Jenkins](#jenkins)
- [CircleCI](#circleci)
- [Azure DevOps](#azure-devops)
- [Quality Gates](#quality-gates)
- [Reporting Integration](#reporting-integration)
- [Best Practices](#best-practices)

## Overview

### Benefits of CI/CD Integration

- **Early Detection**: Catch accessibility issues before production
- **Automated Testing**: No manual intervention required
- **Quality Gates**: Block deployments with critical violations
- **Trend Tracking**: Monitor accessibility scores over time
- **Shift Left**: Test earlier in development cycle
- **Compliance**: Ensure WCAG compliance continuously

### Integration Points

```
Development Workflow:

1. Local Development
   └─> Pre-commit hooks (quick checks)

2. Pull Request
   └─> CI pipeline (full audit)
   └─> Status checks (pass/fail)
   └─> Comment with results

3. Merge to Main
   └─> Full site audit
   └─> Baseline comparison
   └─> Report generation

4. Staging Deployment
   └─> Comprehensive audit
   └─> Performance testing
   └─> Trend analysis

5. Production Deployment
   └─> Smoke tests
   └─> Monitoring setup
```

## GitHub Actions

### Basic Workflow

```yaml
# .github/workflows/accessibility.yml

name: Accessibility Audit

on:
  pull_request:
    branches: [main, develop]
  push:
    branches: [main]
  schedule:
    - cron: '0 9 * * 1'  # Weekly on Monday at 9 AM

jobs:
  accessibility-audit:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: 'pip'

      - name: Install UX Research Platform
        run: |
          cd tools/ux_research
          pip install -r requirements.txt

      - name: Install Playwright browsers
        run: playwright install chromium

      - name: Run accessibility audit
        run: |
          ux-tool audit \
            --url https://staging.example.com \
            --wcag-level AA \
            --output-format json html \
            --output-dir ./reports
        env:
          SITE_URL: ${{ secrets.STAGING_URL }}

      - name: Upload reports
        uses: actions/upload-artifact@v4
        if: always()
        with:
          name: accessibility-reports
          path: ./reports/
          retention-days: 30

      - name: Check for critical/high issues
        run: |
          CRITICAL=$(jq '.summary.by_severity.critical' ./reports/audit.json)
          HIGH=$(jq '.summary.by_severity.high' ./reports/audit.json)

          if [ "$CRITICAL" -gt 0 ] || [ "$HIGH" -gt 5 ]; then
            echo "❌ Found $CRITICAL critical and $HIGH high severity violations"
            exit 1
          else
            echo "✅ Accessibility check passed"
          fi

      - name: Comment PR with results
        uses: actions/github-script@v7
        if: github.event_name == 'pull_request'
        with:
          script: |
            const fs = require('fs');
            const audit = JSON.parse(fs.readFileSync('./reports/audit.json', 'utf8'));

            const body = `## Accessibility Audit Results

            **Score:** ${audit.summary.score}/100
            **Grade:** ${audit.summary.grade}

            **Violations:**
            - Critical: ${audit.summary.by_severity.critical}
            - High: ${audit.summary.by_severity.high}
            - Medium: ${audit.summary.by_severity.medium}
            - Low: ${audit.summary.by_severity.low}

            [View detailed report](https://github.com/${{ github.repository }}/actions/runs/${{ github.run_id }})
            `;

            github.rest.issues.createComment({
              owner: context.repo.owner,
              repo: context.repo.repo,
              issue_number: context.issue.number,
              body: body
            });
```

### Advanced Workflow with Baseline Comparison

```yaml
# .github/workflows/accessibility-advanced.yml

name: Advanced Accessibility Audit

on:
  pull_request:
  push:
    branches: [main]

jobs:
  audit:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0  # Fetch all history for baseline comparison

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r tools/ux_research/requirements.txt
          playwright install --with-deps chromium

      - name: Download baseline report
        uses: actions/download-artifact@v4
        with:
          name: baseline-report
          path: ./baseline/
        continue-on-error: true

      - name: Run accessibility audit
        run: |
          ux-tool audit \
            --url ${{ secrets.STAGING_URL }} \
            --wcag-level AA \
            --max-pages 50 \
            --output-format json \
            --output-dir ./reports

      - name: Compare with baseline
        if: github.event_name == 'pull_request'
        run: |
          if [ -f ./baseline/audit.json ]; then
            ux-tool compare \
              --baseline ./baseline/audit.json \
              --current ./reports/audit.json \
              --output ./reports/comparison.json

            # Check for regressions
            REGRESSIONS=$(jq '.regressions | length' ./reports/comparison.json)

            if [ "$REGRESSIONS" -gt 0 ]; then
              echo "❌ Found $REGRESSIONS new accessibility violations"
              jq '.regressions' ./reports/comparison.json
              exit 1
            fi
          else
            echo "⚠️  No baseline found, skipping comparison"
          fi

      - name: Generate visual report
        run: |
          ux-tool report \
            --audit ./reports/audit.json \
            --output ./reports/report.html \
            --format html

      - name: Upload reports
        uses: actions/upload-artifact@v4
        with:
          name: accessibility-reports
          path: ./reports/

      - name: Update baseline (on main branch)
        if: github.ref == 'refs/heads/main'
        uses: actions/upload-artifact@v4
        with:
          name: baseline-report
          path: ./reports/audit.json

      - name: Post PR comment with comparison
        if: github.event_name == 'pull_request'
        uses: actions/github-script@v7
        with:
          script: |
            const fs = require('fs');
            const current = JSON.parse(fs.readFileSync('./reports/audit.json', 'utf8'));

            let body = `## 🔍 Accessibility Audit Results\n\n`;
            body += `**Score:** ${current.summary.score}/100 (${current.summary.grade})\n\n`;

            if (fs.existsSync('./reports/comparison.json')) {
              const comparison = JSON.parse(fs.readFileSync('./reports/comparison.json', 'utf8'));
              const scoreChange = comparison.score_change;

              body += `**Compared to baseline:** ${scoreChange >= 0 ? '⬆️' : '⬇️'} ${scoreChange}\n\n`;

              if (comparison.regressions.length > 0) {
                body += `### ❌ New Violations (${comparison.regressions.length})\n\n`;
                comparison.regressions.slice(0, 5).forEach(v => {
                  body += `- **${v.id}** (${v.impact}): ${v.description}\n`;
                });
                if (comparison.regressions.length > 5) {
                  body += `\n_... and ${comparison.regressions.length - 5} more_\n`;
                }
              }

              if (comparison.fixes.length > 0) {
                body += `\n### ✅ Fixed Violations (${comparison.fixes.length})\n\n`;
                comparison.fixes.slice(0, 3).forEach(v => {
                  body += `- **${v.id}**: ${v.description}\n`;
                });
              }
            }

            github.rest.issues.createComment({
              owner: context.repo.owner,
              repo: context.repo.repo,
              issue_number: context.issue.number,
              body: body
            });

      - name: Set status check
        if: always()
        uses: actions/github-script@v7
        with:
          script: |
            const fs = require('fs');
            const audit = JSON.parse(fs.readFileSync('./reports/audit.json', 'utf8'));

            const state = audit.summary.score >= 85 ? 'success' : 'failure';
            const description = `Accessibility score: ${audit.summary.score}/100`;

            github.rest.repos.createCommitStatus({
              owner: context.repo.owner,
              repo: context.repo.repo,
              sha: context.sha,
              state: state,
              description: description,
              context: 'Accessibility Audit'
            });
```

### Pre-commit Hook

```yaml
# .github/workflows/pre-commit.yml

name: Pre-commit Checks

on:
  pull_request:

jobs:
  quick-check:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install UX tools
        run: pip install -r tools/ux_research/requirements.txt

      - name: Quick accessibility check (changed files only)
        run: |
          # Get changed HTML files
          CHANGED_FILES=$(git diff --name-only origin/main...HEAD | grep '\.html$' || true)

          if [ -n "$CHANGED_FILES" ]; then
            echo "Checking changed files: $CHANGED_FILES"
            for file in $CHANGED_FILES; do
              ux-tool audit --file "$file" --quick-check
            done
          else
            echo "No HTML files changed"
          fi
```

## GitLab CI

### Basic Configuration

```yaml
# .gitlab-ci.yml

stages:
  - build
  - test
  - deploy

variables:
  STAGING_URL: "https://staging.example.com"

accessibility_audit:
  stage: test
  image: python:3.11
  before_script:
    - pip install -r tools/ux_research/requirements.txt
    - playwright install chromium
  script:
    - ux-tool audit --url $STAGING_URL --wcag-level AA --output-format json html
    - |
      CRITICAL=$(jq '.summary.by_severity.critical' audit.json)
      if [ "$CRITICAL" -gt 0 ]; then
        echo "Critical accessibility violations found"
        exit 1
      fi
  artifacts:
    reports:
      junit: reports/accessibility-junit.xml
    paths:
      - reports/
    expire_in: 30 days
  only:
    - merge_requests
    - main

accessibility_scheduled:
  stage: test
  image: python:3.11
  before_script:
    - pip install -r tools/ux_research/requirements.txt
    - playwright install chromium
  script:
    - ux-tool audit --url $STAGING_URL --max-pages 100 --output-format json html pdf
    - ux-tool report --audit audit.json --output weekly-report.html
  artifacts:
    paths:
      - reports/
    expire_in: 90 days
  only:
    - schedules
```

### Merge Request Integration

```yaml
# .gitlab-ci.yml

accessibility_mr:
  stage: test
  image: python:3.11
  script:
    - pip install -r tools/ux_research/requirements.txt
    - playwright install chromium
    - ux-tool audit --url $CI_MERGE_REQUEST_SOURCE_BRANCH_NAME.preview.example.com
    - |
      # Post comment to MR
      SCORE=$(jq '.summary.score' audit.json)
      VIOLATIONS=$(jq '.summary.total_violations' audit.json)

      curl -X POST \
        -H "PRIVATE-TOKEN: $GITLAB_TOKEN" \
        -d "body=Accessibility Score: $SCORE/100 ($VIOLATIONS violations)" \
        "$CI_API_V4_URL/projects/$CI_PROJECT_ID/merge_requests/$CI_MERGE_REQUEST_IID/notes"
  only:
    - merge_requests
```

## Jenkins

### Jenkinsfile

```groovy
// Jenkinsfile

pipeline {
    agent any

    environment {
        STAGING_URL = credentials('staging-url')
    }

    stages {
        stage('Setup') {
            steps {
                sh '''
                    python3 -m venv venv
                    . venv/bin/activate
                    pip install -r tools/ux_research/requirements.txt
                    playwright install chromium
                '''
            }
        }

        stage('Accessibility Audit') {
            steps {
                sh '''
                    . venv/bin/activate
                    ux-tool audit \
                        --url ${STAGING_URL} \
                        --wcag-level AA \
                        --output-format json html \
                        --output-dir reports/
                '''
            }
        }

        stage('Quality Gate') {
            steps {
                script {
                    def audit = readJSON file: 'reports/audit.json'
                    def score = audit.summary.score

                    if (score < 85) {
                        error("Accessibility score ${score} is below threshold of 85")
                    }

                    echo "✅ Accessibility check passed: ${score}/100"
                }
            }
        }

        stage('Publish Report') {
            steps {
                publishHTML([
                    reportDir: 'reports',
                    reportFiles: 'audit.html',
                    reportName: 'Accessibility Report',
                    keepAll: true
                ])
            }
        }
    }

    post {
        always {
            archiveArtifacts artifacts: 'reports/**', allowEmptyArchive: true
        }
        failure {
            emailext(
                subject: "Accessibility Audit Failed: ${env.JOB_NAME} #${env.BUILD_NUMBER}",
                body: "Check console output at ${env.BUILD_URL}",
                to: "${env.CHANGE_AUTHOR_EMAIL}"
            )
        }
    }
}
```

## CircleCI

### Configuration

```yaml
# .circleci/config.yml

version: 2.1

executors:
  python-executor:
    docker:
      - image: cimg/python:3.11-browsers
    resource_class: medium

jobs:
  accessibility-audit:
    executor: python-executor
    steps:
      - checkout

      - restore_cache:
          keys:
            - v1-dependencies-{{ checksum "tools/ux_research/requirements.txt" }}

      - run:
          name: Install dependencies
          command: |
            pip install -r tools/ux_research/requirements.txt
            playwright install chromium

      - save_cache:
          paths:
            - ~/.cache/pip
            - ~/.cache/ms-playwright
          key: v1-dependencies-{{ checksum "tools/ux_research/requirements.txt" }}

      - run:
          name: Run accessibility audit
          command: |
            ux-tool audit \
              --url https://staging.example.com \
              --wcag-level AA \
              --output-format json html \
              --output-dir /tmp/reports

      - run:
          name: Check quality gate
          command: |
            SCORE=$(jq '.summary.score' /tmp/reports/audit.json)
            echo "Accessibility score: $SCORE"

            if [ "$SCORE" -lt 85 ]; then
              echo "Score below threshold"
              exit 1
            fi

      - store_artifacts:
          path: /tmp/reports
          destination: accessibility-reports

      - store_test_results:
          path: /tmp/reports

workflows:
  version: 2
  build-and-test:
    jobs:
      - accessibility-audit:
          filters:
            branches:
              only:
                - main
                - develop

  scheduled-audit:
    triggers:
      - schedule:
          cron: "0 9 * * 1"
          filters:
            branches:
              only: main
    jobs:
      - accessibility-audit
```

## Azure DevOps

### Pipeline YAML

```yaml
# azure-pipelines.yml

trigger:
  - main
  - develop

pr:
  - main
  - develop

pool:
  vmImage: 'ubuntu-latest'

variables:
  - group: accessibility-secrets
  - name: stagingUrl
    value: 'https://staging.example.com'

stages:
  - stage: AccessibilityAudit
    displayName: 'Accessibility Audit'
    jobs:
      - job: Audit
        displayName: 'Run Accessibility Audit'
        steps:
          - task: UsePythonVersion@0
            inputs:
              versionSpec: '3.11'
              addToPath: true

          - script: |
              pip install -r tools/ux_research/requirements.txt
              playwright install chromium
            displayName: 'Install dependencies'

          - script: |
              ux-tool audit \
                --url $(stagingUrl) \
                --wcag-level AA \
                --output-format json html \
                --output-dir $(Build.ArtifactStagingDirectory)/reports
            displayName: 'Run accessibility audit'

          - script: |
              SCORE=$(jq '.summary.score' $(Build.ArtifactStagingDirectory)/reports/audit.json)
              echo "##vso[task.setvariable variable=accessibilityScore]$SCORE"

              if [ "$SCORE" -lt 85 ]; then
                echo "##vso[task.logissue type=error]Accessibility score $SCORE is below threshold"
                exit 1
              fi
            displayName: 'Check quality gate'

          - task: PublishBuildArtifacts@1
            inputs:
              pathToPublish: '$(Build.ArtifactStagingDirectory)/reports'
              artifactName: 'accessibility-reports'
            condition: always()

          - task: PublishPipelineMetadata@0
            inputs:
              metadata: |
                {
                  "accessibilityScore": "$(accessibilityScore)"
                }
```

## Quality Gates

### Score-Based Gates

```bash
# Minimum score threshold
SCORE=$(jq '.summary.score' audit.json)
MIN_SCORE=85

if [ "$SCORE" -lt "$MIN_SCORE" ]; then
  echo "❌ Score $SCORE below threshold $MIN_SCORE"
  exit 1
fi
```

### Severity-Based Gates

```bash
# Block on critical/high violations
CRITICAL=$(jq '.summary.by_severity.critical' audit.json)
HIGH=$(jq '.summary.by_severity.high' audit.json)

if [ "$CRITICAL" -gt 0 ]; then
  echo "❌ Found $CRITICAL critical violations"
  exit 1
fi

if [ "$HIGH" -gt 5 ]; then
  echo "❌ Found $HIGH high violations (threshold: 5)"
  exit 1
fi
```

### Regression Gates

```bash
# Block on new violations
if [ -f baseline.json ]; then
  ux-tool compare --baseline baseline.json --current audit.json

  REGRESSIONS=$(jq '.regressions | length' comparison.json)

  if [ "$REGRESSIONS" -gt 0 ]; then
    echo "❌ Found $REGRESSIONS new violations"
    jq '.regressions' comparison.json
    exit 1
  fi
fi
```

### Custom Gates

```bash
# Custom validation logic
AUDIT_JSON="audit.json"

# Check specific rules
COLOR_CONTRAST=$(jq '[.violations[] | select(.id == "color-contrast")] | length' $AUDIT_JSON)
if [ "$COLOR_CONTRAST" -gt 0 ]; then
  echo "❌ Color contrast violations found"
  exit 1
fi

# Check specific pages
CHECKOUT_SCORE=$(jq '.pages[] | select(.url | contains("/checkout")) | .score' $AUDIT_JSON)
if [ "$CHECKOUT_SCORE" -lt 95 ]; then
  echo "❌ Checkout page score too low"
  exit 1
fi
```

## Reporting Integration

### Slack Notifications

```bash
# Send Slack notification
SCORE=$(jq '.summary.score' audit.json)
VIOLATIONS=$(jq '.summary.total_violations' audit.json)

EMOJI=$([ "$SCORE" -ge 90 ] && echo "✅" || echo "⚠️")

curl -X POST $SLACK_WEBHOOK_URL \
  -H 'Content-Type: application/json' \
  -d "{
    \"text\": \"${EMOJI} Accessibility Audit Complete\",
    \"attachments\": [{
      \"color\": \"$([ $SCORE -ge 90 ] && echo 'good' || echo 'warning')\",
      \"fields\": [
        {\"title\": \"Score\", \"value\": \"${SCORE}/100\", \"short\": true},
        {\"title\": \"Violations\", \"value\": \"${VIOLATIONS}\", \"short\": true}
      ]
    }]
  }"
```

### Email Reports

```bash
# Send email with report
REPORT_HTML="audit-report.html"

python3 << EOF
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

msg = MIMEMultipart()
msg['From'] = 'ci@example.com'
msg['To'] = 'ux-team@example.com'
msg['Subject'] = 'Weekly Accessibility Report'

with open('$REPORT_HTML', 'r') as f:
    body = f.read()

msg.attach(MIMEText(body, 'html'))

server = smtplib.SMTP('smtp.example.com', 587)
server.starttls()
server.login('user', 'password')
server.send_message(msg)
server.quit()
EOF
```

### GitHub Issues

```bash
# Create GitHub issue for violations
CRITICAL=$(jq '.summary.by_severity.critical' audit.json)

if [ "$CRITICAL" -gt 0 ]; then
  VIOLATIONS=$(jq -r '.violations[] | select(.impact == "critical") | "- \(.id): \(.description)"' audit.json)

  gh issue create \
    --title "Critical Accessibility Violations Detected" \
    --body "## Critical Violations Found

$VIOLATIONS

[View full report](https://github.com/$REPO/actions/runs/$RUN_ID)" \
    --label accessibility,bug \
    --assignee ux-team
fi
```

## Best Practices

### 1. Test Early and Often

```yaml
# Test on every PR
on:
  pull_request:

# Test on every commit to main
on:
  push:
    branches: [main]

# Test nightly
on:
  schedule:
    - cron: '0 2 * * *'
```

### 2. Use Caching

```yaml
# Cache dependencies
- uses: actions/cache@v4
  with:
    path: |
      ~/.cache/pip
      ~/.cache/ms-playwright
    key: ${{ runner.os }}-ux-${{ hashFiles('**/requirements.txt') }}

# Cache audit results (for comparison)
- uses: actions/cache@v4
  with:
    path: ./baseline
    key: accessibility-baseline-${{ github.ref }}
```

### 3. Parallel Execution

```yaml
# Test multiple environments in parallel
jobs:
  audit:
    strategy:
      matrix:
        environment: [staging, qa, production]
        browser: [chromium, firefox]
    steps:
      - name: Audit ${{ matrix.environment }} on ${{ matrix.browser }}
        run: |
          ux-tool audit \
            --url ${{ secrets[matrix.environment] }} \
            --browser ${{ matrix.browser }}
```

### 4. Fail Fast

```yaml
# Fail fast on critical issues
- name: Quick check for critical violations
  run: |
    ux-tool audit --url $URL --quick-check --fail-on critical
```

### 5. Comprehensive Reporting

```yaml
# Generate multiple report formats
- name: Generate reports
  run: |
    ux-tool report \
      --audit audit.json \
      --output-formats html,pdf,json,csv \
      --include-screenshots \
      --include-recommendations
```

## Troubleshooting

### Issue: Pipeline timeouts

```yaml
# Increase timeout
- name: Run audit
  run: ux-tool audit --url $URL
  timeout-minutes: 30  # Default is 360
```

### Issue: Browser installation fails

```yaml
# Install system dependencies
- name: Install browser dependencies
  run: |
    playwright install-deps
    playwright install chromium
```

### Issue: Out of memory

```yaml
# Reduce concurrent pages
- name: Run audit with limits
  run: |
    ux-tool audit --url $URL --parallel 2 --max-pages 50
```

## Next Steps

1. **Choose your CI/CD platform**: Select appropriate configuration
2. **Set up quality gates**: Define pass/fail criteria
3. **Configure notifications**: Alert team of failures
4. **Establish baselines**: Create initial reports for comparison
5. **Monitor trends**: Track improvements over time

## Quick Reference

```yaml
# Minimal GitHub Actions example
name: Accessibility
on: pull_request
jobs:
  audit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: |
          pip install -r tools/ux_research/requirements.txt
          playwright install chromium
          ux-tool audit --url ${{ secrets.STAGING_URL }} --fail-on critical,high
```
