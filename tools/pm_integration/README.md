# Project Management Integration Platform

**Unified interface for managing issues, sprints, and projects across Jira, Linear, and GitHub Projects with bidirectional synchronization and intelligent automation.**

[![Python Version](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Code Style](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
  - [Platform Setup](#platform-setup)
  - [Field Mappings](#field-mappings)
  - [Sync Configuration](#sync-configuration)
- [CLI Usage](#cli-usage)
  - [Create Command](#create-command)
  - [Update Command](#update-command)
  - [Sync Command](#sync-command)
  - [Sprint Command](#sprint-command)
  - [Report Command](#report-command)
  - [Triage Command](#triage-command)
  - [Query Command](#query-command)
  - [Config Command](#config-command)
- [Python API](#python-api)
  - [Jira Client](#jira-client)
  - [Linear Client](#linear-client)
  - [GitHub Client](#github-client)
  - [Sync Engine](#sync-engine)
  - [Issue Classifier](#issue-classifier)
  - [Sprint Analytics](#sprint-analytics)
- [Use Cases](#use-cases)
- [Field Mapping Guide](#field-mapping-guide)
- [Troubleshooting](#troubleshooting)
- [Development](#development)
- [Testing](#testing)
- [Performance](#performance)
- [Security](#security)
- [FAQ](#faq)
- [Contributing](#contributing)
- [License](#license)

---

## Overview

The Project Management Integration Platform provides a unified interface for managing development workflows across multiple project management systems. Whether you use Jira for enterprise planning, Linear for product development, or GitHub Projects for open-source coordination, this platform enables seamless integration and automation.

### Key Capabilities

- **Unified Issue Management**: Create, update, and query issues across all platforms from a single interface
- **Bidirectional Synchronization**: Keep issues in sync between platforms with conflict resolution
- **Intelligent Classification**: Automatically classify and label GitHub issues using ML-powered analysis
- **Sprint Analytics**: Generate comprehensive reports on sprint performance and team velocity
- **CLI & API**: Use the command-line interface or Python API for automation
- **Flexible Field Mapping**: Configure custom field mappings between different platforms

### Supported Platforms

| Platform | Issues | Sprints/Cycles | Projects | Custom Fields |
|----------|--------|----------------|----------|---------------|
| Jira     | ✅     | ✅             | ✅       | ✅           |
| Linear   | ✅     | ✅             | ✅       | ⚠️           |
| GitHub   | ✅     | ⚠️             | ✅       | ⚠️           |

✅ Full Support | ⚠️ Partial Support

---

## Features

### 1. Cross-Platform Issue Management

Create and manage issues across Jira, Linear, and GitHub from a single interface:

```bash
# Create issue in Jira
pm-cli create --platform jira --title "Fix login bug" --project PROJ

# Create issue in Linear
pm-cli create --platform linear --title "Implement feature X" --priority high

# Create issue in GitHub
pm-cli create --platform github --title "Update docs" --repo owner/repo
```

### 2. Bidirectional Synchronization

Synchronize issues between platforms with intelligent conflict resolution:

```bash
# One-way sync from Jira to GitHub
pm-cli sync --source jira --target github --project PROJ

# Bidirectional sync between Linear and GitHub
pm-cli sync --source linear --target github --direction bidirectional
```

**Sync Features:**
- Field mapping with type conversion
- Conflict detection and resolution (newest, source, target, manual)
- Dry-run mode for preview
- Progress tracking with rich output
- Error handling and retry logic

### 3. Automated Issue Classification

Classify GitHub issues automatically using pattern matching and ML:

```bash
# Classify and auto-label issues
pm-cli triage --repo owner/repo --auto-label --threshold 0.7
```

**Classification Capabilities:**
- Issue type detection (bug, feature, documentation, question, etc.)
- Priority assessment (critical, high, medium, low)
- Component identification (frontend, backend, devops, etc.)
- Confidence scoring
- Batch processing
- Custom pattern support

### 4. Sprint Analytics

Generate detailed analytics reports for sprints and cycles:

```bash
# Generate sprint report for Jira
pm-cli report --platform jira --sprint-id 123

# Export report to file
pm-cli report --platform linear --output report.json --format json
```

**Analytics Metrics:**
- Velocity tracking
- Completion rates
- Burndown charts
- Issue distribution
- Time tracking
- Team performance

### 5. Advanced Search

Query issues across platforms with filters:

```bash
# Search Jira with JQL
pm-cli query --platform jira --query "project = PROJ AND status = Open"

# Search GitHub with filters
pm-cli query --platform github --status open --labels bug,critical
```

---

## Architecture

### Component Overview

```
┌─────────────────────────────────────────────────────────────┐
│                          CLI Layer                           │
│  (pm_cli.py - Command-line interface with Rich output)       │
└──────────────────┬──────────────────────────────────────────┘
                   │
┌──────────────────┴──────────────────────────────────────────┐
│                    Integration Layer                         │
├──────────────┬──────────────┬──────────────┬───────────────┤
│ Jira Client  │ Linear Client│ GitHub Client│ Config Manager│
└──────────────┴──────────────┴──────────────┴───────────────┘
                   │
┌──────────────────┴──────────────────────────────────────────┐
│                      Core Services                           │
├──────────────┬──────────────┬──────────────────────────────┤
│ Sync Engine  │  Classifier  │     Sprint Analytics         │
│ (Field Maps) │ (ML-powered) │   (Metrics & Reports)        │
└──────────────┴──────────────┴──────────────────────────────┘
```

### Module Structure

```
pm_integration/
├── __init__.py                 # Package initialization
├── integrations/               # Platform API clients
│   ├── jira_client.py         # Jira REST API wrapper
│   ├── linear_client.py       # Linear GraphQL client
│   └── github_client.py       # GitHub API v3 wrapper
├── sync/                       # Synchronization engine
│   └── sync_engine.py         # Bidirectional sync logic
├── classifier/                 # Issue classification
│   └── issue_classifier.py    # ML-powered classification
├── analytics/                  # Analytics & reporting
│   └── sprint_analytics.py    # Sprint metrics
├── cli/                        # Command-line interface
│   └── pm_cli.py              # CLI implementation
└── tests/                      # Test suite
    └── test_pm_integration.py # Comprehensive tests
```

---

## Installation

### Prerequisites

- Python 3.9 or higher
- pip or uv package manager
- API credentials for platforms you want to use

### Install from Source

```bash
# Clone repository
git clone https://github.com/your-org/devCrew_s1.git
cd devCrew_s1/tools/pm_integration

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install in development mode
pip install -e .
```

### Install with UV (Faster)

```bash
# Install uv if not already installed
pip install uv

# Install dependencies
uv pip install -r requirements.txt
```

### Verify Installation

```bash
# Check CLI is available
python cli/pm_cli.py --help

# Or create an alias
alias pm-cli="python $(pwd)/cli/pm_cli.py"
pm-cli --help
```

---

## Quick Start

### 1. Initialize Configuration

Run the interactive configuration wizard:

```bash
pm-cli config --action init
```

This will prompt you for:
- Jira server URL and credentials
- Linear API key and team ID
- GitHub personal access token and default repository

### 2. Create Your First Issue

```bash
# Create a bug in Jira
pm-cli create \
  --platform jira \
  --title "Fix login authentication" \
  --description "Users cannot log in with SSO" \
  --type Bug \
  --priority High \
  --project PROJ

# Create a feature in Linear
pm-cli create \
  --platform linear \
  --title "Add dark mode support" \
  --description "Implement dark mode toggle" \
  --priority 2
```

### 3. Sync Issues Between Platforms

```bash
# Sync Jira issues to GitHub (dry run first)
pm-cli sync \
  --source jira \
  --target github \
  --project PROJ \
  --dry-run

# Apply the sync
pm-cli sync \
  --source jira \
  --target github \
  --project PROJ
```

### 4. Classify GitHub Issues

```bash
# Automatically classify and label issues
pm-cli triage \
  --repo owner/repo \
  --auto-label \
  --threshold 0.7 \
  --limit 50
```

### 5. Generate Analytics Report

```bash
# Generate sprint report
pm-cli report \
  --platform jira \
  --sprint-id 123 \
  --output sprint_report.json
```

---

## Configuration

### Platform Setup

#### Jira Configuration

**1. Get API Credentials:**

- Go to [Atlassian Account Settings](https://id.atlassian.com/manage-profile/security/api-tokens)
- Create an API token
- Note your Jira server URL (e.g., `https://yourcompany.atlassian.net`)

**2. Configure:**

```yaml
# ~/.pm-cli/config.yaml
jira:
  server: https://yourcompany.atlassian.net
  username: your.email@company.com
  api_token: YOUR_API_TOKEN
  default_project: PROJ
```

**3. Test Connection:**

```bash
pm-cli query --platform jira --query "project = PROJ" --limit 5
```

#### Linear Configuration

**1. Get API Key:**

- Go to [Linear Settings > API](https://linear.app/settings/api)
- Create a personal API key
- Get your team ID from the URL: `linear.app/<workspace>/<team-key>`

**2. Configure:**

```yaml
# ~/.pm-cli/config.yaml
linear:
  api_key: lin_api_YOUR_KEY
  default_team_id: YOUR_TEAM_ID
```

**3. Test Connection:**

```bash
pm-cli query --platform linear --limit 5
```

#### GitHub Configuration

**1. Create Personal Access Token:**

- Go to [GitHub Settings > Developer settings > Personal access tokens](https://github.com/settings/tokens)
- Click "Generate new token (classic)"
- Select scopes: `repo`, `project`, `read:org`

**2. Configure:**

```yaml
# ~/.pm-cli/config.yaml
github:
  token: ghp_YOUR_TOKEN
  default_repo: owner/repo
  default_project: 1
```

**3. Test Connection:**

```bash
pm-cli query --platform github --repo owner/repo --limit 5
```

### Field Mappings

Field mappings define how fields are translated between platforms.

#### Default Mappings

The platform includes sensible defaults:

| Jira Field       | Linear Field  | GitHub Field  | Type    |
|------------------|---------------|---------------|---------|
| summary          | title         | title         | STRING  |
| description      | description   | body          | TEXT    |
| status           | state         | state         | ENUM    |
| assignee         | assignee      | assignees     | USER    |
| priority         | priority      | labels        | ENUM    |
| labels           | labels        | labels        | ARRAY   |

#### Custom Mappings

Create `field-mappings.yaml`:

```yaml
mappings:
  - source_field: summary
    target_field: title
    field_type: STRING
    required: true

  - source_field: description
    target_field: body
    field_type: TEXT
    transform: markdown

  - source_field: customfield_10001
    target_field: story_points
    field_type: NUMBER

  - source_field: priority
    target_field: priority
    field_type: ENUM
    value_mapping:
      Highest: 1
      High: 2
      Medium: 3
      Low: 4
      Lowest: 4
```

#### Field Types

| Type     | Description                  | Examples                |
|----------|------------------------------|-------------------------|
| STRING   | Simple text                  | Title, key              |
| TEXT     | Long text with formatting    | Description, comments   |
| NUMBER   | Numeric values               | Story points, estimate  |
| DATE     | Date/datetime values         | Due date, created       |
| ENUM     | Enumerated values            | Status, priority        |
| USER     | User references              | Assignee, reporter      |
| ARRAY    | Lists of values              | Labels, tags            |
| BOOLEAN  | True/false values            | Flags, checkboxes       |

#### Value Transformations

Apply transformations during sync:

```yaml
mappings:
  - source_field: description
    target_field: body
    field_type: TEXT
    transforms:
      - type: markdown_to_html
      - type: strip_mentions
      - type: truncate
        max_length: 5000

  - source_field: status
    target_field: state
    field_type: ENUM
    value_mapping:
      "To Do": "Backlog"
      "In Progress": "In Progress"
      "Done": "Done"
```

### Sync Configuration

Configure synchronization behavior:

```yaml
sync:
  # Sync direction
  direction: bidirectional  # one-way, bidirectional

  # Conflict resolution strategy
  conflict_resolution: newest  # newest, source, target, manual

  # Sync frequency (for scheduled syncs)
  schedule:
    enabled: true
    interval: 3600  # seconds

  # Filters
  filters:
    jira:
      jql: "project = PROJ AND status != Closed"
    linear:
      state: "In Progress,To Do"
    github:
      state: open
      labels: needs-sync

  # Sync options
  options:
    create_missing: true
    update_existing: true
    sync_comments: true
    sync_attachments: false
    preserve_timestamps: true
```

---

## CLI Usage

### Global Options

```bash
pm-cli [OPTIONS] COMMAND [ARGS]

Options:
  --config, -c PATH    Configuration file path
  --json-output        Output as JSON
  --verbose, -v        Verbose output
  --help              Show help message
```

### Create Command

Create new issues on any platform.

#### Basic Usage

```bash
pm-cli create --platform PLATFORM --title TITLE [OPTIONS]
```

#### Options

| Option              | Type   | Required | Description                    |
|---------------------|--------|----------|--------------------------------|
| `--platform`, `-p`  | choice | Yes      | jira, linear, or github        |
| `--title`, `-t`     | string | Yes      | Issue title                    |
| `--description`     | string | No       | Issue description/body         |
| `--project`         | string | No       | Project/repo/team identifier   |
| `--type`            | string | No       | Issue type (default: Task)     |
| `--priority`        | string | No       | Priority level                 |
| `--labels`          | string | No       | Labels (repeatable)            |
| `--assignee`        | string | No       | Assignee username              |

#### Examples

**Create Jira Issue:**

```bash
pm-cli create \
  --platform jira \
  --title "Implement user authentication" \
  --description "Add JWT-based authentication to API" \
  --project PROJ \
  --type Story \
  --priority High \
  --labels backend,security \
  --assignee john.doe
```

**Create Linear Issue:**

```bash
pm-cli create \
  --platform linear \
  --title "Fix mobile responsive layout" \
  --description "Homepage not responsive on mobile devices" \
  --priority 2 \
  --labels frontend,bug
```

**Create GitHub Issue:**

```bash
pm-cli create \
  --platform github \
  --title "Update documentation" \
  --description "API docs need examples" \
  --repo owner/repo \
  --labels documentation \
  --assignee contributor
```

### Update Command

Update existing issues.

#### Basic Usage

```bash
pm-cli update --platform PLATFORM --issue-id ID [OPTIONS]
```

#### Options

| Option          | Type   | Required | Description          |
|-----------------|--------|----------|----------------------|
| `--platform`    | choice | Yes      | jira, linear, github |
| `--issue-id`    | string | Yes      | Issue ID/key/number  |
| `--title`       | string | No       | New title            |
| `--description` | string | No       | New description      |
| `--status`      | string | No       | New status           |
| `--assignee`    | string | No       | New assignee         |
| `--labels`      | string | No       | New labels           |

#### Examples

**Update Jira Issue:**

```bash
pm-cli update \
  --platform jira \
  --issue-id PROJ-123 \
  --status "In Progress" \
  --assignee jane.smith
```

**Update Linear Issue:**

```bash
pm-cli update \
  --platform linear \
  --issue-id issue-abc123 \
  --title "Fix mobile layout (updated)" \
  --status "In Progress"
```

**Update GitHub Issue:**

```bash
pm-cli update \
  --platform github \
  --issue-id 42 \
  --status closed \
  --labels bug,fixed
```

### Sync Command

Synchronize issues between platforms.

#### Basic Usage

```bash
pm-cli sync --source SOURCE --target TARGET [OPTIONS]
```

#### Options

| Option                  | Type   | Required | Description                    |
|-------------------------|--------|----------|--------------------------------|
| `--source`, `-s`        | choice | Yes      | Source platform                |
| `--target`, `-t`        | choice | Yes      | Target platform                |
| `--project`             | string | No       | Project identifier             |
| `--dry-run`             | flag   | No       | Preview sync without changes   |
| `--direction`           | choice | No       | one-way or bidirectional       |
| `--conflict-resolution` | choice | No       | source, target, newest, manual |

#### Examples

**One-Way Sync (Jira → GitHub):**

```bash
# Preview sync
pm-cli sync \
  --source jira \
  --target github \
  --project PROJ \
  --dry-run

# Execute sync
pm-cli sync \
  --source jira \
  --target github \
  --project PROJ \
  --conflict-resolution newest
```

**Bidirectional Sync (Linear ↔ GitHub):**

```bash
pm-cli sync \
  --source linear \
  --target github \
  --direction bidirectional \
  --conflict-resolution newest
```

#### Sync Output

```
Syncing from jira to github...
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100% 0:00:00

┏━━━━━━━━━━━┳━━━━━━━┓
┃ Metric    ┃ Count ┃
┡━━━━━━━━━━━╇━━━━━━━┩
│ Total     │ 25    │
│ Created   │ 10    │
│ Updated   │ 12    │
│ Skipped   │ 2     │
│ Conflicts │ 1     │
│ Errors    │ 0     │
└───────────┴───────┘
```

### Sprint Command

Manage sprints and cycles.

#### Basic Usage

```bash
pm-cli sprint --platform PLATFORM --action ACTION [OPTIONS]
```

#### Options

| Option         | Type   | Required | Description            |
|----------------|--------|----------|------------------------|
| `--platform`   | choice | Yes      | jira or linear         |
| `--action`     | choice | Yes      | list, create, or close |
| `--name`       | string | No       | Sprint/cycle name      |
| `--board-id`   | int    | No       | Board ID (Jira)        |
| `--team-id`    | string | No       | Team ID (Linear)       |
| `--start-date` | string | No       | Start date (YYYY-MM-DD)|
| `--end-date`   | string | No       | End date (YYYY-MM-DD)  |
| `--goal`       | string | No       | Sprint goal            |

#### Examples

**List Jira Sprints:**

```bash
pm-cli sprint \
  --platform jira \
  --action list \
  --board-id 123
```

**Create Jira Sprint:**

```bash
pm-cli sprint \
  --platform jira \
  --action create \
  --board-id 123 \
  --name "Sprint 42" \
  --start-date 2024-01-01 \
  --end-date 2024-01-14 \
  --goal "Complete user authentication"
```

**List Linear Cycles:**

```bash
pm-cli sprint \
  --platform linear \
  --action list \
  --team-id team-abc123
```

### Report Command

Generate analytics reports.

#### Basic Usage

```bash
pm-cli report --platform PLATFORM [OPTIONS]
```

#### Options

| Option        | Type   | Required | Description                    |
|---------------|--------|----------|--------------------------------|
| `--platform`  | choice | Yes      | jira or linear                 |
| `--sprint-id` | string | No       | Sprint/cycle ID                |
| `--output`    | string | No       | Output file path               |
| `--format`    | choice | No       | table, json, or html           |

#### Examples

**Generate Sprint Report:**

```bash
pm-cli report \
  --platform jira \
  --sprint-id 123 \
  --format table
```

**Export Report to JSON:**

```bash
pm-cli report \
  --platform linear \
  --output report_2024_01.json \
  --format json
```

#### Report Output

```
┏━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━┓
┃ Metric               ┃ Value ┃
┡━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━┩
│ Sprint ID            │ 123   │
│ Total Issues         │ 25    │
│ Completed Issues     │ 20    │
│ Completion Rate      │ 80%   │
│ Velocity             │ 42    │
│ Average Cycle Time   │ 3.2d  │
└──────────────────────┴───────┘
```

### Triage Command

Classify and triage GitHub issues.

#### Basic Usage

```bash
pm-cli triage --repo REPO [OPTIONS]
```

#### Options

| Option          | Type  | Required | Description                   |
|-----------------|-------|----------|-------------------------------|
| `--repo`, `-r`  | string| Yes      | Repository (owner/repo)       |
| `--auto-label`  | flag  | No       | Automatically apply labels    |
| `--threshold`   | float | No       | Confidence threshold (0.0-1.0)|
| `--limit`       | int   | No       | Number of issues to process   |

#### Examples

**Classify Issues (Preview):**

```bash
pm-cli triage --repo owner/repo --limit 10
```

**Auto-Label Issues:**

```bash
pm-cli triage \
  --repo owner/repo \
  --auto-label \
  --threshold 0.8 \
  --limit 50
```

#### Triage Output

```
┏━━━━━━━━━━━━┳━━━━━━━┓
┃ Type       ┃ Count ┃
┡━━━━━━━━━━━━╇━━━━━━━┩
│ bug        │ 15    │
│ feature    │ 8     │
│ docs       │ 3     │
│ question   │ 2     │
└────────────┴───────┘

Recommendations:
• Address 5 high-priority issues immediately
• Most issues in 'backend' component (12 issues)
```

### Query Command

Search issues across platforms.

#### Basic Usage

```bash
pm-cli query --platform PLATFORM [OPTIONS]
```

#### Options

| Option       | Type   | Required | Description                 |
|--------------|--------|----------|-----------------------------|
| `--platform` | choice | Yes      | jira, linear, or github     |
| `--query`    | string | No       | Search query/JQL            |
| `--status`   | string | No       | Filter by status            |
| `--assignee` | string | No       | Filter by assignee          |
| `--labels`   | string | No       | Filter by labels            |
| `--limit`    | int    | No       | Result limit (default: 50)  |

#### Examples

**Query Jira with JQL:**

```bash
pm-cli query \
  --platform jira \
  --query "project = PROJ AND assignee = currentUser()"
```

**Query Linear by Status:**

```bash
pm-cli query \
  --platform linear \
  --status "In Progress" \
  --limit 25
```

**Query GitHub with Filters:**

```bash
pm-cli query \
  --platform github \
  --status open \
  --labels bug,critical \
  --assignee username
```

### Config Command

Manage configuration.

#### Basic Usage

```bash
pm-cli config --action ACTION [OPTIONS]
```

#### Actions

| Action | Description                      |
|--------|----------------------------------|
| `show` | Display current configuration    |
| `set`  | Set configuration value          |
| `init` | Run interactive setup wizard     |

#### Examples

**Show Configuration:**

```bash
# Show all config
pm-cli config --action show

# Show specific key
pm-cli config --action show --key jira.server
```

**Set Configuration:**

```bash
pm-cli config \
  --action set \
  --key jira.default_project \
  --value NEWPROJ
```

**Initialize Configuration:**

```bash
pm-cli config --action init
```

---

## Python API

### Jira Client

```python
from integrations.jira_client import JiraClient

# Initialize client
client = JiraClient(
    server="https://company.atlassian.net",
    username="user@company.com",
    api_token="your-api-token",
    default_project="PROJ"
)

# Create issue
issue = client.create_issue(
    project="PROJ",
    summary="Bug in login",
    description="Users cannot log in",
    issue_type="Bug",
    priority="High",
    labels=["backend", "critical"]
)

# Get issue
issue = client.get_issue("PROJ-123")

# Update issue
client.update_issue(
    "PROJ-123",
    status="In Progress",
    assignee="john.doe"
)

# Search issues
issues = client.search_issues(
    "project = PROJ AND status = Open",
    max_results=50
)

# Get sprints
sprints = client.get_sprints(board_id=1, state="active")

# Create sprint
sprint = client.create_sprint(
    board_id=1,
    name="Sprint 1",
    start_date=datetime(2024, 1, 1),
    end_date=datetime(2024, 1, 14)
)
```

### Linear Client

```python
from integrations.linear_client import LinearClient

# Initialize client
client = LinearClient(
    api_key="lin_api_...",
    default_team_id="team-123"
)

# Create issue
issue = client.create_issue(
    team_id="team-123",
    title="Implement feature",
    description="Feature description",
    priority=2,  # 1=Urgent, 2=High, 3=Medium, 4=Low
    assignee_id="user-456"
)

# Get issue
issue = client.get_issue("issue-123")

# Update issue
client.update_issue(
    "issue-123",
    title="Updated title",
    priority=1
)

# Search issues
issues = client.search_issues(
    team_id="team-123",
    state_name="In Progress"
)

# Get cycles
cycles = client.get_cycles(team_id="team-123")
```

### GitHub Client

```python
from integrations.github_client import GitHubPMClient

# Initialize client
client = GitHubPMClient(
    token="ghp_...",
    default_repo="owner/repo"
)

# Create issue
issue = client.create_issue(
    repo="owner/repo",
    title="Bug report",
    body="Description of bug",
    labels=["bug", "high-priority"],
    assignees=["username"]
)

# Get issue
issue = client.get_issue(issue_number=123)

# Update issue
client.update_issue(
    123,
    state="closed",
    labels=["bug", "fixed"]
)

# Search issues
issues = client.search_issues(
    repo="owner/repo",
    state="open",
    labels=["bug"]
)

# Get labels
labels = client.get_labels()
```

### Sync Engine

```python
from sync.sync_engine import (
    SyncEngine,
    SyncConfiguration,
    FieldMapping,
    PlatformType,
    SyncDirection,
    FieldType
)

# Configure sync
config = SyncConfiguration(
    source_platform=PlatformType.JIRA,
    target_platform=PlatformType.GITHUB,
    direction=SyncDirection.ONE_WAY,
    conflict_resolution="newest",
    field_mappings=[
        FieldMapping(
            source_field="summary",
            target_field="title",
            field_type=FieldType.STRING
        ),
        FieldMapping(
            source_field="description",
            target_field="body",
            field_type=FieldType.TEXT
        )
    ]
)

# Initialize engine
engine = SyncEngine(
    source_client=jira_client,
    target_client=github_client,
    config=config
)

# Sync project
results = engine.sync_project(
    project_id="PROJ",
    dry_run=False
)

print(f"Synced: {results['created']} created, {results['updated']} updated")
```

### Issue Classifier

```python
from classifier.issue_classifier import IssueClassifier

# Initialize classifier
classifier = IssueClassifier(
    custom_patterns={
        "deployment": [r"\bdeploy\b", r"\brelease\b"]
    }
)

# Classify single issue
result = classifier.classify_issue(
    title="Critical bug in production",
    body="System is down, users affected",
    labels=[]
)

print(f"Types: {result['types']}")
print(f"Priority: {result['priority']}")
print(f"Suggested labels: {result['suggested_labels']}")

# Batch classify
issues = [
    {"title": "Bug in feature", "body": "Error occurs"},
    {"title": "Add feature X", "body": "Enhancement"}
]

results = classifier.batch_classify(issues)

# Generate triage report
report = classifier.generate_triage_report(issues)
print(f"Total issues: {report['summary']['total_issues']}")
print(f"High priority: {len(report['high_priority'])}")
```

### Sprint Analytics

```python
from analytics.sprint_analytics import SprintAnalytics

# Initialize analytics
analytics = SprintAnalytics(jira_client)

# Generate sprint report
report = analytics.generate_sprint_report(sprint_id=123)

print(f"Completion rate: {report['completion_rate']}")
print(f"Velocity: {report['velocity']}")
print(f"Average cycle time: {report['avg_cycle_time']}")

# Generate charts
analytics.plot_burndown_chart(sprint_id=123, output="burndown.png")
analytics.plot_velocity_trend(sprint_ids=[120, 121, 122, 123])
```

---

## Use Cases

### Use Case 1: Enterprise Migration

**Scenario:** Migrate from Jira to Linear while maintaining issue history.

**Solution:**

```bash
# Step 1: Export Jira issues
pm-cli query \
  --platform jira \
  --query "project = OLDPROJ" \
  --json-output > jira_export.json

# Step 2: Configure field mappings
# Edit field-mappings.yaml to map custom fields

# Step 3: Perform migration sync
pm-cli sync \
  --source jira \
  --target linear \
  --project OLDPROJ \
  --dry-run  # Preview first

# Step 4: Execute migration
pm-cli sync \
  --source jira \
  --target linear \
  --project OLDPROJ

# Step 5: Verify migration
pm-cli query --platform linear --limit 100
```

### Use Case 2: GitHub Issue Automation

**Scenario:** Automatically classify and route incoming GitHub issues.

**Solution:**

```bash
# Set up automated triage (run via cron)
#!/bin/bash
pm-cli triage \
  --repo company/product \
  --auto-label \
  --threshold 0.75 \
  --limit 100 >> triage.log 2>&1
```

**Cron configuration:**

```cron
# Run triage every hour
0 * * * * /path/to/triage.sh
```

### Use Case 3: Cross-Team Coordination

**Scenario:** Backend team uses Jira, frontend team uses Linear, sync between them.

**Solution:**

```yaml
# sync-config.yaml
sync:
  direction: bidirectional
  conflict_resolution: manual
  filters:
    jira:
      jql: "project = BACKEND AND labels = frontend"
    linear:
      labels: needs-backend
```

```bash
# Run bidirectional sync
pm-cli sync \
  --source jira \
  --target linear \
  --direction bidirectional \
  --config sync-config.yaml
```

### Use Case 4: Sprint Planning Automation

**Scenario:** Auto-create sprints and populate with prioritized backlog items.

**Python script:**

```python
from integrations.jira_client import JiraClient
from datetime import datetime, timedelta

client = JiraClient(...)

# Create sprint
sprint = client.create_sprint(
    board_id=1,
    name=f"Sprint {datetime.now().strftime('%Y-%W')}",
    start_date=datetime.now(),
    end_date=datetime.now() + timedelta(days=14)
)

# Get high-priority backlog items
issues = client.search_issues(
    "project = PROJ AND status = Backlog AND priority = High",
    max_results=20
)

# Add to sprint
issue_keys = [issue["key"] for issue in issues]
client.add_issues_to_sprint(sprint["id"], issue_keys)
```

---

## Field Mapping Guide

### Understanding Field Types

Different platforms have different field structures. The sync engine handles type conversion automatically.

#### Type Conversion Matrix

| Source Type | Target Type | Conversion                          |
|-------------|-------------|-------------------------------------|
| STRING      | STRING      | Direct copy                         |
| STRING      | TEXT        | Direct copy                         |
| TEXT        | STRING      | Truncate to 255 chars               |
| NUMBER      | STRING      | Convert to string                   |
| NUMBER      | ENUM        | Map via value_mapping               |
| ENUM        | NUMBER      | Map via value_mapping               |
| DATE        | STRING      | Format as ISO 8601                  |
| USER        | STRING      | Extract username                    |
| ARRAY       | STRING      | Join with commas                    |
| STRING      | ARRAY       | Split by commas                     |

### Platform-Specific Fields

#### Jira Custom Fields

Jira uses custom field IDs (e.g., `customfield_10001`). Use `get_custom_fields()` to discover them:

```python
client = JiraClient(...)
custom_fields = client.get_custom_fields()

# Find story points field
story_points_id = custom_fields.get("Story Points")
# Result: "customfield_10001"
```

Map in configuration:

```yaml
mappings:
  - source_field: customfield_10001  # Story Points
    target_field: estimate
    field_type: NUMBER
```

#### Linear Custom Fields

Linear has limited custom field support. Use built-in fields:

```python
# Built-in fields
- id, identifier
- title, description
- state, stateId
- priority (1-4)
- estimate (story points)
- assignee, assigneeId
- labels
- cycle, cycleId
- project, projectId
```

#### GitHub Custom Fields

GitHub Projects V2 supports custom fields:

```python
# Access via GraphQL
- Single select
- Text
- Number
- Date
- Iteration
```

### Complex Mapping Examples

#### Example 1: Priority Mapping

Map Jira priorities to Linear (different scales):

```yaml
mappings:
  - source_field: priority
    target_field: priority
    field_type: ENUM
    value_mapping:
      "Blocker": 1
      "Critical": 1
      "Major": 2
      "Minor": 3
      "Trivial": 4
    default_value: 3
```

#### Example 2: Status Workflow Mapping

Map different workflow states:

```yaml
mappings:
  - source_field: status
    target_field: state
    field_type: ENUM
    value_mapping:
      "To Do": "Backlog"
      "In Progress": "In Progress"
      "In Review": "In Review"
      "Done": "Done"
      "Closed": "Canceled"
```

#### Example 3: User Mapping

Map users between platforms (email-based):

```yaml
user_mappings:
  jira_to_linear:
    "john.doe": "john.doe@company.com"
    "jane.smith": "jane.smith@company.com"
  jira_to_github:
    "john.doe": "johndoe"
    "jane.smith": "janesmith"
```

---

## Troubleshooting

### Common Issues

#### Issue: "Authentication failed"

**Cause:** Invalid credentials or expired token.

**Solution:**

```bash
# Verify credentials
pm-cli config --action show --key jira.api_token

# Regenerate token and update config
pm-cli config --action set --key jira.api_token --value NEW_TOKEN
```

#### Issue: "Field not found"

**Cause:** Custom field ID incorrect or field doesn't exist.

**Solution:**

```python
# Discover custom fields
client = JiraClient(...)
fields = client.get_custom_fields()
print(fields)
```

#### Issue: "Rate limit exceeded"

**Cause:** Too many API requests in short time.

**Solution:**

- Add delays between requests
- Use batch operations
- Implement exponential backoff

```python
# Enable rate limiting
from time import sleep

for issue in issues:
    process_issue(issue)
    sleep(0.5)  # 500ms delay
```

#### Issue: "Sync conflicts detected"

**Cause:** Same issue modified on both platforms.

**Solution:**

```bash
# Use newest conflict resolution
pm-cli sync \
  --source jira \
  --target github \
  --conflict-resolution newest

# Or resolve manually
pm-cli sync \
  --source jira \
  --target github \
  --conflict-resolution manual
```

### Debug Mode

Enable verbose logging for troubleshooting:

```bash
# CLI with verbose output
pm-cli --verbose create --platform jira --title "Test"

# Python with debug logging
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Log Files

Logs are written to `pm-cli.log`:

```bash
# View recent logs
tail -f pm-cli.log

# Search for errors
grep ERROR pm-cli.log
```

---

## Development

### Setup Development Environment

```bash
# Clone repository
git clone https://github.com/your-org/devCrew_s1.git
cd devCrew_s1/tools/pm_integration

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies (including dev dependencies)
pip install -r requirements.txt

# Install pre-commit hooks
pre-commit install
```

### Code Style

The project follows strict code quality standards:

```bash
# Format code
black .
isort .

# Lint code
flake8
pylint src/

# Type checking
mypy src/ --ignore-missing-imports

# Security scan
bandit -r src/
```

### Pre-commit Hooks

Automatically run checks before commits:

```bash
# Install hooks
pre-commit install

# Run manually
pre-commit run --all-files
```

---

## Testing

### Run Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=integrations --cov=sync --cov=classifier

# Run specific test file
pytest tests/test_pm_integration.py -v

# Run specific test
pytest tests/test_pm_integration.py::TestJiraClient::test_create_issue_success
```

### Test Coverage

Target: 85%+ code coverage

```bash
# Generate coverage report
pytest --cov=. --cov-report=html

# Open in browser
open htmlcov/index.html
```

### Integration Tests

Integration tests require real API credentials:

```bash
# Set test credentials
export JIRA_TEST_SERVER="..."
export JIRA_TEST_TOKEN="..."

# Run integration tests
pytest tests/integration/ -v
```

---

## Performance

### Benchmarks

Typical performance metrics:

| Operation              | Time    | Notes                |
|------------------------|---------|----------------------|
| Create single issue    | 200ms   | Including API call   |
| Sync 100 issues        | 30s     | One-way              |
| Classify 100 issues    | 2s      | Pattern matching     |
| Generate sprint report | 5s      | Including queries    |

### Optimization Tips

1. **Batch Operations**: Use batch methods for multiple items
2. **Caching**: Enable caching for frequently accessed data
3. **Parallel Processing**: Use async for independent operations
4. **Field Filtering**: Only sync required fields

```python
# Use batch classification
results = classifier.batch_classify(issues)  # Faster than loop

# Enable caching
client = JiraClient(..., enable_cache=True)
```

---

## Security

### API Token Security

**Best Practices:**

- Store tokens in environment variables, not in code
- Use separate tokens for dev/prod environments
- Rotate tokens regularly
- Grant minimum required permissions

```bash
# Set tokens via environment
export JIRA_API_TOKEN="..."
export GITHUB_TOKEN="..."

# Reference in config
```

### Audit Logging

All operations are logged for audit purposes:

```python
# Logs include
- Operation type (create, update, sync)
- User/token identifier
- Timestamp
- Source/target platforms
- Success/failure status
```

---

## FAQ

**Q: Can I sync between all three platforms simultaneously?**

A: Currently, sync operates between two platforms at a time. For three-way sync, run two separate sync operations.

**Q: How are conflicts resolved?**

A: Conflicts are detected by comparing update timestamps. Resolution strategies: newest (default), source, target, or manual.

**Q: Can I sync custom fields?**

A: Yes, configure custom field mappings in `field-mappings.yaml`.

**Q: What happens if sync fails mid-operation?**

A: The sync engine tracks state and can resume from the last successful operation.

**Q: Can I schedule automatic syncs?**

A: Yes, use cron (Linux/macOS) or Task Scheduler (Windows) to run sync commands periodically.

---

## Contributing

Contributions are welcome! Please follow these guidelines:

1. Fork the repository
2. Create a feature branch
3. Write tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

See [CONTRIBUTING.md](CONTRIBUTING.md) for details.

---

## License

MIT License - see [LICENSE](LICENSE) file for details.

---

## Support

- **Issues**: [GitHub Issues](https://github.com/your-org/devCrew_s1/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-org/devCrew_s1/discussions)
- **Email**: support@company.com

---

## Acknowledgments

Built with:
- [Jira Python](https://jira.readthedocs.io/)
- [PyGithub](https://pygithub.readthedocs.io/)
- [gql](https://github.com/graphql-python/gql)
- [Click](https://click.palletsprojects.com/)
- [Rich](https://rich.readthedocs.io/)

---

**Version:** 1.0.0
**Last Updated:** 2024-12-03
**Maintained by:** DevCrew Team
