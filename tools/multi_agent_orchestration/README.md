# Multi-Agent Orchestration Platform

**Tool ID:** TOOL-ORG-001
**Version:** 1.0.0
**Issue:** [#46](https://github.com/Cybonto/devCrew_s1/issues/46)

A comprehensive platform for orchestrating multi-agent workflows with intelligent task delegation, resource management, and hierarchical coordination patterns. Built on Prefect for workflow orchestration and Redis for distributed state management.

---

## Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [Architecture](#architecture)
- [Technology Stack](#technology-stack)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Usage Examples](#usage-examples)
  - [Python API](#python-api)
  - [CLI](#cli)
- [Workflow Templates](#workflow-templates)
- [Protocol Integration](#protocol-integration)
- [API Reference](#api-reference)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)
- [Performance](#performance)
- [Development](#development)
- [License](#license)

---

## Overview

The Multi-Agent Orchestration Platform enables complex, distributed workflows involving multiple specialized AI agents. It provides intelligent task routing, resource allocation, context preservation during agent handoffs, and hierarchical coordination patterns.

### What It Does

- **Task Orchestration**: Coordinate multi-step workflows with dependency management and parallel execution
- **Intelligent Delegation**: Route tasks to agents based on capability matching and load balancing
- **Resource Management**: Track and allocate CPU, memory, and concurrent task resources across agents
- **Hub-and-Spoke Coordination**: Decompose high-level objectives into sub-tasks with hierarchical coordination
- **Context Preservation**: Seamlessly transfer execution context between agents with validation
- **Workflow Templates**: Pre-built patterns for TDD, feature development, and bug fixing
- **CLI Interface**: Command-line tools for workflow management and monitoring

### Key Features

| Feature | Description |
|---------|-------------|
| **Prefect-Based Orchestration** | Leverage Prefect's robust workflow engine for task scheduling and execution |
| **Capability-Based Routing** | Match tasks to agents based on required skills and current availability |
| **Distributed State Management** | Redis-backed state tracking with automatic agent TTL and heartbeat monitoring |
| **Resource Allocation** | Priority-based resource allocation with deadlock detection and preemption |
| **Audit Trail** | Complete PostgreSQL-backed transaction log for all handoffs and delegations |
| **Conditional Workflows** | Support for branching logic, dynamic task generation, and parallel execution |
| **Agent Handoffs** | Preserve conversation history, file changes, and state during agent transfers |
| **Load Balancing** | Intelligent agent selection considering current load and priority weights |

---

## Architecture

### System Components

```
┌─────────────────────────────────────────────────────────────────┐
│                    Multi-Agent Orchestration Platform            │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────┐        ┌──────────────┐      ┌─────────────┐ │
│  │   Workflow   │        │   Task       │      │  Delegation  │ │
│  │   Engine     │───────▶│ Orchestrator │◀────▶│   Manager   │ │
│  │              │        │  (Prefect)   │      │             │ │
│  └──────────────┘        └──────────────┘      └─────────────┘ │
│         │                        │                      │        │
│         │                        │                      │        │
│         ▼                        ▼                      ▼        │
│  ┌──────────────┐        ┌──────────────┐      ┌─────────────┐ │
│  │   Hub-Spoke  │        │   Resource   │      │   Handoff   │ │
│  │ Coordinator  │        │  Allocator   │      │   Manager   │ │
│  │              │        │              │      │             │ │
│  └──────────────┘        └──────────────┘      └─────────────┘ │
│         │                        │                      │        │
└─────────┼────────────────────────┼──────────────────────┼────────┘
          │                        │                      │
          ▼                        ▼                      ▼
    ┌──────────┐           ┌──────────┐          ┌──────────────┐
    │  Celery  │           │  Redis   │          │ PostgreSQL   │
    │  Tasks   │           │  State   │          │ Audit Trail  │
    └──────────┘           └──────────┘          └──────────────┘
```

### Data Flow

1. **Workflow Creation**: User defines workflow with tasks and dependencies
2. **Task Orchestration**: Prefect manages task scheduling and execution order
3. **Agent Selection**: Delegation Manager finds best agent based on capabilities
4. **Resource Allocation**: Resource Allocator reserves CPU/memory for task
5. **Task Execution**: Agent executes task with allocated resources
6. **Context Transfer**: Handoff Manager preserves context for next agent
7. **Result Aggregation**: Hub-Spoke Coordinator combines spoke results

### Component Interactions

```
┌───────────┐
│  User/API │
└─────┬─────┘
      │
      ▼
┌─────────────────┐
│ Workflow Engine │──────┐
└────────┬────────┘      │
         │               │
         ▼               ▼
  ┌─────────────┐  ┌──────────────┐
  │Orchestrator │  │Hub-Spoke     │
  └──────┬──────┘  │Coordinator   │
         │         └──────┬───────┘
         ▼                │
  ┌─────────────┐        │
  │ Delegation  │◀───────┘
  │  Manager    │
  └──────┬──────┘
         │
         ├───────────┐
         ▼           ▼
  ┌──────────┐  ┌──────────┐
  │Resource  │  │ Handoff  │
  │Allocator │  │ Manager  │
  └──────────┘  └──────────┘
         │           │
         ▼           ▼
    ┌────────────────────┐
    │  Agent Execution   │
    └────────────────────┘
```

---

## Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Workflow Engine** | Prefect 2.14.9 | Task orchestration and scheduling |
| **Task Queue** | Celery 5.3.4 | Distributed task execution |
| **State Store** | Redis 5.0.1 | Agent registry and state management |
| **Audit Database** | PostgreSQL | Handoff transaction log |
| **Data Validation** | Pydantic 2.5.3 | Model validation and serialization |
| **CLI** | Click 8.1.7 | Command-line interface |
| **Message Broker** | Redis/RabbitMQ | Task message routing |

---

## Installation

### Prerequisites

- **Python**: 3.10 or higher
- **Redis**: 5.0 or higher
- **PostgreSQL**: 12 or higher (optional, for handoff audit trail)
- **Operating System**: Linux, macOS, or Windows

### Step 1: Install Redis

**macOS:**
```bash
brew install redis
brew services start redis
```

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install redis-server
sudo systemctl start redis-server
sudo systemctl enable redis-server
```

**Verify Redis:**
```bash
redis-cli ping
# Should output: PONG
```

### Step 2: Install PostgreSQL (Optional)

**macOS:**
```bash
brew install postgresql@14
brew services start postgresql@14
```

**Ubuntu/Debian:**
```bash
sudo apt-get install postgresql postgresql-contrib
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

**Create Database:**
```bash
sudo -u postgres psql
CREATE DATABASE multi_agent_platform;
CREATE USER orchestrator WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE multi_agent_platform TO orchestrator;
\q
```

### Step 3: Install Python Dependencies

```bash
# Clone the repository
cd /path/to/devCrew_s1/tools/multi_agent_orchestration

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Step 4: Configuration

Create configuration file:

```bash
mkdir -p ~/.devcrew
cat > ~/.devcrew/config.yaml << EOF
# Redis Configuration
redis_url: redis://localhost:6379
redis_db: 0

# PostgreSQL Configuration (optional)
postgres_host: localhost
postgres_port: 5432
postgres_db: multi_agent_platform
postgres_user: orchestrator
postgres_password: your_secure_password
EOF
```

### Step 5: Verify Installation

```bash
# Test Redis connection
python -c "import redis; r = redis.from_url('redis://localhost:6379'); print(r.ping())"

# Test platform imports
python -c "from task_orchestrator import TaskOrchestrator; from delegation_manager import DelegationManager; print('✓ Platform ready')"
```

---

## Quick Start

### Basic Workflow Example

```python
from task_orchestrator import TaskOrchestrator, Workflow, Task
from delegation_manager import DelegationManager

# Initialize components
orchestrator = TaskOrchestrator(redis_url="redis://localhost:6379")
delegation_manager = DelegationManager(redis_url="redis://localhost:6379")

# Register agents
delegation_manager.register_agent(
    agent_id="backend-dev-001",
    agent_type="Backend-Engineer",
    capabilities=["python", "api-development", "testing"],
    max_concurrent_tasks=3,
    priority_weight=15
)

delegation_manager.register_agent(
    agent_id="qa-tester-001",
    agent_type="QA-Tester",
    capabilities=["testing", "pytest", "quality-assurance"],
    max_concurrent_tasks=5,
    priority_weight=10
)

# Create workflow
workflow = Workflow(
    workflow_id="feature-dev-001",
    name="Feature Development Workflow",
    priority="high"
)

# Add tasks with dependencies
test_task = Task(
    task_id="write-tests",
    agent_type="QA-Tester",
    agent_capabilities=["testing", "pytest"],
    input_data={
        "action": "write_tests",
        "feature": "user_authentication"
    },
    timeout=900
)

impl_task = Task(
    task_id="implement-feature",
    agent_type="Backend-Engineer",
    agent_capabilities=["python", "api-development"],
    input_data={
        "action": "implement_feature",
        "feature": "user_authentication"
    },
    depends_on=["write-tests"],  # Wait for tests
    timeout=1800
)

workflow.add_task(test_task)
workflow.add_task(impl_task)

# Execute workflow
orchestrator.create_workflow(workflow)
result = orchestrator.execute_workflow("feature-dev-001")

print(f"Workflow Status: {result['status']}")
print(f"Tasks Completed: {result['tasks_completed']}")
print(f"Duration: {result['duration_seconds']}s")
```

### CLI Quick Start

```bash
# Create workflow from YAML file
devcrew workflow create --file workflow.yaml

# Start workflow execution
devcrew workflow start --id feature-dev-001

# Monitor workflow status
devcrew workflow status --id feature-dev-001

# List all agents
devcrew agent list

# Check agent capacity
devcrew agent status --id backend-dev-001
```

---

## Configuration

### Environment Variables

```bash
# Redis Configuration
export REDIS_URL="redis://localhost:6379"
export REDIS_DB="0"

# PostgreSQL Configuration
export POSTGRES_HOST="localhost"
export POSTGRES_PORT="5432"
export POSTGRES_DB="multi_agent_platform"
export POSTGRES_USER="orchestrator"
export POSTGRES_PASSWORD="your_secure_password"

# Platform Settings
export DEVCREW_CONFIG="~/.devcrew/config.yaml"
export DEVCREW_LOG_LEVEL="INFO"
```

### Configuration File Format

**Location**: `~/.devcrew/config.yaml`

```yaml
# Redis State Store
redis_url: redis://localhost:6379
redis_db: 0
redis_password: null  # Optional

# PostgreSQL Audit Database (optional)
postgres_host: localhost
postgres_port: 5432
postgres_db: multi_agent_platform
postgres_user: orchestrator
postgres_password: your_secure_password

# Platform Settings
agent_ttl_seconds: 300  # Agent registration TTL
agent_heartbeat_interval: 60  # Heartbeat frequency
task_timeout_default: 3600  # Default task timeout
workflow_timeout_default: 7200  # Default workflow timeout

# Resource Limits
default_cpu_cores: 2
default_memory_mb: 2048
default_max_concurrent_tasks: 3

# Celery Configuration (for hub-spoke)
celery_broker_url: redis://localhost:6379/1
celery_result_backend: redis://localhost:6379/2
celery_task_serializer: json
celery_result_serializer: json
```

### Redis Connection Settings

```python
from delegation_manager import DelegationManager

# Basic connection
manager = DelegationManager(redis_url="redis://localhost:6379")

# With password
manager = DelegationManager(
    redis_url="redis://:password@localhost:6379",
    redis_db=0
)

# With connection pool
manager = DelegationManager(
    redis_url="redis://localhost:6379",
    connection_pool_size=20
)
```

### PostgreSQL Connection Settings

```python
from handoff_manager import HandoffManager
import redis

redis_client = redis.from_url("redis://localhost:6379", decode_responses=True)

postgres_config = {
    "host": "localhost",
    "port": 5432,
    "database": "multi_agent_platform",
    "user": "orchestrator",
    "password": "your_secure_password",
    "minconn": 1,
    "maxconn": 10
}

handoff_manager = HandoffManager(
    redis_client=redis_client,
    postgres_config=postgres_config
)
```

---

## Usage Examples

### Python API

#### 1. Create and Execute Workflows

```python
from task_orchestrator import TaskOrchestrator, Workflow, Task

orchestrator = TaskOrchestrator(redis_url="redis://localhost:6379")

# Define workflow
workflow = Workflow(
    workflow_id="data-pipeline-001",
    name="Data Processing Pipeline",
    priority="high",
    timeout=7200
)

# Add parallel tasks
extract_task = Task(
    task_id="extract-data",
    agent_type="Data-Engineer",
    agent_capabilities=["data-extraction", "etl"],
    input_data={
        "source": "postgresql://data-warehouse",
        "query": "SELECT * FROM raw_events WHERE date >= '2025-01-01'"
    },
    timeout=1800
)

# Transform depends on extract
transform_task = Task(
    task_id="transform-data",
    agent_type="Data-Engineer",
    agent_capabilities=["data-transformation", "pandas"],
    input_data={
        "transformations": ["normalize", "deduplicate", "aggregate"]
    },
    depends_on=["extract-data"],
    timeout=3600
)

# Load depends on transform
load_task = Task(
    task_id="load-data",
    agent_type="Data-Engineer",
    agent_capabilities=["data-loading", "etl"],
    input_data={
        "destination": "postgresql://analytics",
        "table": "processed_events"
    },
    depends_on=["transform-data"],
    timeout=1800
)

workflow.add_task(extract_task)
workflow.add_task(transform_task)
workflow.add_task(load_task)

# Execute
orchestrator.create_workflow(workflow)
result = orchestrator.execute_workflow("data-pipeline-001")

print(f"Workflow completed: {result['status']}")
print(f"Started: {result['started_at']}")
print(f"Completed: {result['completed_at']}")
print(f"Duration: {result['duration_seconds']} seconds")
```

#### 2. Register and Manage Agents

```python
from delegation_manager import (
    DelegationManager,
    ResourceLimits
)

manager = DelegationManager(redis_url="redis://localhost:6379")

# Register specialized agent
resource_limits = ResourceLimits(
    memory_mb=4096,
    cpu_cores=4,
    disk_mb=10240,
    network_mbps=1000
)

manager.register_agent(
    agent_id="ml-specialist-001",
    agent_type="ML-Engineer",
    capabilities=[
        "machine-learning",
        "tensorflow",
        "model-training",
        "feature-engineering"
    ],
    max_concurrent_tasks=2,  # ML tasks are resource-intensive
    priority_weight=20,  # Higher priority
    available=True,
    resource_limits=resource_limits,
    metadata={
        "gpu_available": True,
        "gpu_model": "NVIDIA A100",
        "specialization": "deep-learning"
    }
)

# Update agent availability
manager.set_agent_availability("ml-specialist-001", available=False)

# Send heartbeat to extend TTL
manager.heartbeat_agent("ml-specialist-001")

# Get agent status
status = manager.get_agent_status("ml-specialist-001")
print(f"Agent Load: {status['current_load']}/{status['max_concurrent_tasks']}")
print(f"Capabilities: {status['capabilities']}")
print(f"Has Capacity: {status['has_capacity']}")

# List all agents
agents = manager.list_agents(
    filter_type="ML-Engineer",
    available_only=True,
    has_capacity=True
)

for agent in agents:
    print(f"{agent['agent_id']}: {agent['load_percentage']:.1f}% loaded")
```

#### 3. Delegate Tasks to Agents

```python
from delegation_manager import (
    DelegationManager,
    TaskRequest,
    TaskPriority,
    RetryPolicy,
    RetryBackoff
)

manager = DelegationManager(redis_url="redis://localhost:6379")

# Create task request
retry_policy = RetryPolicy(
    max_retries=3,
    backoff=RetryBackoff.EXPONENTIAL,
    initial_delay=5,
    max_delay=300
)

task_request = TaskRequest(
    task_id="train-model-001",
    task_type="model-training",
    required_capabilities=["machine-learning", "tensorflow"],
    priority=TaskPriority.HIGH,
    estimated_duration=3600,
    context={
        "model_type": "cnn",
        "dataset": "imagenet-subset",
        "epochs": 10,
        "batch_size": 32
    },
    timeout=7200,
    retry_policy=retry_policy,
    required_agent_type="ML-Engineer",
    exclude_agents=["ml-specialist-002"]  # Exclude specific agents
)

# Find best agent
agent_match = manager.find_best_agent(task_request)

if agent_match:
    print(f"Best Match: {agent_match.agent_id}")
    print(f"Match Score: {agent_match.score:.2f}")
    print(f"Effective Score: {agent_match.effective_score:.2f}")
    print(f"Matched Capabilities: {agent_match.matched_capabilities}")
    print(f"Current Load: {agent_match.current_load}/{agent_match.max_load}")

    # Delegate task
    delegation_result = manager.delegate_task(task_request, agent_match)
    print(f"Task delegated to: {delegation_result['agent_id']}")
    print(f"Delegation time: {delegation_result['delegated_at']}")
else:
    print("No suitable agent found")

# Mark task complete
manager.complete_task(
    agent_id="ml-specialist-001",
    task_id="train-model-001"
)
```

#### 4. Hub-and-Spoke Coordination

```python
from hub_spoke_coordinator import (
    HubSpokeCoordinator,
    Objective,
    DecompositionStrategy
)

coordinator = HubSpokeCoordinator(
    redis_url="redis://localhost:6379",
    celery_broker="redis://localhost:6379/1"
)

# Register hub agent
hub_id = coordinator.register_hub(
    hub_type="project-coordinator",
    specializations=["project-management", "task-decomposition"],
    decomposition_strategy=DecompositionStrategy.FUNCTIONAL,
    max_spokes=10
)

# Register spoke agents
spoke_ids = []
for role, capabilities in [
    ("Backend-Engineer", ["python", "api-development", "databases"]),
    ("Frontend-Engineer", ["javascript", "react", "ui-design"]),
    ("QA-Tester", ["testing", "automation", "quality-assurance"]),
    ("DevOps-Engineer", ["docker", "kubernetes", "ci-cd"])
]:
    spoke_id = coordinator.register_spoke(
        spoke_type=role,
        specializations=capabilities,
        max_concurrent_tasks=3
    )
    spoke_ids.append(spoke_id)

# Create high-level objective
objective = Objective(
    objective_id="build-api-001",
    description="Build RESTful API for user management",
    requirements=[
        "User authentication with JWT",
        "CRUD operations for users",
        "Role-based access control",
        "API documentation with OpenAPI",
        "Unit and integration tests",
        "Docker containerization"
    ],
    constraints={
        "deadline": "2025-12-01T00:00:00Z",
        "budget_hours": 80
    },
    decomposition_strategy=DecompositionStrategy.FUNCTIONAL
)

# Execute with hub-spoke pattern
result = coordinator.execute_objective(
    hub_id=hub_id,
    objective=objective,
    timeout=14400  # 4 hours
)

print(f"Objective Status: {result['status']}")
print(f"Sub-tasks Created: {len(result['sub_tasks'])}")
print(f"Spokes Used: {len(result['spoke_results'])}")
print(f"Duration: {result['duration_seconds']}s")

# Check spoke results
for spoke_result in result['spoke_results']:
    print(f"Spoke {spoke_result['spoke_id']}: {spoke_result['status']}")
```

#### 5. Agent Handoffs with Context Preservation

```python
from handoff_manager import (
    HandoffManager,
    AgentContext,
    HandoffPrecondition
)
import redis

redis_client = redis.from_url("redis://localhost:6379", decode_responses=True)

postgres_config = {
    "host": "localhost",
    "port": 5432,
    "database": "multi_agent_platform",
    "user": "orchestrator",
    "password": "your_password",
    "minconn": 1,
    "maxconn": 10
}

handoff_manager = HandoffManager(
    redis_client=redis_client,
    postgres_config=postgres_config
)

# Create source agent context
source_context = AgentContext(
    agent_id="backend-dev-001",
    agent_type="Backend-Engineer",
    conversation_history=[
        {"role": "user", "content": "Implement user authentication API"},
        {"role": "assistant", "content": "I've implemented JWT-based authentication"}
    ],
    files_created=[
        "src/api/auth.py",
        "src/models/user.py",
        "tests/test_auth.py"
    ],
    files_modified=[
        "src/api/__init__.py",
        "requirements.txt"
    ],
    state={
        "tests_passing": True,
        "coverage_percentage": 85.5,
        "api_endpoints_created": 3,
        "authentication_method": "JWT"
    },
    metadata={
        "task_id": "implement-auth-001",
        "workflow_id": "feature-dev-001",
        "completion_percentage": 100
    }
)

# Define handoff preconditions
preconditions = [
    HandoffPrecondition(
        condition_type="tests_passing",
        expected_value=True,
        operator="==",
        required=True,
        error_message="All tests must pass before handoff to QA"
    ),
    HandoffPrecondition(
        condition_type="coverage_percentage",
        expected_value=80.0,
        operator=">=",
        required=True,
        error_message="Code coverage must be at least 80%"
    ),
    HandoffPrecondition(
        condition_type="api_endpoints_created",
        expected_value=0,
        operator=">",
        required=True,
        error_message="At least one API endpoint must be created"
    )
]

# Execute handoff
handoff_result = handoff_manager.execute_handoff(
    workflow_id="feature-dev-001",
    source_context=source_context,
    target_agent_type="QA-Tester",
    preconditions=preconditions,
    transfer_files=True
)

if handoff_result.success:
    print(f"✓ Handoff successful: {handoff_result.handoff_id}")
    print(f"  Source: {handoff_result.source_agent_id}")
    print(f"  Target: {handoff_result.target_agent_id}")
    print(f"  Context transferred: {handoff_result.context_transferred}")

    # Retrieve context in target agent
    target_context = handoff_manager.get_handoff_context(handoff_result.handoff_id)
    print(f"  Files to review: {len(target_context.files_created)}")
else:
    print(f"✗ Handoff failed: {handoff_result.error}")
    print(f"  Failed preconditions: {handoff_result.failed_preconditions}")
    if handoff_result.rollback_performed:
        print("  Rollback performed")
```

#### 6. Workflow Engine with Templates

```python
from workflow_engine import (
    WorkflowEngine,
    TDDWorkflow,
    FeatureDevelopmentWorkflow,
    BugFixWorkflow,
    ExecutionMode
)

engine = WorkflowEngine(redis_url="redis://localhost:6379")

# Use TDD workflow template
tdd_template = TDDWorkflow(
    workflow_id="tdd-auth-001",
    name="TDD User Authentication"
)

tdd_workflow = tdd_template.create_workflow(
    feature_name="user_authentication",
    test_file="tests/test_user_auth.py",
    implementation_file="src/auth/user_auth.py",
    requirements="JWT-based authentication with refresh tokens"
)

# Execute workflow
result = engine.execute_workflow(tdd_workflow)
print(f"TDD Workflow: {result['status']}")

# Use Feature Development workflow template
feature_template = FeatureDevelopmentWorkflow(
    workflow_id="feature-payment-001",
    name="Payment Processing Feature"
)

feature_workflow = feature_template.create_workflow(
    feature_name="stripe_payment_integration",
    requirements="Integrate Stripe payment processing with webhook support",
    components=["api", "database", "frontend"],
    testing_required=True
)

result = engine.execute_workflow(feature_workflow)
print(f"Feature Workflow: {result['status']}")

# Use Bug Fix workflow template
bugfix_template = BugFixWorkflow(
    workflow_id="bugfix-memory-001",
    name="Memory Leak Fix"
)

bugfix_workflow = bugfix_template.create_workflow(
    bug_id="BUG-1234",
    description="Memory leak in long-running background task",
    affected_files=["src/tasks/background_worker.py"],
    severity="high",
    root_cause_analysis_required=True
)

result = engine.execute_workflow(bugfix_workflow)
print(f"Bug Fix Workflow: {result['status']}")
```

#### 7. Resource Management

```python
from resource_allocator import (
    ResourceAllocator,
    ResourceLimits,
    Priority
)

allocator = ResourceAllocator(redis_url="redis://localhost:6379")

# Register agent with resource limits
limits = ResourceLimits(
    agent_id="data-processor-001",
    cpu_cores=8.0,
    memory_mb=16384,
    max_tasks=4
)

allocator.register_agent(limits)

# Allocate resources for task
allocation_result = allocator.allocate(
    agent_id="data-processor-001",
    task_id="process-dataset-001",
    cpu_cores=2.0,
    memory_mb=4096,
    priority=Priority.HIGH
)

if allocation_result:
    print(f"✓ Resources allocated")
    print(f"  CPU: {allocation_result['cpu_allocated']} cores")
    print(f"  Memory: {allocation_result['memory_allocated']} MB")
else:
    print("✗ Insufficient resources")

# Check resource usage
usage = allocator.get_agent_usage("data-processor-001")
print(f"CPU Usage: {usage.cpu_used}/{usage.cpu_limit} cores ({usage.cpu_utilization:.1f}%)")
print(f"Memory Usage: {usage.memory_used}/{usage.memory_limit} MB ({usage.memory_utilization:.1f}%)")
print(f"Active Tasks: {usage.active_tasks}/{usage.max_tasks}")

# Release resources
allocator.release("data-processor-001", "process-dataset-001")

# Make reservation
reservation = allocator.reserve(
    agent_id="data-processor-001",
    cpu_cores=4.0,
    memory_mb=8192,
    duration_seconds=3600,
    task_id="future-task-001"
)

print(f"Reservation created: {reservation['reservation_id']}")
print(f"Expires at: {reservation['expires_at']}")
```

### CLI

#### Workflow Commands

```bash
# Create workflow from YAML file
devcrew workflow create --file workflows/feature_development.yaml --output json

# Create workflow from JSON file
devcrew workflow create --file workflows/bug_fix.json

# List all workflows
devcrew workflow list --format table

# Filter workflows by status
devcrew workflow list --status running --format table

# Start workflow execution
devcrew workflow start --id feature-dev-001 --priority high

# Get workflow status
devcrew workflow status --id feature-dev-001 --output json

# Monitor workflow (auto-refresh)
devcrew workflow monitor --id feature-dev-001 --refresh 5

# Cancel running workflow
devcrew workflow cancel --id feature-dev-001 --confirm

# Get workflow results
devcrew workflow result --id feature-dev-001 --output yaml

# Export workflow definition
devcrew workflow export --id feature-dev-001 --output workflows/exported.yaml
```

**Example Workflow YAML:**

```yaml
workflow:
  id: feature-dev-001
  name: Feature Development Workflow
  priority: high
  timeout: 7200

  tasks:
    - task_id: design-api
      agent_type: Backend-Engineer
      agent_capabilities:
        - api-design
        - openapi
      input:
        action: design_api
        feature: user_profile
        endpoints:
          - GET /users/{id}
          - PUT /users/{id}
          - DELETE /users/{id}
      timeout: 1800
      retry: 3

    - task_id: implement-api
      agent_type: Backend-Engineer
      agent_capabilities:
        - python
        - api-development
        - fastapi
      input:
        action: implement_api
        design_reference: design-api
      depends_on:
        - design-api
      timeout: 3600
      retry: 3

    - task_id: write-tests
      agent_type: QA-Tester
      agent_capabilities:
        - testing
        - pytest
        - api-testing
      input:
        action: write_tests
        test_type: integration
        api_reference: implement-api
      depends_on:
        - implement-api
      timeout: 1800
      retry: 2

    - task_id: run-tests
      agent_type: QA-Tester
      agent_capabilities:
        - testing
        - pytest
      input:
        action: run_tests
        coverage_required: 80
      depends_on:
        - write-tests
      timeout: 900
      retry: 1

  notification:
    on_complete:
      - user@example.com
    on_failure:
      - admin@example.com
      - oncall@example.com
```

#### Agent Commands

```bash
# Register new agent
devcrew agent register \
  --id backend-dev-001 \
  --type Backend-Engineer \
  --capabilities python,api-development,testing \
  --max-tasks 3 \
  --priority 15

# Register agent with resource limits
devcrew agent register \
  --id ml-specialist-001 \
  --type ML-Engineer \
  --capabilities machine-learning,tensorflow \
  --max-tasks 2 \
  --priority 20 \
  --cpu-cores 8 \
  --memory-mb 16384 \
  --metadata '{"gpu": "A100", "vram": "40GB"}'

# List all agents
devcrew agent list --format table

# Filter agents by type
devcrew agent list --type Backend-Engineer --format table

# Show only available agents
devcrew agent list --available --format table

# Show only agents with capacity
devcrew agent list --has-capacity --format table

# Get agent status
devcrew agent status --id backend-dev-001 --output json

# Update agent availability
devcrew agent set-availability --id backend-dev-001 --available false

# Update agent availability (enable)
devcrew agent set-availability --id backend-dev-001 --available true

# Send heartbeat
devcrew agent heartbeat --id backend-dev-001

# Deregister agent
devcrew agent deregister --id backend-dev-001 --confirm

# Get delegation statistics
devcrew agent stats --output json

# Clean up expired agents
devcrew agent cleanup
```

#### Task Commands

```bash
# Delegate task to best agent
devcrew task delegate \
  --task-id train-model-001 \
  --type model-training \
  --capabilities machine-learning,tensorflow \
  --priority high \
  --duration 3600 \
  --timeout 7200 \
  --context '{"model": "cnn", "dataset": "imagenet"}'

# Find best agent for capabilities
devcrew task find-agent \
  --capabilities python,api-development,testing \
  --type Backend-Engineer \
  --output json

# Complete task
devcrew task complete \
  --agent-id backend-dev-001 \
  --task-id implement-api-001

# List active tasks
devcrew task list --status active --format table

# List tasks by agent
devcrew task list --agent-id backend-dev-001 --format table

# Get task details
devcrew task status --task-id implement-api-001 --output json
```

#### Hub-Spoke Commands

```bash
# Register hub agent
devcrew hub register \
  --type project-coordinator \
  --specializations project-management,task-decomposition \
  --strategy functional \
  --max-spokes 10

# Register spoke agent
devcrew spoke register \
  --type Backend-Engineer \
  --specializations python,api-development,databases \
  --max-tasks 3 \
  --priority 15

# Execute objective with hub-spoke
devcrew hub execute \
  --hub-id hub-001 \
  --objective-file objectives/build_api.yaml \
  --timeout 14400

# List hub agents
devcrew hub list --format table

# List spoke agents for hub
devcrew spoke list --hub-id hub-001 --format table

# Get hub status
devcrew hub status --id hub-001 --output json

# Get spoke status
devcrew spoke status --id spoke-001 --output json
```

**Example Objective YAML:**

```yaml
objective:
  id: build-api-001
  description: Build RESTful API for user management

  requirements:
    - User authentication with JWT
    - CRUD operations for users
    - Role-based access control
    - API documentation with OpenAPI
    - Unit and integration tests
    - Docker containerization

  constraints:
    deadline: "2025-12-01T00:00:00Z"
    budget_hours: 80
    team_size: 4

  decomposition_strategy: functional

  context:
    tech_stack:
      - Python 3.10+
      - FastAPI
      - PostgreSQL
      - Redis
      - Docker

    quality_requirements:
      test_coverage: 85
      code_quality: A
      security_scan: passed
```

#### Handoff Commands

```bash
# Execute handoff with preconditions
devcrew handoff execute \
  --workflow-id feature-dev-001 \
  --source-agent backend-dev-001 \
  --target-type QA-Tester \
  --preconditions-file preconditions.yaml \
  --transfer-files

# Get handoff status
devcrew handoff status --id handoff-123 --output json

# List handoffs for workflow
devcrew handoff list --workflow-id feature-dev-001 --format table

# Get handoff context
devcrew handoff context --id handoff-123 --output json

# Rollback handoff
devcrew handoff rollback --id handoff-123 --reason "Failed validation"

# Get handoff audit trail
devcrew handoff audit --workflow-id feature-dev-001 --format table

# Export handoff log
devcrew handoff export --workflow-id feature-dev-001 --output handoff_log.json
```

**Example Preconditions YAML:**

```yaml
preconditions:
  - condition_type: tests_passing
    expected_value: true
    operator: "=="
    required: true
    error_message: "All tests must pass before handoff to QA"

  - condition_type: coverage_percentage
    expected_value: 80.0
    operator: ">="
    required: true
    error_message: "Code coverage must be at least 80%"

  - condition_type: api_endpoints_created
    expected_value: 0
    operator: ">"
    required: true
    error_message: "At least one API endpoint must be created"

  - condition_type: documentation_complete
    expected_value: true
    operator: "=="
    required: false
    error_message: "API documentation should be complete"
```

#### Monitoring Commands

```bash
# Show platform health
devcrew monitor health --output json

# Show resource usage
devcrew monitor resources --format table

# Monitor workflow execution (real-time)
devcrew monitor workflow --id feature-dev-001 --refresh 5

# Show agent metrics
devcrew monitor agents --format table

# Export metrics
devcrew monitor export --output metrics.json --duration 3600

# Show capacity planning
devcrew monitor capacity --output json
```

---

## Workflow Templates

The platform includes pre-built workflow templates for common development patterns.

### TDD Workflow

Test-Driven Development workflow implementing the Red → Green → Refactor cycle.

```python
from workflow_engine import TDDWorkflow

template = TDDWorkflow(
    workflow_id="tdd-feature-001",
    name="TDD Feature Development"
)

workflow = template.create_workflow(
    feature_name="payment_processing",
    test_file="tests/test_payment.py",
    implementation_file="src/payment/processor.py",
    requirements="Process credit card payments with Stripe integration"
)
```

**Phases:**
1. **Red**: Write failing tests for the feature
2. **Green**: Implement feature to pass tests
3. **Refactor**: Improve code quality while maintaining tests

### Feature Development Workflow

Complete feature development lifecycle with design, implementation, testing, and review.

```python
from workflow_engine import FeatureDevelopmentWorkflow

template = FeatureDevelopmentWorkflow(
    workflow_id="feature-dashboard-001",
    name="User Dashboard Feature"
)

workflow = template.create_workflow(
    feature_name="user_dashboard",
    requirements="Interactive dashboard with real-time metrics and charts",
    components=["backend-api", "frontend-ui", "database-schema"],
    testing_required=True
)
```

**Phases:**
1. **Design**: API design and UI mockups
2. **Backend**: API implementation
3. **Frontend**: UI implementation
4. **Integration**: Connect frontend and backend
5. **Testing**: End-to-end testing
6. **Review**: Code review and quality checks

### Bug Fix Workflow

Systematic bug resolution with root cause analysis and verification.

```python
from workflow_engine import BugFixWorkflow

template = BugFixWorkflow(
    workflow_id="bugfix-001",
    name="Memory Leak Fix"
)

workflow = template.create_workflow(
    bug_id="BUG-5678",
    description="Memory leak in background task processing",
    affected_files=["src/tasks/processor.py", "src/utils/cache.py"],
    severity="high",
    root_cause_analysis_required=True
)
```

**Phases:**
1. **Reproduce**: Reproduce the bug
2. **Root Cause**: Analyze root cause
3. **Fix**: Implement fix
4. **Test**: Verify fix with tests
5. **Regression**: Run regression tests

### Custom Template Creation

Create your own workflow templates:

```python
from workflow_engine import WorkflowTemplate
from task_orchestrator import Workflow, Task
from typing import Any

class CustomWorkflow(WorkflowTemplate):
    """Custom workflow template."""

    def create_workflow(self, **params: Any) -> Workflow:
        """Create custom workflow."""
        workflow = Workflow(
            workflow_id=self.workflow_id,
            name=self.name,
            priority=params.get("priority", "medium")
        )

        # Add custom tasks
        task1 = self._create_task(
            task_id=f"{self.workflow_id}_step1",
            agent_type="Custom-Agent",
            input_data={"action": "custom_action"},
            timeout=1800
        )

        workflow.add_task(task1)
        return workflow

# Use custom template
template = CustomWorkflow(
    workflow_id="custom-001",
    name="Custom Workflow"
)

workflow = template.create_workflow(priority="high")
```

---

## Protocol Integration

The platform implements multiple coordination protocols for multi-agent orchestration.

### CA-CS-NotifyHuman

**Human-in-the-Loop Notifications**

Notify humans for approval, feedback, or critical decisions.

```python
from task_orchestrator import Workflow

workflow = Workflow(
    workflow_id="deployment-001",
    name="Production Deployment",
    notification={
        "on_complete": ["ops-team@example.com"],
        "on_failure": ["oncall@example.com"],
        "on_approval_needed": ["tech-lead@example.com"]
    }
)
```

**Use Cases:**
- Production deployment approvals
- Critical error notifications
- Manual review requests
- Escalation triggers

### P-DELEGATION-DEFAULT

**Capability-Based Task Delegation**

Intelligent routing of tasks to agents based on capabilities and availability.

```python
from delegation_manager import DelegationManager, TaskRequest

manager = DelegationManager(redis_url="redis://localhost:6379")

task_request = TaskRequest(
    task_id="complex-task-001",
    task_type="data-analysis",
    required_capabilities=["python", "pandas", "statistical-analysis"],
    priority="high"
)

agent_match = manager.find_best_agent(task_request)
delegation_result = manager.delegate_task(task_request, agent_match)
```

**Features:**
- Capability scoring and matching
- Load balancing across agents
- Priority-weighted selection
- Automatic failover

### P-HANDOFF

**Agent-to-Agent Context Transfer**

Seamless handoffs between agents with context preservation and validation.

```python
from handoff_manager import HandoffManager, AgentContext, HandoffPrecondition

handoff_result = handoff_manager.execute_handoff(
    workflow_id="feature-dev-001",
    source_context=source_context,
    target_agent_type="QA-Tester",
    preconditions=[
        HandoffPrecondition(
            condition_type="tests_passing",
            expected_value=True,
            operator="==",
            required=True
        )
    ]
)
```

**Features:**
- Context serialization and transfer
- Precondition validation
- Automatic rollback on failure
- Complete audit trail

### P-HUB-SPOKE-COORDINATION

**Hierarchical Task Decomposition**

Hub agent decomposes objectives into sub-tasks for spoke agents.

```python
from hub_spoke_coordinator import HubSpokeCoordinator, Objective

coordinator = HubSpokeCoordinator(redis_url="redis://localhost:6379")

objective = Objective(
    objective_id="project-001",
    description="Build complete web application",
    requirements=["Frontend", "Backend", "Database", "Tests"],
    decomposition_strategy="functional"
)

result = coordinator.execute_objective(
    hub_id="hub-001",
    objective=objective
)
```

**Features:**
- Intelligent objective decomposition
- Parallel spoke execution
- Result aggregation
- Dynamic spoke assignment

### P-ORCHESTRATION

**Multi-Agent Workflow Coordination**

Prefect-based workflow orchestration with dependency management.

```python
from task_orchestrator import TaskOrchestrator, Workflow, Task

orchestrator = TaskOrchestrator(redis_url="redis://localhost:6379")

workflow = Workflow(
    workflow_id="complex-workflow-001",
    name="Multi-Step Process"
)

# Tasks with dependencies
task1 = Task(task_id="step1", agent_type="Agent-A", input_data={})
task2 = Task(task_id="step2", agent_type="Agent-B", input_data={}, depends_on=["step1"])
task3 = Task(task_id="step3", agent_type="Agent-C", input_data={}, depends_on=["step1"])
task4 = Task(task_id="step4", agent_type="Agent-D", input_data={}, depends_on=["step2", "step3"])

workflow.add_task(task1)
workflow.add_task(task2)
workflow.add_task(task3)
workflow.add_task(task4)

result = orchestrator.execute_workflow("complex-workflow-001")
```

**Features:**
- Dependency resolution
- Parallel execution
- State management
- Failure recovery

### P-RESOURCE

**Distributed Resource Management**

Track and allocate CPU, memory, and task resources across agents.

```python
from resource_allocator import ResourceAllocator, Priority

allocator = ResourceAllocator(redis_url="redis://localhost:6379")

# Allocate resources
allocation = allocator.allocate(
    agent_id="worker-001",
    task_id="heavy-task-001",
    cpu_cores=4.0,
    memory_mb=8192,
    priority=Priority.HIGH
)

# Release when done
allocator.release("worker-001", "heavy-task-001")
```

**Features:**
- Priority-based allocation
- Resource reservation
- Deadlock detection
- Automatic cleanup

### P-SYSTEM-NOTIFY

**System-Level Notifications**

Internal notifications for system events and state changes.

```python
# System notifications are automatically triggered for:
# - Agent registration/deregistration
# - Resource exhaustion
# - Workflow state changes
# - Task failures
# - Handoff events
```

**Event Types:**
- Agent lifecycle events
- Resource threshold alerts
- Task execution events
- System health warnings

---

## API Reference

### TaskOrchestrator

**Purpose**: Coordinate multi-agent workflows using Prefect.

#### Methods

##### `__init__(redis_url: str = "redis://localhost:6379")`

Initialize the task orchestrator.

**Parameters:**
- `redis_url` (str): Redis connection URL

**Example:**
```python
orchestrator = TaskOrchestrator(redis_url="redis://localhost:6379")
```

##### `parse_workflow_definition(file_path: str) -> Workflow`

Parse workflow definition from YAML or JSON file.

**Parameters:**
- `file_path` (str): Path to workflow definition file

**Returns:**
- `Workflow`: Parsed workflow object

**Raises:**
- `ValueError`: If file format is invalid

**Example:**
```python
workflow = TaskOrchestrator.parse_workflow_definition("workflow.yaml")
```

##### `create_workflow(workflow: Workflow) -> str`

Register a workflow for execution.

**Parameters:**
- `workflow` (Workflow): Workflow to register

**Returns:**
- `str`: Workflow ID

**Example:**
```python
workflow_id = orchestrator.create_workflow(workflow)
```

##### `execute_workflow(workflow_id: str) -> Dict[str, Any]`

Execute a workflow using Prefect.

**Parameters:**
- `workflow_id` (str): ID of workflow to execute

**Returns:**
- `Dict[str, Any]`: Workflow execution result

**Example:**
```python
result = orchestrator.execute_workflow("feature-dev-001")
```

##### `get_workflow_status(workflow_id: str) -> Dict[str, Any]`

Get workflow status.

**Parameters:**
- `workflow_id` (str): Workflow ID

**Returns:**
- `Dict[str, Any]`: Workflow status information

**Example:**
```python
status = orchestrator.get_workflow_status("feature-dev-001")
```

##### `cancel_workflow(workflow_id: str) -> bool`

Cancel a running workflow.

**Parameters:**
- `workflow_id` (str): Workflow ID

**Returns:**
- `bool`: True if cancelled successfully

**Example:**
```python
cancelled = orchestrator.cancel_workflow("feature-dev-001")
```

---

### DelegationManager

**Purpose**: Intelligent task routing to agents based on capabilities.

#### Methods

##### `__init__(redis_url: str, redis_db: int = 0, redis_password: Optional[str] = None, connection_pool_size: int = 10)`

Initialize the delegation manager.

**Parameters:**
- `redis_url` (str): Redis connection URL
- `redis_db` (int): Redis database number
- `redis_password` (Optional[str]): Redis password
- `connection_pool_size` (int): Connection pool size

**Example:**
```python
manager = DelegationManager(
    redis_url="redis://localhost:6379",
    redis_db=0,
    connection_pool_size=20
)
```

##### `register_agent(agent_id: str, agent_type: str, capabilities: List[str], max_concurrent_tasks: int = 3, priority_weight: int = 10, available: bool = True, resource_limits: Optional[ResourceLimits] = None, metadata: Optional[Dict[str, Any]] = None) -> bool`

Register an agent with the delegation manager.

**Parameters:**
- `agent_id` (str): Unique agent identifier
- `agent_type` (str): Type/category of agent
- `capabilities` (List[str]): List of agent capabilities
- `max_concurrent_tasks` (int): Maximum concurrent tasks
- `priority_weight` (int): Agent priority weight (1-100)
- `available` (bool): Agent availability status
- `resource_limits` (Optional[ResourceLimits]): Resource limits
- `metadata` (Optional[Dict[str, Any]]): Additional metadata

**Returns:**
- `bool`: True if registration successful

**Example:**
```python
manager.register_agent(
    agent_id="backend-dev-001",
    agent_type="Backend-Engineer",
    capabilities=["python", "api-development"],
    max_concurrent_tasks=5
)
```

##### `find_best_agent(task_request: TaskRequest) -> Optional[AgentMatch]`

Find the best agent for a task request.

**Parameters:**
- `task_request` (TaskRequest): Task delegation request

**Returns:**
- `Optional[AgentMatch]`: Best matching agent or None

**Example:**
```python
task_request = TaskRequest(
    task_id="task-001",
    task_type="api-development",
    required_capabilities=["python", "fastapi"]
)
agent_match = manager.find_best_agent(task_request)
```

##### `delegate_task(task_request: TaskRequest, agent_match: AgentMatch) -> Dict[str, Any]`

Delegate a task to a matched agent.

**Parameters:**
- `task_request` (TaskRequest): Task request to delegate
- `agent_match` (AgentMatch): Matched agent to receive task

**Returns:**
- `Dict[str, Any]`: Delegation details

**Example:**
```python
delegation_result = manager.delegate_task(task_request, agent_match)
```

##### `complete_task(agent_id: str, task_id: str) -> bool`

Mark a task as complete and decrement agent load.

**Parameters:**
- `agent_id` (str): Agent identifier
- `task_id` (str): Task identifier

**Returns:**
- `bool`: True if successful

**Example:**
```python
manager.complete_task("backend-dev-001", "task-001")
```

##### `get_agent_status(agent_id: str) -> Optional[Dict[str, Any]]`

Get current status of an agent.

**Parameters:**
- `agent_id` (str): Agent identifier

**Returns:**
- `Optional[Dict[str, Any]]`: Agent status or None

**Example:**
```python
status = manager.get_agent_status("backend-dev-001")
```

##### `list_agents(filter_type: Optional[str] = None, available_only: bool = False, has_capacity: bool = False) -> List[Dict[str, Any]]`

List all registered agents with optional filters.

**Parameters:**
- `filter_type` (Optional[str]): Filter by agent type
- `available_only` (bool): Only return available agents
- `has_capacity` (bool): Only return agents with capacity

**Returns:**
- `List[Dict[str, Any]]`: List of agent status dictionaries

**Example:**
```python
agents = manager.list_agents(
    filter_type="Backend-Engineer",
    available_only=True,
    has_capacity=True
)
```

---

### WorkflowEngine

**Purpose**: Advanced workflow execution with conditional logic and templates.

#### Methods

##### `__init__(redis_url: str = "redis://localhost:6379")`

Initialize the workflow engine.

**Parameters:**
- `redis_url` (str): Redis connection URL

**Example:**
```python
engine = WorkflowEngine(redis_url="redis://localhost:6379")
```

##### `execute_workflow(workflow: Workflow, execution_mode: ExecutionMode = ExecutionMode.SEQUENTIAL) -> Dict[str, Any]`

Execute a workflow with specified execution mode.

**Parameters:**
- `workflow` (Workflow): Workflow to execute
- `execution_mode` (ExecutionMode): Execution mode

**Returns:**
- `Dict[str, Any]`: Execution result

**Example:**
```python
result = engine.execute_workflow(workflow, ExecutionMode.PARALLEL)
```

---

### ResourceAllocator

**Purpose**: Distributed resource management for agents.

#### Methods

##### `__init__(redis_url: str = "redis://localhost:6379")`

Initialize the resource allocator.

**Parameters:**
- `redis_url` (str): Redis connection URL

**Example:**
```python
allocator = ResourceAllocator(redis_url="redis://localhost:6379")
```

##### `register_agent(limits: ResourceLimits) -> bool`

Register an agent with resource limits.

**Parameters:**
- `limits` (ResourceLimits): Resource limits for agent

**Returns:**
- `bool`: True if registration successful

**Example:**
```python
limits = ResourceLimits(
    agent_id="worker-001",
    cpu_cores=8.0,
    memory_mb=16384,
    max_tasks=4
)
allocator.register_agent(limits)
```

##### `allocate(agent_id: str, task_id: str, cpu_cores: float, memory_mb: float, priority: Priority = Priority.MEDIUM) -> Optional[Dict[str, Any]]`

Allocate resources for a task.

**Parameters:**
- `agent_id` (str): Agent identifier
- `task_id` (str): Task identifier
- `cpu_cores` (float): CPU cores to allocate
- `memory_mb` (float): Memory in MB to allocate
- `priority` (Priority): Task priority

**Returns:**
- `Optional[Dict[str, Any]]`: Allocation details or None

**Example:**
```python
allocation = allocator.allocate(
    agent_id="worker-001",
    task_id="task-001",
    cpu_cores=2.0,
    memory_mb=4096,
    priority=Priority.HIGH
)
```

##### `release(agent_id: str, task_id: str) -> bool`

Release resources allocated for a task.

**Parameters:**
- `agent_id` (str): Agent identifier
- `task_id` (str): Task identifier

**Returns:**
- `bool`: True if released successfully

**Example:**
```python
allocator.release("worker-001", "task-001")
```

##### `get_agent_usage(agent_id: str) -> Optional[ResourceUsage]`

Get current resource usage for an agent.

**Parameters:**
- `agent_id` (str): Agent identifier

**Returns:**
- `Optional[ResourceUsage]`: Resource usage or None

**Example:**
```python
usage = allocator.get_agent_usage("worker-001")
print(f"CPU: {usage.cpu_utilization:.1f}%")
print(f"Memory: {usage.memory_utilization:.1f}%")
```

---

### HubSpokeCoordinator

**Purpose**: Hierarchical multi-agent coordination pattern.

#### Methods

##### `__init__(redis_url: str, celery_broker: str)`

Initialize the hub-spoke coordinator.

**Parameters:**
- `redis_url` (str): Redis connection URL
- `celery_broker` (str): Celery broker URL

**Example:**
```python
coordinator = HubSpokeCoordinator(
    redis_url="redis://localhost:6379",
    celery_broker="redis://localhost:6379/1"
)
```

##### `register_hub(hub_type: str, specializations: List[str], decomposition_strategy: DecompositionStrategy = DecompositionStrategy.FUNCTIONAL, max_spokes: int = 10) -> str`

Register a hub agent.

**Parameters:**
- `hub_type` (str): Type of hub agent
- `specializations` (List[str]): Hub specializations
- `decomposition_strategy` (DecompositionStrategy): Decomposition strategy
- `max_spokes` (int): Maximum number of spokes

**Returns:**
- `str`: Hub ID

**Example:**
```python
hub_id = coordinator.register_hub(
    hub_type="project-coordinator",
    specializations=["task-decomposition"],
    max_spokes=10
)
```

##### `register_spoke(spoke_type: str, specializations: List[str], max_concurrent_tasks: int = 3) -> str`

Register a spoke agent.

**Parameters:**
- `spoke_type` (str): Type of spoke agent
- `specializations` (List[str]): Spoke specializations
- `max_concurrent_tasks` (int): Maximum concurrent tasks

**Returns:**
- `str`: Spoke ID

**Example:**
```python
spoke_id = coordinator.register_spoke(
    spoke_type="Backend-Engineer",
    specializations=["python", "api-development"],
    max_concurrent_tasks=3
)
```

##### `execute_objective(hub_id: str, objective: Objective, timeout: int = 3600) -> Dict[str, Any]`

Execute an objective with hub-spoke coordination.

**Parameters:**
- `hub_id` (str): Hub agent ID
- `objective` (Objective): High-level objective
- `timeout` (int): Execution timeout in seconds

**Returns:**
- `Dict[str, Any]`: Execution result

**Example:**
```python
result = coordinator.execute_objective(
    hub_id="hub-001",
    objective=objective,
    timeout=7200
)
```

---

### HandoffManager

**Purpose**: Seamless agent-to-agent handoffs with context preservation.

#### Methods

##### `__init__(redis_client: Optional[Redis] = None, postgres_config: Optional[Dict[str, Any]] = None)`

Initialize the handoff manager.

**Parameters:**
- `redis_client` (Optional[Redis]): Redis client instance
- `postgres_config` (Optional[Dict[str, Any]]): PostgreSQL configuration

**Example:**
```python
import redis

redis_client = redis.from_url("redis://localhost:6379", decode_responses=True)

postgres_config = {
    "host": "localhost",
    "port": 5432,
    "database": "multi_agent_platform",
    "user": "orchestrator",
    "password": "password",
    "minconn": 1,
    "maxconn": 10
}

handoff_manager = HandoffManager(
    redis_client=redis_client,
    postgres_config=postgres_config
)
```

##### `execute_handoff(workflow_id: str, source_context: AgentContext, target_agent_type: str, preconditions: Optional[List[HandoffPrecondition]] = None, transfer_files: bool = True) -> HandoffResult`

Execute a handoff from source agent to target agent.

**Parameters:**
- `workflow_id` (str): Workflow identifier
- `source_context` (AgentContext): Source agent context
- `target_agent_type` (str): Target agent type
- `preconditions` (Optional[List[HandoffPrecondition]]): Validation rules
- `transfer_files` (bool): Whether to transfer files

**Returns:**
- `HandoffResult`: Handoff execution result

**Example:**
```python
handoff_result = handoff_manager.execute_handoff(
    workflow_id="feature-dev-001",
    source_context=source_context,
    target_agent_type="QA-Tester",
    preconditions=preconditions,
    transfer_files=True
)
```

##### `get_handoff_context(handoff_id: str) -> Optional[AgentContext]`

Retrieve handoff context.

**Parameters:**
- `handoff_id` (str): Handoff identifier

**Returns:**
- `Optional[AgentContext]`: Agent context or None

**Example:**
```python
context = handoff_manager.get_handoff_context("handoff-123")
```

##### `rollback_handoff(handoff_id: str, reason: str) -> bool`

Rollback a handoff.

**Parameters:**
- `handoff_id` (str): Handoff identifier
- `reason` (str): Rollback reason

**Returns:**
- `bool`: True if rollback successful

**Example:**
```python
handoff_manager.rollback_handoff("handoff-123", "Validation failed")
```

---

## Testing

### Running Tests

```bash
# Run all tests
pytest -v

# Run specific test file
pytest tests/test_orchestration.py -v

# Run tests with coverage
pytest --cov=. --cov-report=html --cov-report=term

# Run tests matching pattern
pytest -k "test_delegation" -v

# Run tests with specific marker
pytest -m integration -v

# Run tests in parallel
pytest -n auto
```

### Test Structure

```
tests/
├── test_orchestration.py       # Integration tests for all components
├── test_task_orchestrator.py   # Unit tests for TaskOrchestrator
├── test_delegation_manager.py  # Unit tests for DelegationManager
├── test_workflow_engine.py     # Unit tests for WorkflowEngine
├── test_resource_allocator.py  # Unit tests for ResourceAllocator
├── test_hub_spoke.py           # Unit tests for HubSpokeCoordinator
├── test_handoff_manager.py     # Unit tests for HandoffManager
└── conftest.py                 # Pytest fixtures
```

### Test Markers

```python
# Unit tests
@pytest.mark.unit
def test_task_creation():
    pass

# Integration tests
@pytest.mark.integration
def test_workflow_execution():
    pass

# Requires Redis
@pytest.mark.redis
def test_agent_registration():
    pass

# Requires PostgreSQL
@pytest.mark.postgres
def test_handoff_audit_trail():
    pass

# Slow tests
@pytest.mark.slow
def test_large_workflow():
    pass
```

### Writing Tests

```python
import pytest
from task_orchestrator import TaskOrchestrator, Workflow, Task

@pytest.fixture
def orchestrator():
    """Create TaskOrchestrator instance for testing."""
    return TaskOrchestrator(redis_url="redis://localhost:6379")

@pytest.fixture
def sample_workflow():
    """Create sample workflow for testing."""
    workflow = Workflow(
        workflow_id="test-workflow-001",
        name="Test Workflow"
    )

    task = Task(
        task_id="test-task-001",
        agent_type="Test-Agent",
        input_data={"action": "test"}
    )

    workflow.add_task(task)
    return workflow

def test_workflow_creation(orchestrator, sample_workflow):
    """Test workflow creation."""
    workflow_id = orchestrator.create_workflow(sample_workflow)
    assert workflow_id == "test-workflow-001"

def test_workflow_execution(orchestrator, sample_workflow):
    """Test workflow execution."""
    orchestrator.create_workflow(sample_workflow)
    result = orchestrator.execute_workflow("test-workflow-001")

    assert result["status"] == "completed"
    assert result["tasks_completed"] == 1
    assert result["tasks_failed"] == 0
```

### Coverage Reports

```bash
# Generate HTML coverage report
pytest --cov=. --cov-report=html

# Open coverage report
open htmlcov/index.html

# Generate terminal coverage report
pytest --cov=. --cov-report=term-missing

# Generate XML coverage report (for CI)
pytest --cov=. --cov-report=xml
```

### Test Environment Setup

```bash
# Start Redis for testing
docker run -d --name redis-test -p 6379:6379 redis:7

# Start PostgreSQL for testing
docker run -d --name postgres-test \
  -e POSTGRES_DB=multi_agent_platform_test \
  -e POSTGRES_USER=test \
  -e POSTGRES_PASSWORD=test \
  -p 5432:5432 \
  postgres:14

# Run tests
REDIS_URL=redis://localhost:6379 \
POSTGRES_HOST=localhost \
POSTGRES_PORT=5432 \
POSTGRES_DB=multi_agent_platform_test \
POSTGRES_USER=test \
POSTGRES_PASSWORD=test \
pytest -v

# Cleanup
docker stop redis-test postgres-test
docker rm redis-test postgres-test
```

---

## Troubleshooting

### Common Issues

#### 1. Redis Connection Errors

**Symptom:**
```
RedisConnectionError: Error connecting to Redis
```

**Solution:**
```bash
# Check if Redis is running
redis-cli ping

# Start Redis
brew services start redis  # macOS
sudo systemctl start redis-server  # Linux

# Check Redis port
lsof -i :6379

# Test connection
redis-cli -h localhost -p 6379 ping
```

**Python test:**
```python
import redis

try:
    r = redis.from_url("redis://localhost:6379")
    r.ping()
    print("✓ Redis connection successful")
except Exception as e:
    print(f"✗ Redis connection failed: {e}")
```

#### 2. PostgreSQL Connection Errors

**Symptom:**
```
psycopg2.OperationalError: could not connect to server
```

**Solution:**
```bash
# Check if PostgreSQL is running
pg_isready

# Start PostgreSQL
brew services start postgresql@14  # macOS
sudo systemctl start postgresql  # Linux

# Test connection
psql -U orchestrator -d multi_agent_platform -h localhost

# Check PostgreSQL logs
tail -f /usr/local/var/log/postgresql@14.log  # macOS
sudo journalctl -u postgresql -f  # Linux
```

**Connection string format:**
```python
postgres_config = {
    "host": "localhost",
    "port": 5432,
    "database": "multi_agent_platform",
    "user": "orchestrator",
    "password": "your_password",
    "minconn": 1,
    "maxconn": 10
}
```

#### 3. Agent Registration Failures

**Symptom:**
```
ValueError: Agent must have at least one capability
```

**Solution:**
```python
# Ensure capabilities list is not empty
manager.register_agent(
    agent_id="backend-dev-001",
    agent_type="Backend-Engineer",
    capabilities=["python", "api-development"],  # Must have at least one
    max_concurrent_tasks=3
)

# Capabilities are normalized to lowercase
# "Python" -> "python"
# "API-Development" -> "api-development"
```

#### 4. Workflow Execution Failures

**Symptom:**
```
RuntimeError: Workflow has pending tasks but none are ready
```

**Cause:** Circular dependency in task definitions

**Solution:**
```python
# Check task dependencies
workflow = Workflow(workflow_id="test-001", name="Test")

task1 = Task(task_id="task1", agent_type="Agent-A", input_data={})
task2 = Task(task_id="task2", agent_type="Agent-B", input_data={}, depends_on=["task3"])
task3 = Task(task_id="task3", agent_type="Agent-C", input_data={}, depends_on=["task2"])  # Circular!

# Fix: Remove circular dependency
task2 = Task(task_id="task2", agent_type="Agent-B", input_data={}, depends_on=["task1"])
task3 = Task(task_id="task3", agent_type="Agent-C", input_data={}, depends_on=["task2"])
```

#### 5. Resource Exhaustion

**Symptom:**
```
ValueError: Agent has no capacity (load: 5/5)
```

**Solution:**
```python
# Check agent capacity
status = manager.get_agent_status("backend-dev-001")
print(f"Load: {status['current_load']}/{status['max_concurrent_tasks']}")

# Option 1: Wait for tasks to complete
manager.complete_task("backend-dev-001", "completed-task-id")

# Option 2: Register additional agents
manager.register_agent(
    agent_id="backend-dev-002",
    agent_type="Backend-Engineer",
    capabilities=["python", "api-development"],
    max_concurrent_tasks=5
)

# Option 3: Increase max_concurrent_tasks
# (requires re-registration)
manager.deregister_agent("backend-dev-001")
manager.register_agent(
    agent_id="backend-dev-001",
    agent_type="Backend-Engineer",
    capabilities=["python", "api-development"],
    max_concurrent_tasks=10  # Increased
)
```

#### 6. Agent TTL Expiration

**Symptom:**
```
Agent not found (expired)
```

**Solution:**
```python
# Send regular heartbeats
import time
import threading

def heartbeat_worker(manager, agent_id, interval=60):
    """Send heartbeat every interval seconds."""
    while True:
        try:
            manager.heartbeat_agent(agent_id)
            time.sleep(interval)
        except Exception as e:
            print(f"Heartbeat failed: {e}")
            break

# Start heartbeat thread
thread = threading.Thread(
    target=heartbeat_worker,
    args=(manager, "backend-dev-001", 60),
    daemon=True
)
thread.start()
```

#### 7. Handoff Validation Failures

**Symptom:**
```
HandoffResult(success=False, validation_passed=False)
```

**Solution:**
```python
# Check failed preconditions
if not handoff_result.success:
    print("Failed preconditions:")
    for condition in handoff_result.failed_preconditions:
        print(f"  - {condition}")

    # Fix the issues before retry
    # Example: Ensure tests pass
    source_context.state["tests_passing"] = True

    # Retry handoff
    retry_result = handoff_manager.execute_handoff(
        workflow_id="feature-dev-001",
        source_context=source_context,
        target_agent_type="QA-Tester",
        preconditions=preconditions
    )
```

### Debugging Tips

#### Enable Debug Logging

```python
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Platform component loggers
logging.getLogger("delegation_manager").setLevel(logging.DEBUG)
logging.getLogger("task_orchestrator").setLevel(logging.DEBUG)
logging.getLogger("hub_spoke_coordinator").setLevel(logging.DEBUG)
```

#### Inspect Redis State

```bash
# Connect to Redis
redis-cli

# List all agents
SMEMBERS agents:index

# Get agent data
GET agent:backend-dev-001

# Get agent load
GET agent:load:backend-dev-001

# List agents by type
SMEMBERS agents:type:Backend-Engineer
```

#### Inspect PostgreSQL Audit Trail

```sql
-- Connect to database
psql -U orchestrator -d multi_agent_platform

-- View all handoffs
SELECT
    handoff_id,
    workflow_id,
    source_agent_type,
    target_agent_type,
    success,
    created_at
FROM handoff_log
ORDER BY created_at DESC
LIMIT 10;

-- View failed handoffs
SELECT
    handoff_id,
    error,
    failed_preconditions
FROM handoff_log
WHERE success = false
ORDER BY created_at DESC;

-- View handoffs for workflow
SELECT *
FROM handoff_log
WHERE workflow_id = 'feature-dev-001'
ORDER BY created_at;
```

#### Monitor Celery Tasks (Hub-Spoke)

```bash
# Start Celery worker with logging
celery -A hub_spoke_coordinator worker --loglevel=debug

# Monitor Celery events
celery -A hub_spoke_coordinator events

# Inspect active tasks
celery -A hub_spoke_coordinator inspect active

# Inspect registered tasks
celery -A hub_spoke_coordinator inspect registered
```

---

## Performance

### Benchmarks and Metrics

#### Task Orchestration

- **Sequential Execution**: 10-100 tasks/second (depends on task complexity)
- **Parallel Execution**: Up to 1000 tasks/second with concurrent runner
- **Workflow Overhead**: ~50-100ms per workflow
- **Task Overhead**: ~10-20ms per task

#### Agent Delegation

- **Agent Registration**: ~5ms per agent
- **Capability Matching**: ~1-5ms per match (depends on agent count)
- **Task Delegation**: ~10-20ms per delegation
- **Agent Query**: ~2-5ms per query

#### Resource Allocation

- **Allocation Operation**: ~5-10ms (atomic Lua script)
- **Release Operation**: ~5-10ms
- **Usage Query**: ~2-5ms
- **Concurrent Allocations**: 1000+ operations/second

#### Hub-Spoke Coordination

- **Objective Decomposition**: ~100-500ms (depends on complexity)
- **Spoke Task Distribution**: ~50-100ms per spoke
- **Result Aggregation**: ~50-200ms (depends on spoke count)
- **End-to-End Latency**: ~1-5 seconds for typical objective

### Scaling Guidelines

#### Agent Scaling

```python
# Horizontal scaling: Add more agents
for i in range(10):
    manager.register_agent(
        agent_id=f"worker-{i:03d}",
        agent_type="Worker",
        capabilities=["general-purpose"],
        max_concurrent_tasks=5
    )

# Result: 10 agents × 5 tasks = 50 concurrent tasks
```

**Recommendations:**
- Start with 5-10 agents per agent type
- Scale to 50-100 agents for production workloads
- Monitor agent utilization and add capacity at 70% threshold

#### Redis Scaling

```yaml
# Redis configuration for production
redis:
  # Connection pooling
  max_connections: 100

  # Persistence
  save: "900 1 300 10 60 10000"

  # Memory
  maxmemory: 4gb
  maxmemory-policy: allkeys-lru

  # Performance
  tcp-backlog: 511
  timeout: 0
```

**Recommendations:**
- Use Redis Cluster for >10GB datasets
- Enable persistence (AOF or RDB) for production
- Monitor memory usage and set maxmemory policy

#### PostgreSQL Scaling

```yaml
# PostgreSQL configuration for production
postgresql:
  # Connection pooling
  max_connections: 100
  shared_buffers: 256MB

  # Performance
  effective_cache_size: 1GB
  work_mem: 4MB
  maintenance_work_mem: 64MB

  # Write-ahead log
  wal_buffers: 16MB
  checkpoint_completion_target: 0.9
```

**Recommendations:**
- Use connection pooling (pgBouncer or PgPool)
- Partition handoff_log table by workflow_id
- Archive old handoff records (>30 days)

#### Workflow Scaling

```python
# Optimize large workflows
workflow = Workflow(
    workflow_id="large-workflow-001",
    name="Large Workflow",
    timeout=14400  # 4 hours
)

# Break into smaller sub-workflows
for batch in range(10):
    sub_workflow = Workflow(
        workflow_id=f"batch-{batch:02d}",
        name=f"Batch {batch}"
    )
    # Add tasks...

    # Execute sub-workflow
    result = orchestrator.execute_workflow(sub_workflow.workflow_id)
```

**Recommendations:**
- Limit workflows to 50-100 tasks
- Use sub-workflows for larger processes
- Enable parallel execution where possible

### Resource Optimization

#### Memory Optimization

```python
# Configure resource limits appropriately
resource_limits = ResourceLimits(
    memory_mb=2048,  # Don't over-allocate
    cpu_cores=2,
    disk_mb=5120,
    network_mbps=100
)

# Monitor actual usage
usage = allocator.get_agent_usage("worker-001")
print(f"Memory utilization: {usage.memory_utilization:.1f}%")

# Adjust limits based on actual usage
if usage.memory_utilization < 50:
    # Reduce memory allocation
    new_limits = ResourceLimits(
        agent_id="worker-001",
        memory_mb=1024,  # Reduced
        cpu_cores=2,
        max_tasks=4
    )
```

#### CPU Optimization

```python
# Use appropriate CPU allocation
allocator.allocate(
    agent_id="worker-001",
    task_id="compute-intensive-001",
    cpu_cores=4.0,  # Allocate more for compute tasks
    memory_mb=2048,
    priority=Priority.HIGH
)

allocator.allocate(
    agent_id="worker-002",
    task_id="io-bound-001",
    cpu_cores=0.5,  # Allocate less for I/O tasks
    memory_mb=1024,
    priority=Priority.MEDIUM
)
```

#### Network Optimization

```python
# Batch Redis operations
pipeline = manager.redis_client.pipeline()
for i in range(100):
    pipeline.get(f"key-{i}")
results = pipeline.execute()

# Use Redis connection pooling
manager = DelegationManager(
    redis_url="redis://localhost:6379",
    connection_pool_size=50  # Increased pool
)
```

### Capacity Planning

#### Calculating Required Capacity

```python
# Estimate capacity requirements
def calculate_capacity(
    daily_workflows: int,
    avg_tasks_per_workflow: int,
    avg_task_duration_seconds: int,
    peak_multiplier: float = 2.0
) -> dict:
    """Calculate required agent capacity."""

    # Tasks per day
    daily_tasks = daily_workflows * avg_tasks_per_workflow

    # Tasks per hour (peak)
    peak_tasks_per_hour = (daily_tasks / 24) * peak_multiplier

    # Concurrent tasks (assuming 1 hour average)
    concurrent_tasks = (peak_tasks_per_hour * avg_task_duration_seconds) / 3600

    # Agent requirements (assuming 3 tasks per agent)
    required_agents = int(concurrent_tasks / 3) + 1

    return {
        "daily_workflows": daily_workflows,
        "daily_tasks": daily_tasks,
        "peak_tasks_per_hour": peak_tasks_per_hour,
        "concurrent_tasks": concurrent_tasks,
        "required_agents": required_agents
    }

# Example calculation
capacity = calculate_capacity(
    daily_workflows=1000,
    avg_tasks_per_workflow=10,
    avg_task_duration_seconds=600,  # 10 minutes
    peak_multiplier=2.0
)

print(f"Required agents: {capacity['required_agents']}")
```

---

## Development

### Code Structure

```
multi_agent_orchestration/
├── __init__.py                 # Package exports
├── task_orchestrator.py        # Workflow coordination
├── delegation_manager.py       # Task routing
├── workflow_engine.py          # Advanced workflows
├── resource_allocator.py       # Resource management
├── hub_spoke_coordinator.py    # Hub-spoke pattern
├── handoff_manager.py          # Context transfer
├── orchestration_cli.py        # CLI interface
├── requirements.txt            # Dependencies
├── README.md                   # This file
└── test_orchestration.py       # Tests
```

### Contributing Guidelines

1. **Fork the Repository**
   ```bash
   git clone https://github.com/Cybonto/devCrew_s1.git
   cd devCrew_s1/tools/multi_agent_orchestration
   ```

2. **Create Feature Branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make Changes**
   - Follow existing code style
   - Add tests for new features
   - Update documentation

4. **Run Quality Checks**
   ```bash
   # Format code
   black .
   isort .

   # Check style
   flake8

   # Type checking
   mypy . --ignore-missing-imports

   # Security scan
   bandit -r .

   # Run tests
   pytest -v --cov=.
   ```

5. **Commit Changes**
   ```bash
   git add .
   git commit -m "Add feature: your feature description"
   ```

6. **Push and Create PR**
   ```bash
   git push origin feature/your-feature-name
   # Create pull request on GitHub
   ```

### Code Quality Standards

#### Python Style Guide

Follow PEP 8 and Black formatting:

```python
# Good: Clear naming, type hints, docstrings
def register_agent(
    self,
    agent_id: str,
    agent_type: str,
    capabilities: List[str],
    max_concurrent_tasks: int = 3,
) -> bool:
    """
    Register an agent with the delegation manager.

    Args:
        agent_id: Unique agent identifier
        agent_type: Type/category of agent
        capabilities: List of agent capabilities
        max_concurrent_tasks: Maximum concurrent tasks

    Returns:
        True if registration successful

    Raises:
        ValueError: If validation fails
    """
    # Implementation...
    pass
```

#### Type Hints

Use type hints for all functions:

```python
from typing import List, Dict, Optional, Any

def process_workflow(
    workflow_id: str,
    tasks: List[Task],
    options: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Process workflow with tasks."""
    # Implementation...
    pass
```

#### Error Handling

```python
# Good: Specific exceptions with context
try:
    result = self.redis_client.get(key)
except RedisConnectionError as e:
    logger.error(f"Redis connection failed: {e}")
    raise
except RedisError as e:
    logger.error(f"Redis operation failed: {e}")
    raise

# Bad: Bare except
try:
    result = self.redis_client.get(key)
except:  # Don't do this
    pass
```

#### Logging

```python
import logging

logger = logging.getLogger(__name__)

# Use appropriate log levels
logger.debug("Detailed debugging information")
logger.info("General informational messages")
logger.warning("Warning messages for concerning situations")
logger.error("Error messages for failures")
logger.critical("Critical failures requiring immediate attention")
```

### Release Process

1. **Update Version**
   ```python
   # __init__.py
   __version__ = "1.1.0"
   ```

2. **Update Changelog**
   ```markdown
   ## [1.1.0] - 2025-12-01

   ### Added
   - New feature X
   - New feature Y

   ### Changed
   - Improved performance of Z

   ### Fixed
   - Bug in component A
   ```

3. **Tag Release**
   ```bash
   git tag -a v1.1.0 -m "Release version 1.1.0"
   git push origin v1.1.0
   ```

4. **Build Package**
   ```bash
   python -m build
   python -m twine upload dist/*
   ```

---

## License

This project is part of the devCrew_s1 repository.

**Project**: devCrew_s1
**Component**: Multi-Agent Orchestration Platform
**Tool ID**: TOOL-ORG-001
**Issue**: [#46](https://github.com/Cybonto/devCrew_s1/issues/46)

---

## Credits

Developed by the devCrew_s1 team as part of the multi-agent orchestration initiative.

### Contributors

- Core architecture and implementation
- Protocol integration
- Documentation and testing

### Technology Acknowledgments

- **Prefect**: Workflow orchestration framework
- **Celery**: Distributed task queue
- **Redis**: In-memory data store
- **PostgreSQL**: Relational database
- **Pydantic**: Data validation

---

## Support

For issues, questions, or contributions:

1. **GitHub Issues**: [devCrew_s1 Issues](https://github.com/Cybonto/devCrew_s1/issues)
2. **Documentation**: This README and inline code documentation
3. **Examples**: See Usage Examples section above

---

**Last Updated**: 2025-11-24
**Documentation Version**: 1.0.0
