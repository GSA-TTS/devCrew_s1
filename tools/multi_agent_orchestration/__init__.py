"""
Multi-Agent Orchestration & Task Delegation Platform.

This package provides a comprehensive platform for orchestrating multi-agent
workflows with intelligent task delegation, resource management, and
hub-and-spoke coordination patterns.

Core Components:
    - Task Orchestrator: Prefect-based workflow coordination
    - Delegation Manager: Capability-based task routing
    - Workflow Engine: Sequential, parallel, and conditional execution
    - Resource Allocator: Agent resource management
    - Hub-and-Spoke Coordinator: Hierarchical agent coordination
    - Handoff Manager: Agent-to-agent context transfer
    - CLI Interface: Command-line workflow management

Protocols Supported:
    - CA-CS-NotifyHuman: Human notifications
    - P-DELEGATION-DEFAULT: Default task delegation
    - P-HANDOFF: Agent-to-agent handoffs
    - P-HUB-SPOKE-COORDINATION: Hierarchical coordination
    - P-ORCHESTRATION: Multi-agent workflow orchestration
    - P-RESOURCE: Resource allocation and tracking
    - P-SYSTEM-NOTIFY: System-level notifications
"""

__version__ = "1.0.0"
__author__ = "devCrew_s1"

from .delegation_manager import (AgentCapability, AgentMatch,
                                 DelegationManager, TaskRequest)
from .handoff_manager import AgentContext, HandoffManager, HandoffResult
from .hub_spoke_coordinator import HubAgent, HubSpokeCoordinator, SpokeAgent
from .resource_allocator import (Priority, ResourceAllocator, ResourceLimits,
                                 ResourceReservation, ResourceUsage,
                                 TaskAllocation)
from .task_orchestrator import Task, TaskOrchestrator, Workflow
from .workflow_engine import WorkflowEngine, WorkflowStatus

__all__ = [
    "TaskOrchestrator",
    "Workflow",
    "Task",
    "DelegationManager",
    "AgentCapability",
    "TaskRequest",
    "AgentMatch",
    "WorkflowEngine",
    "WorkflowStatus",
    "ResourceAllocator",
    "ResourceLimits",
    "ResourceUsage",
    "ResourceReservation",
    "TaskAllocation",
    "Priority",
    "HubSpokeCoordinator",
    "HubAgent",
    "SpokeAgent",
    "HandoffManager",
    "AgentContext",
    "HandoffResult",
]
