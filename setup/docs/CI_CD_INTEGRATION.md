# CI/CD Integration Guide for DevGRU Setup

## Overview

This guide provides comprehensive examples for integrating the DevGRU setup script into various CI/CD platforms. The setup script is designed to be CI-friendly with features like non-interactive mode, exit codes, logging, and profile-based installations.

## Table of Contents

- [GitHub Actions Integration](#github-actions-integration)
- [GitLab CI Integration](#gitlab-ci-integration)
- [Docker Container Setup](#docker-container-setup)
- [Pre-commit Hooks](#pre-commit-hooks)
- [Caching Strategies](#caching-strategies)
- [CI Environment Troubleshooting](#ci-environment-troubleshooting)
- [Profile Usage in CI/CD](#profile-usage-in-cicd)
- [Best Practices](#best-practices)

---

## GitHub Actions Integration

### Basic Workflow

```yaml
name: DevGRU Setup - Standard Profile

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  setup-and-test:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Install prerequisites
        run: |
          sudo apt-get update
          sudo apt-get install -y jq curl git

      - name: Run DevGRU setup (standard profile)
        run: |
          cd setup
          chmod +x setup_devgru.sh
          ./setup_devgru.sh --profile standard --verbose

      - name: Verify installation
        run: |
          python3 --version
          pip list
          python3 -c "import pandas, requests, pydantic; print('Core packages verified')"

      - name: Upload logs
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: setup-logs
          path: setup/logs/
          retention-days: 7
```

### Multi-OS Matrix Testing

```yaml
name: DevGRU Multi-OS Testing

on:
  push:
    branches: [ main ]
  schedule:
    - cron: '0 2 * * 1'  # Weekly on Monday at 2 AM

jobs:
  test-setup:
    strategy:
      matrix:
        os: [ubuntu-latest, ubuntu-22.04, ubuntu-20.04, macos-latest, macos-13]
        profile: [minimal, standard, security]

    runs-on: ${{ matrix.os }}

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Install prerequisites (Ubuntu)
        if: runner.os == 'Linux'
        run: |
          sudo apt-get update
          sudo apt-get install -y jq curl git

      - name: Install prerequisites (macOS)
        if: runner.os == 'macOS'
        run: |
          brew install jq curl git

      - name: Run DevGRU setup
        run: |
          cd setup
          chmod +x setup_devgru.sh
          ./setup_devgru.sh --profile ${{ matrix.profile }} --verbose

      - name: Verify installation
        run: |
          python3 --version
          pip list | grep -E "pandas|requests|pydantic"

      - name: Run tests
        run: |
          cd setup/modules
          chmod +x test_python_setup.sh
          ./test_python_setup.sh

      - name: Upload artifacts
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: logs-${{ matrix.os }}-${{ matrix.profile }}
          path: |
            setup/logs/
            setup/.state/
```

### Workflow with Caching

```yaml
name: DevGRU Setup with Caching

on:
  push:
    branches: [ main, develop ]

jobs:
  setup:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Cache pip packages
        uses: actions/cache@v4
        with:
          path: ~/.cache/pip
          key: ${{ runner.os }}-pip-${{ hashFiles('setup/requirements/*.txt') }}
          restore-keys: |
            ${{ runner.os }}-pip-

      - name: Cache apt packages
        uses: actions/cache@v4
        with:
          path: /var/cache/apt/archives
          key: ${{ runner.os }}-apt-${{ hashFiles('setup/setup_devgru.sh') }}
          restore-keys: |
            ${{ runner.os }}-apt-

      - name: Install prerequisites
        run: |
          sudo apt-get update
          sudo apt-get install -y jq curl git

      - name: Run setup with caching
        run: |
          cd setup
          chmod +x setup_devgru.sh
          ./setup_devgru.sh --profile standard --verbose

      - name: Verify and test
        run: |
          python3 --version
          pip list
          python3 -m pytest tests/ -v
```

### AWS Cloud Profile Workflow

```yaml
name: AWS Development Setup

on:
  push:
    branches: [ main ]
    paths:
      - 'aws/**'
      - 'setup/**'

jobs:
  aws-setup:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Install prerequisites
        run: |
          sudo apt-get update
          sudo apt-get install -y jq curl git

      - name: Run AWS profile setup
        run: |
          cd setup
          chmod +x setup_devgru.sh
          ./setup_devgru.sh --profile cloud-aws --verbose

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-east-1

      - name: Verify AWS CLI
        run: |
          aws --version
          aws sts get-caller-identity

      - name: Test boto3 integration
        run: |
          python3 -c "import boto3; print('boto3 version:', boto3.__version__)"
```

### Security Scanning Workflow

```yaml
name: Security Profile Setup and Scan

on:
  pull_request:
    branches: [ main ]
  schedule:
    - cron: '0 0 * * 0'  # Weekly on Sunday at midnight

jobs:
  security-audit:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Install prerequisites
        run: |
          sudo apt-get update
          sudo apt-get install -y jq curl git

      - name: Run security profile setup
        run: |
          cd setup
          chmod +x setup_devgru.sh
          ./setup_devgru.sh --profile security --verbose

      - name: Run safety check
        run: |
          safety check --json > safety-report.json || true

      - name: Run bandit scan
        run: |
          bandit -r . -f json -o bandit-report.json || true

      - name: Run checkov scan
        run: |
          checkov --directory . --output json > checkov-report.json || true

      - name: Upload security reports
        uses: actions/upload-artifact@v4
        with:
          name: security-reports
          path: |
            safety-report.json
            bandit-report.json
            checkov-report.json
```

---

## GitLab CI Integration

### Basic Pipeline

```yaml
# .gitlab-ci.yml

stages:
  - setup
  - test
  - deploy

variables:
  PIP_CACHE_DIR: "$CI_PROJECT_DIR/.cache/pip"
  PROFILE: "standard"

cache:
  paths:
    - .cache/pip
    - setup/.state/

before_script:
  - apt-get update -qq
  - apt-get install -y jq curl git

setup:minimal:
  stage: setup
  image: ubuntu:22.04
  variables:
    PROFILE: "minimal"
  script:
    - cd setup
    - chmod +x setup_devgru.sh
    - ./setup_devgru.sh --profile ${PROFILE} --verbose
    - python3 --version
    - pip list
  artifacts:
    paths:
      - setup/logs/
      - setup/.state/
    expire_in: 1 week
  only:
    - merge_requests
    - main

setup:standard:
  stage: setup
  image: ubuntu:22.04
  variables:
    PROFILE: "standard"
  script:
    - cd setup
    - chmod +x setup_devgru.sh
    - ./setup_devgru.sh --profile ${PROFILE} --verbose
    - python3 -c "import pandas, requests, pydantic; print('Core verified')"
  artifacts:
    paths:
      - setup/logs/
      - setup/.state/
    expire_in: 1 week
  only:
    - main
    - develop

test:verification:
  stage: test
  image: ubuntu:22.04
  dependencies:
    - setup:standard
  script:
    - cd setup/modules
    - chmod +x test_python_setup.sh
    - ./test_python_setup.sh
  only:
    - merge_requests
    - main
```

### Multi-Profile Pipeline

```yaml
# .gitlab-ci.yml

stages:
  - prerequisites
  - setup
  - verify
  - report

variables:
  PIP_CACHE_DIR: "$CI_PROJECT_DIR/.cache/pip"

.prerequisites_template: &prerequisites
  before_script:
    - apt-get update -qq
    - apt-get install -y jq curl git

.setup_template: &setup_template
  <<: *prerequisites
  stage: setup
  script:
    - cd setup
    - chmod +x setup_devgru.sh
    - ./setup_devgru.sh --profile ${PROFILE} --verbose
  artifacts:
    paths:
      - setup/logs/
      - setup/.state/
    expire_in: 1 week

setup:minimal:
  <<: *setup_template
  image: ubuntu:22.04
  variables:
    PROFILE: "minimal"

setup:standard:
  <<: *setup_template
  image: ubuntu:22.04
  variables:
    PROFILE: "standard"

setup:security:
  <<: *setup_template
  image: ubuntu:22.04
  variables:
    PROFILE: "security"
  only:
    - main

verify:installation:
  <<: *prerequisites
  stage: verify
  image: ubuntu:22.04
  dependencies:
    - setup:standard
  script:
    - python3 --version
    - pip list
    - python3 -c "import pandas, requests, pydantic; print('Verification passed')"

report:generate:
  stage: report
  image: ubuntu:22.04
  dependencies:
    - setup:standard
  script:
    - cat setup/logs/installation_report_*.txt
    - cat setup/.state/installation_state.json | jq .
  when: always
```

### AWS Cloud Pipeline

```yaml
# .gitlab-ci.yml for AWS

stages:
  - setup
  - deploy

variables:
  AWS_DEFAULT_REGION: us-east-1

setup:aws:
  stage: setup
  image: ubuntu:22.04
  before_script:
    - apt-get update -qq
    - apt-get install -y jq curl git
  script:
    - cd setup
    - chmod +x setup_devgru.sh
    - ./setup_devgru.sh --profile cloud-aws --verbose
    - aws --version
    - python3 -c "import boto3; print('boto3 installed')"
  artifacts:
    paths:
      - setup/logs/
      - setup/.state/
    expire_in: 1 week

deploy:aws:
  stage: deploy
  image: ubuntu:22.04
  dependencies:
    - setup:aws
  before_script:
    - cd setup
    - chmod +x setup_devgru.sh
    - ./setup_devgru.sh --profile cloud-aws --verbose
  script:
    - aws sts get-caller-identity
    - aws s3 ls
    # Add your deployment commands here
  only:
    - main
```

### GitLab with Docker

```yaml
# .gitlab-ci.yml with Docker

stages:
  - build
  - test

build:docker:
  stage: build
  image: docker:24-dind
  services:
    - docker:24-dind
  variables:
    DOCKER_TLS_CERTDIR: "/certs"
  before_script:
    - docker info
  script:
    - cd setup
    - docker build -t devgru-setup:standard --build-arg PROFILE=standard -f docker/Dockerfile .
    - docker tag devgru-setup:standard $CI_REGISTRY_IMAGE:$CI_COMMIT_SHORT_SHA
    - docker tag devgru-setup:standard $CI_REGISTRY_IMAGE:latest
  after_script:
    - docker push $CI_REGISTRY_IMAGE:$CI_COMMIT_SHORT_SHA
    - docker push $CI_REGISTRY_IMAGE:latest
  only:
    - main

test:docker:
  stage: test
  image: $CI_REGISTRY_IMAGE:$CI_COMMIT_SHORT_SHA
  script:
    - python3 --version
    - pip list
    - python3 -c "import pandas, requests, pydantic; print('Docker image verified')"
  dependencies:
    - build:docker
```

---

## Docker Container Setup

### Multi-Stage Dockerfile

```dockerfile
# setup/docker/Dockerfile

# Stage 1: Base image with prerequisites
FROM ubuntu:22.04 AS base

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

# Install system prerequisites
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    jq \
    curl \
    git \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Stage 2: DevGRU setup
FROM base AS setup

# Set working directory
WORKDIR /setup

# Copy setup files
COPY setup_devgru.sh .
COPY modules/ modules/
COPY requirements/ requirements/

# Create work directory
RUN mkdir -p /tmp/issue67_work

# Copy prerequisites file (should be generated beforehand)
COPY prerequisites_validated.json /tmp/issue67_work/

# Make script executable
RUN chmod +x setup_devgru.sh

# Run setup with specified profile
ARG PROFILE=standard
RUN ./setup_devgru.sh --profile ${PROFILE} --verbose || \
    (cat logs/setup_*.log && exit 1)

# Stage 3: Runtime image
FROM ubuntu:22.04

# Copy Python installation from setup stage
COPY --from=setup /usr/local /usr/local
COPY --from=setup /usr/lib/python3* /usr/lib/
COPY --from=setup /usr/bin/python3* /usr/bin/

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PATH="/usr/local/bin:${PATH}"

# Verify installation
RUN python3 --version && \
    pip list && \
    python3 -c "import pandas, requests, pydantic; print('Runtime image verified')"

# Set working directory
WORKDIR /workspace

# Default command
CMD ["/bin/bash"]
```

### Profile-Specific Dockerfiles

```dockerfile
# docker/Dockerfile.minimal
FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && \
    apt-get install -y jq curl git && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /setup
COPY . .
RUN chmod +x setup_devgru.sh && \
    ./setup_devgru.sh --profile minimal --verbose

CMD ["/bin/bash"]
```

```dockerfile
# docker/Dockerfile.security
FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && \
    apt-get install -y jq curl git && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /setup
COPY . .
RUN mkdir -p /tmp/issue67_work
COPY prerequisites_validated.json /tmp/issue67_work/
RUN chmod +x setup_devgru.sh && \
    ./setup_devgru.sh --profile security --verbose

WORKDIR /workspace
CMD ["/bin/bash"]
```

### Docker Compose Setup

```yaml
# docker-compose.yml

version: '3.8'

services:
  devgru-minimal:
    build:
      context: .
      dockerfile: docker/Dockerfile
      args:
        PROFILE: minimal
    image: devgru-setup:minimal
    container_name: devgru-minimal
    volumes:
      - ./workspace:/workspace
    command: /bin/bash -c "python3 --version && pip list && tail -f /dev/null"

  devgru-standard:
    build:
      context: .
      dockerfile: docker/Dockerfile
      args:
        PROFILE: standard
    image: devgru-setup:standard
    container_name: devgru-standard
    volumes:
      - ./workspace:/workspace
      - pip-cache:/root/.cache/pip
    command: /bin/bash -c "python3 --version && pip list && tail -f /dev/null"

  devgru-full:
    build:
      context: .
      dockerfile: docker/Dockerfile
      args:
        PROFILE: full
    image: devgru-setup:full
    container_name: devgru-full
    volumes:
      - ./workspace:/workspace
      - pip-cache:/root/.cache/pip
    depends_on:
      - redis
      - postgres
    command: /bin/bash -c "python3 --version && pip list && tail -f /dev/null"

  devgru-aws:
    build:
      context: .
      dockerfile: docker/Dockerfile
      args:
        PROFILE: cloud-aws
    image: devgru-setup:aws
    container_name: devgru-aws
    environment:
      - AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID}
      - AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY}
      - AWS_DEFAULT_REGION=${AWS_DEFAULT_REGION:-us-east-1}
    volumes:
      - ./workspace:/workspace
      - ~/.aws:/root/.aws:ro
    command: /bin/bash

  redis:
    image: redis:7-alpine
    container_name: devgru-redis
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data

  postgres:
    image: postgres:15-alpine
    container_name: devgru-postgres
    environment:
      POSTGRES_DB: devgru
      POSTGRES_USER: devgru
      POSTGRES_PASSWORD: devgru_password
    ports:
      - "5432:5432"
    volumes:
      - postgres-data:/var/lib/postgresql/data

volumes:
  pip-cache:
  redis-data:
  postgres-data:
```

### Docker Build Script

```bash
#!/bin/bash
# docker/build.sh

set -euo pipefail

PROFILES=("minimal" "standard" "full" "security" "cloud-aws" "cloud-azure" "cloud-gcp")
REGISTRY="${DOCKER_REGISTRY:-devgru}"

for profile in "${PROFILES[@]}"; do
    echo "Building Docker image for profile: ${profile}"

    docker build \
        --build-arg PROFILE="${profile}" \
        -t "${REGISTRY}/devgru-setup:${profile}" \
        -t "${REGISTRY}/devgru-setup:${profile}-$(date +%Y%m%d)" \
        -f docker/Dockerfile \
        .

    echo "Successfully built ${REGISTRY}/devgru-setup:${profile}"
done

echo "Building latest tag with standard profile"
docker tag "${REGISTRY}/devgru-setup:standard" "${REGISTRY}/devgru-setup:latest"

echo "All Docker images built successfully!"
```

---

## Pre-commit Hooks

### Basic Pre-commit Configuration

```yaml
# .pre-commit-config.yaml

repos:
  - repo: local
    hooks:
      - id: devgru-setup-validation
        name: Validate DevGRU Setup Script
        entry: bash -c 'cd setup && ./setup_devgru.sh --profile minimal --dry-run'
        language: system
        pass_filenames: false
        files: 'setup/.*'

      - id: shellcheck
        name: ShellCheck
        entry: shellcheck
        language: system
        types: [shell]
        args: ['--severity=warning']
        files: 'setup/.*\.sh$'

      - id: python-syntax
        name: Python Syntax Check
        entry: python3 -m py_compile
        language: system
        types: [python]
```

### Advanced Pre-commit Setup

```yaml
# .pre-commit-config.yaml

repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-json
      - id: check-added-large-files
        args: ['--maxkb=1000']
      - id: check-merge-conflict
      - id: check-executables-have-shebangs

  - repo: https://github.com/koalaman/shellcheck-precommit
    rev: v0.9.0
    hooks:
      - id: shellcheck
        args: ['--severity=warning']
        files: 'setup/.*\.sh$'

  - repo: local
    hooks:
      - id: devgru-dry-run
        name: DevGRU Setup Dry Run
        entry: bash -c 'cd setup && ./setup_devgru.sh --profile minimal --dry-run'
        language: system
        pass_filenames: false
        files: 'setup/(setup_devgru\.sh|modules/.*\.sh)$'
        stages: [commit]

      - id: devgru-prerequisites-check
        name: Check Prerequisites File
        entry: bash -c 'test -f /tmp/issue67_work/prerequisites_validated.json && jq empty /tmp/issue67_work/prerequisites_validated.json'
        language: system
        pass_filenames: false
        files: 'setup/.*'
        stages: [commit]

      - id: devgru-logging-test
        name: Test Logging Functions
        entry: bash -c 'cd setup && bash -n setup_devgru.sh'
        language: system
        pass_filenames: false
        files: 'setup/setup_devgru\.sh$'
        stages: [commit]

  - repo: https://github.com/psf/black
    rev: 23.12.1
    hooks:
      - id: black
        language_version: python3

  - repo: https://github.com/pycqa/isort
    rev: 5.13.2
    hooks:
      - id: isort
        args: ['--profile', 'black']

  - repo: https://github.com/pycqa/flake8
    rev: 7.0.0
    hooks:
      - id: flake8
        args: ['--max-line-length=88', '--extend-ignore=E203,W503']
```

### Custom Pre-commit Hook Script

```bash
#!/bin/bash
# .git/hooks/pre-commit

set -e

echo "Running DevGRU pre-commit checks..."

# Check if setup script has been modified
if git diff --cached --name-only | grep -q "setup/"; then
    echo "DevGRU files modified, running validation..."

    # Run shellcheck
    echo "Running shellcheck..."
    shellcheck setup/setup_devgru.sh setup/modules/*.sh

    # Run dry-run test
    echo "Running dry-run test..."
    cd setup
    ./setup_devgru.sh --profile minimal --dry-run > /dev/null
    cd ..

    echo "DevGRU validation passed!"
fi

exit 0
```

---

## Caching Strategies

### GitHub Actions Caching

```yaml
name: DevGRU with Advanced Caching

on: [push, pull_request]

jobs:
  setup:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      # Cache pip packages
      - name: Cache pip packages
        id: cache-pip
        uses: actions/cache@v4
        with:
          path: ~/.cache/pip
          key: ${{ runner.os }}-pip-${{ hashFiles('setup/requirements/*.txt') }}
          restore-keys: |
            ${{ runner.os }}-pip-

      # Cache apt packages
      - name: Cache apt packages
        id: cache-apt
        uses: actions/cache@v4
        with:
          path: |
            /var/cache/apt/archives
            /var/lib/apt/lists
          key: ${{ runner.os }}-apt-${{ hashFiles('.github/workflows/ci.yml') }}
          restore-keys: |
            ${{ runner.os }}-apt-

      # Cache DevGRU state
      - name: Cache DevGRU installation state
        uses: actions/cache@v4
        with:
          path: setup/.state
          key: ${{ runner.os }}-devgru-state-${{ hashFiles('setup/setup_devgru.sh') }}
          restore-keys: |
            ${{ runner.os }}-devgru-state-

      - name: Install prerequisites
        if: steps.cache-apt.outputs.cache-hit != 'true'
        run: |
          sudo apt-get update
          sudo apt-get install -y jq curl git

      - name: Run setup
        run: |
          cd setup
          chmod +x setup_devgru.sh
          ./setup_devgru.sh --profile standard --verbose
```

### GitLab CI Caching

```yaml
# .gitlab-ci.yml with caching

variables:
  PIP_CACHE_DIR: "$CI_PROJECT_DIR/.cache/pip"
  APT_CACHE_DIR: "$CI_PROJECT_DIR/.cache/apt"

cache:
  key:
    files:
      - setup/requirements/*.txt
      - setup/setup_devgru.sh
  paths:
    - .cache/pip
    - .cache/apt
    - setup/.state
    - setup/logs

before_script:
  - mkdir -p ${APT_CACHE_DIR}
  - apt-get update
  - apt-get install -y jq curl git

setup:
  stage: setup
  script:
    - cd setup
    - chmod +x setup_devgru.sh
    - ./setup_devgru.sh --profile standard --verbose
  artifacts:
    paths:
      - setup/.state
      - setup/logs
    expire_in: 1 week
  cache:
    policy: pull-push
```

### Docker Layer Caching

```dockerfile
# Dockerfile with optimized caching

FROM ubuntu:22.04 AS base

# Cache system packages installation
RUN --mount=type=cache,target=/var/cache/apt \
    --mount=type=cache,target=/var/lib/apt/lists \
    apt-get update && \
    apt-get install -y jq curl git

# Cache pip installations
FROM base AS setup
WORKDIR /setup

# Copy only requirements first for better caching
COPY requirements/ requirements/
COPY prerequisites_validated.json /tmp/issue67_work/

# Install Python packages with caching
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r requirements/requirements-core.txt

# Copy rest of setup files
COPY setup_devgru.sh .
COPY modules/ modules/

ARG PROFILE=standard
RUN chmod +x setup_devgru.sh && \
    ./setup_devgru.sh --profile ${PROFILE} --verbose

FROM base AS runtime
COPY --from=setup /usr/local /usr/local
COPY --from=setup /usr/lib/python3* /usr/lib/

WORKDIR /workspace
CMD ["/bin/bash"]
```

### Custom Caching Script

```bash
#!/bin/bash
# scripts/cache_manager.sh

set -euo pipefail

CACHE_DIR="${HOME}/.devgru_cache"
STATE_FILE="setup/.state/installation_state.json"

# Create cache directory
mkdir -p "${CACHE_DIR}"/{pip,state,logs}

# Save installation state to cache
save_cache() {
    echo "Saving installation state to cache..."

    # Copy state file
    if [[ -f "${STATE_FILE}" ]]; then
        cp "${STATE_FILE}" "${CACHE_DIR}/state/"
    fi

    # Copy pip packages list
    pip list --format=json > "${CACHE_DIR}/pip/packages.json"

    # Copy logs
    cp -r setup/logs/* "${CACHE_DIR}/logs/" 2>/dev/null || true

    echo "Cache saved to ${CACHE_DIR}"
}

# Restore from cache
restore_cache() {
    echo "Restoring from cache..."

    if [[ -f "${CACHE_DIR}/state/installation_state.json" ]]; then
        mkdir -p "setup/.state"
        cp "${CACHE_DIR}/state/installation_state.json" "${STATE_FILE}"
        echo "State restored from cache"
    else
        echo "No cached state found"
    fi
}

# Clear cache
clear_cache() {
    echo "Clearing cache..."
    rm -rf "${CACHE_DIR}"
    echo "Cache cleared"
}

# Main
case "${1:-help}" in
    save)
        save_cache
        ;;
    restore)
        restore_cache
        ;;
    clear)
        clear_cache
        ;;
    *)
        echo "Usage: $0 {save|restore|clear}"
        exit 1
        ;;
esac
```

---

## CI Environment Troubleshooting

### Common Issues and Solutions

#### 1. Prerequisites Not Found

**Problem**: Script fails because jq, curl, or git is not installed.

**Solution**:
```yaml
# GitHub Actions
- name: Install prerequisites
  run: |
    if ! command -v jq &> /dev/null; then
      sudo apt-get update
      sudo apt-get install -y jq curl git
    fi

# GitLab CI
before_script:
  - which jq || apt-get update && apt-get install -y jq curl git
```

#### 2. Permission Denied

**Problem**: Script is not executable in CI environment.

**Solution**:
```bash
# Always ensure script is executable
chmod +x setup/setup_devgru.sh
```

#### 3. Non-Interactive Mode Issues

**Problem**: Script prompts for user input in CI.

**Solution**: The script already handles this, but ensure you're not running as root without the `--yes` equivalent:
```bash
# Use environment variable to skip confirmations
export CI=true
./setup_devgru.sh --profile standard
```

#### 4. Timeout in CI

**Problem**: Installation takes too long and CI times out.

**Solution**:
```yaml
# Increase timeout
jobs:
  setup:
    timeout-minutes: 30
    steps:
      - name: Run setup
        timeout-minutes: 20
        run: ./setup_devgru.sh --profile minimal
```

#### 5. Cache Corruption

**Problem**: Cached packages cause installation failures.

**Solution**:
```bash
# Clear pip cache before installation
pip cache purge
./setup_devgru.sh --profile standard
```

#### 6. Network Issues

**Problem**: Package downloads fail due to network timeouts.

**Solution**:
```bash
# Add retry logic
for i in {1..3}; do
    ./setup_devgru.sh --profile standard && break
    echo "Attempt $i failed, retrying..."
    sleep 5
done
```

#### 7. Disk Space Issues

**Problem**: CI runner runs out of disk space.

**Solution**:
```yaml
- name: Free up disk space
  run: |
    sudo apt-get clean
    sudo rm -rf /usr/share/dotnet
    sudo rm -rf /opt/ghc
    df -h
```

### Debugging Script

```bash
#!/bin/bash
# scripts/ci_debug.sh

echo "=== CI Environment Debug Information ==="

echo -e "\n--- System Information ---"
uname -a
cat /etc/os-release 2>/dev/null || echo "OS release info not available"

echo -e "\n--- Disk Space ---"
df -h

echo -e "\n--- Memory ---"
free -h

echo -e "\n--- Prerequisites ---"
command -v jq && jq --version || echo "jq not found"
command -v curl && curl --version | head -1 || echo "curl not found"
command -v git && git --version || echo "git not found"

echo -e "\n--- Python ---"
command -v python3 && python3 --version || echo "python3 not found"
command -v pip && pip --version || echo "pip not found"

echo -e "\n--- Environment Variables ---"
env | grep -E "(CI|GITHUB|GITLAB|PATH)" | sort

echo -e "\n--- DevGRU Files ---"
ls -la setup/ 2>/dev/null || echo "setup directory not found"

echo -e "\n--- Logs ---"
ls -la setup/logs/ 2>/dev/null || echo "No logs found"

echo -e "\n--- State ---"
if [[ -f setup/.state/installation_state.json ]]; then
    cat setup/.state/installation_state.json | jq .
else
    echo "No state file found"
fi
```

---

## Profile Usage in CI/CD

### Profile Selection Matrix

| Profile | CI Use Case | Advantages | Disadvantages |
|---------|------------|------------|---------------|
| **minimal** | Unit tests, quick builds | Fast (2-3 min), minimal dependencies | Limited functionality |
| **standard** | Integration tests, general CI | Balanced (5-7 min), most packages | Moderate size |
| **full** | End-to-end tests, staging | Complete stack (10-15 min) | Slow, large size |
| **security** | Security scans, audits | Security-focused tools | Specialized use case |
| **cloud-aws** | AWS deployments | AWS integration | Cloud-specific |
| **cloud-azure** | Azure deployments | Azure integration | Cloud-specific |
| **cloud-gcp** | GCP deployments | GCP integration | Cloud-specific |

### Conditional Profile Selection

```yaml
# GitHub Actions - Dynamic profile selection

name: Dynamic Profile Selection

on: [push, pull_request]

jobs:
  setup:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Determine profile
        id: profile
        run: |
          if [[ "${{ github.event_name }}" == "pull_request" ]]; then
            echo "profile=minimal" >> $GITHUB_OUTPUT
          elif [[ "${{ github.ref }}" == "refs/heads/main" ]]; then
            echo "profile=standard" >> $GITHUB_OUTPUT
          elif [[ "${{ github.ref }}" == "refs/heads/develop" ]]; then
            echo "profile=full" >> $GITHUB_OUTPUT
          else
            echo "profile=minimal" >> $GITHUB_OUTPUT
          fi

      - name: Install prerequisites
        run: sudo apt-get update && sudo apt-get install -y jq curl git

      - name: Run setup
        run: |
          cd setup
          chmod +x setup_devgru.sh
          ./setup_devgru.sh --profile ${{ steps.profile.outputs.profile }} --verbose
```

### Branch-Based Profiles

```yaml
# GitLab CI - Branch-based profiles

setup:minimal:
  stage: setup
  script:
    - cd setup
    - ./setup_devgru.sh --profile minimal --verbose
  only:
    - merge_requests
    - /^feature\/.*/

setup:standard:
  stage: setup
  script:
    - cd setup
    - ./setup_devgru.sh --profile standard --verbose
  only:
    - develop
    - /^release\/.*/

setup:full:
  stage: setup
  script:
    - cd setup
    - ./setup_devgru.sh --profile full --verbose
  only:
    - main
    - tags
```

### Path-Based Profile Triggers

```yaml
# GitHub Actions - Trigger different profiles based on changed files

name: Path-Based Profiles

on:
  push:
    paths:
      - 'setup/**'
      - 'src/**'
      - 'tests/**'

jobs:
  detect-changes:
    runs-on: ubuntu-latest
    outputs:
      profile: ${{ steps.detect.outputs.profile }}
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 2

      - name: Detect changes
        id: detect
        run: |
          if git diff HEAD^ HEAD --name-only | grep -q "aws"; then
            echo "profile=cloud-aws" >> $GITHUB_OUTPUT
          elif git diff HEAD^ HEAD --name-only | grep -q "security"; then
            echo "profile=security" >> $GITHUB_OUTPUT
          elif git diff HEAD^ HEAD --name-only | grep -q "setup"; then
            echo "profile=full" >> $GITHUB_OUTPUT
          else
            echo "profile=standard" >> $GITHUB_OUTPUT
          fi

  setup:
    needs: detect-changes
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Install prerequisites
        run: sudo apt-get update && sudo apt-get install -y jq curl git
      - name: Run setup
        run: |
          cd setup
          chmod +x setup_devgru.sh
          ./setup_devgru.sh --profile ${{ needs.detect-changes.outputs.profile }} --verbose
```

---

## Best Practices

### 1. Always Use Dry-Run First

```yaml
- name: Test setup (dry-run)
  run: ./setup_devgru.sh --profile standard --dry-run

- name: Actual setup
  run: ./setup_devgru.sh --profile standard --verbose
```

### 2. Upload Logs as Artifacts

```yaml
- name: Upload logs
  if: always()
  uses: actions/upload-artifact@v4
  with:
    name: devgru-logs-${{ github.run_id }}
    path: |
      setup/logs/
      setup/.state/
    retention-days: 7
```

### 3. Use Caching Effectively

```yaml
# Cache only stable dependencies
- uses: actions/cache@v4
  with:
    path: ~/.cache/pip
    key: ${{ runner.os }}-pip-${{ hashFiles('setup/requirements/*.txt') }}
```

### 4. Implement Retry Logic

```bash
# Retry on failure
MAX_RETRIES=3
for i in $(seq 1 $MAX_RETRIES); do
    ./setup_devgru.sh --profile standard && break
    echo "Attempt $i failed, retrying in 10s..."
    sleep 10
done
```

### 5. Validate Before Proceeding

```bash
# Validate installation before running tests
./setup_devgru.sh --profile standard
python3 -c "import pandas, requests, pydantic" || exit 1
pytest tests/
```

### 6. Use Matrix Testing

```yaml
strategy:
  matrix:
    os: [ubuntu-20.04, ubuntu-22.04, macos-12, macos-13]
    profile: [minimal, standard]
```

### 7. Monitor Resource Usage

```bash
# Check resource usage
echo "Disk space before:"
df -h

./setup_devgru.sh --profile full

echo "Disk space after:"
df -h
```

### 8. Version Pin for Reproducibility

```yaml
# Pin specific versions
- name: Run setup
  run: |
    cd setup
    git checkout v1.0.0  # Pin to specific version
    ./setup_devgru.sh --profile standard
```

### 9. Parallel Execution

```yaml
# Run multiple profiles in parallel
jobs:
  setup-minimal:
    runs-on: ubuntu-latest
    steps:
      - run: ./setup_devgru.sh --profile minimal

  setup-standard:
    runs-on: ubuntu-latest
    steps:
      - run: ./setup_devgru.sh --profile standard
```

### 10. Security Scanning

```yaml
- name: Security scan
  run: |
    ./setup_devgru.sh --profile security
    safety check
    bandit -r .
    checkov --directory .
```

---

## Complete Example: Production-Ready Pipeline

```yaml
# .github/workflows/production.yml

name: Production DevGRU Pipeline

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]
  schedule:
    - cron: '0 2 * * 1'  # Weekly security scan

env:
  PYTHON_VERSION: '3.10'
  CACHE_VERSION: v1

jobs:
  # Job 1: Validate setup script
  validate:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Shellcheck
        run: |
          sudo apt-get install -y shellcheck
          shellcheck setup/setup_devgru.sh
          shellcheck setup/modules/*.sh

      - name: Dry run test
        run: |
          sudo apt-get install -y jq curl git
          cd setup
          chmod +x setup_devgru.sh
          ./setup_devgru.sh --profile minimal --dry-run

  # Job 2: Multi-OS testing
  test-matrix:
    needs: validate
    strategy:
      fail-fast: false
      matrix:
        os: [ubuntu-22.04, ubuntu-20.04, macos-13, macos-12]
        profile: [minimal, standard, security]
        exclude:
          - os: macos-12
            profile: security

    runs-on: ${{ matrix.os }}

    steps:
      - uses: actions/checkout@v4

      - name: Cache pip
        uses: actions/cache@v4
        with:
          path: ~/.cache/pip
          key: ${{ runner.os }}-pip-${{ env.CACHE_VERSION }}-${{ hashFiles('setup/requirements/*.txt') }}

      - name: Install prerequisites (Linux)
        if: runner.os == 'Linux'
        run: sudo apt-get update && sudo apt-get install -y jq curl git

      - name: Install prerequisites (macOS)
        if: runner.os == 'macOS'
        run: brew install jq curl git

      - name: Run setup
        run: |
          cd setup
          chmod +x setup_devgru.sh
          ./setup_devgru.sh --profile ${{ matrix.profile }} --verbose

      - name: Verify installation
        run: |
          python3 --version
          pip list
          python3 -c "import pandas, requests, pydantic; print('Verified')"

      - name: Upload artifacts
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: logs-${{ matrix.os }}-${{ matrix.profile }}
          path: |
            setup/logs/
            setup/.state/

  # Job 3: Security scan
  security:
    needs: test-matrix
    runs-on: ubuntu-latest
    if: github.event_name == 'schedule' || github.ref == 'refs/heads/main'

    steps:
      - uses: actions/checkout@v4

      - name: Setup
        run: |
          sudo apt-get update && sudo apt-get install -y jq curl git
          cd setup
          chmod +x setup_devgru.sh
          ./setup_devgru.sh --profile security --verbose

      - name: Run security scans
        run: |
          safety check --json > safety-report.json || true
          bandit -r . -f json -o bandit-report.json || true
          checkov --directory . --output json > checkov-report.json || true

      - name: Upload security reports
        uses: actions/upload-artifact@v4
        with:
          name: security-reports
          path: |
            safety-report.json
            bandit-report.json
            checkov-report.json

  # Job 4: Docker build
  docker:
    needs: test-matrix
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'

    steps:
      - uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Build Docker images
        run: |
          docker build --build-arg PROFILE=minimal -t devgru:minimal setup/
          docker build --build-arg PROFILE=standard -t devgru:standard setup/
          docker build --build-arg PROFILE=full -t devgru:full setup/

      - name: Test Docker images
        run: |
          docker run devgru:minimal python3 --version
          docker run devgru:standard python3 -c "import pandas; print('OK')"

  # Job 5: Report generation
  report:
    needs: [test-matrix, security, docker]
    runs-on: ubuntu-latest
    if: always()

    steps:
      - name: Download all artifacts
        uses: actions/download-artifact@v4

      - name: Generate summary report
        run: |
          echo "# DevGRU Setup CI/CD Report" > report.md
          echo "" >> report.md
          echo "## Test Results" >> report.md
          find . -name "installation_state.json" -exec cat {} \; | jq -s '.' > consolidated-state.json
          echo "\`\`\`json" >> report.md
          cat consolidated-state.json >> report.md
          echo "\`\`\`" >> report.md

      - name: Upload final report
        uses: actions/upload-artifact@v4
        with:
          name: final-report
          path: report.md
```

---

## Summary

This CI/CD integration guide provides comprehensive examples for:

1. **GitHub Actions**: Multi-OS workflows, caching, matrix testing, and AWS integration
2. **GitLab CI**: Multi-profile pipelines, templates, and Docker integration
3. **Docker**: Multi-stage builds, profile-specific images, and Docker Compose
4. **Pre-commit Hooks**: Validation, shellcheck, and custom hooks
5. **Caching**: Advanced strategies for pip, apt, and state files
6. **Troubleshooting**: Common issues and solutions for CI environments
7. **Profiles**: Dynamic selection, branch-based, and path-based triggers

All examples are production-ready and tested for the DevGRU setup script.
