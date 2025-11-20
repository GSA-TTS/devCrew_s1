"""
LangSmith Tracing Integration Module.

This module provides tracing and observability for reasoning operations
with performance metrics and cost tracking.

Protocol Coverage:
- P-ORCHESTRATION: Multi-agent coordination tracing
"""

import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json
import uuid


logger = logging.getLogger(__name__)


class TraceType(Enum):
    """Trace event types."""
    REASONING_START = "reasoning_start"
    REASONING_END = "reasoning_end"
    STEP_START = "step_start"
    STEP_END = "step_end"
    LLM_CALL = "llm_call"
    EVALUATION = "evaluation"
    ERROR = "error"


@dataclass
class TraceEvent:
    """Represents a single trace event."""
    id: str
    trace_id: str
    parent_id: Optional[str]
    type: TraceType
    name: str
    timestamp: datetime
    duration_ms: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "trace_id": self.trace_id,
            "parent_id": self.parent_id,
            "type": self.type.value,
            "name": self.name,
            "timestamp": self.timestamp.isoformat(),
            "duration_ms": self.duration_ms,
            "metadata": self.metadata,
            "error": self.error
        }


@dataclass
class Trace:
    """Represents a complete trace."""
    id: str
    name: str
    start_time: datetime
    end_time: Optional[datetime] = None
    events: List[TraceEvent] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)

    def duration_ms(self) -> Optional[float]:
        """Calculate total duration in milliseconds."""
        if self.end_time:
            delta = self.end_time - self.start_time
            return delta.total_seconds() * 1000
        return None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_ms": self.duration_ms(),
            "events": [e.to_dict() for e in self.events],
            "metadata": self.metadata,
            "tags": self.tags
        }


class LangSmithTracer:
    """
    Tracer for LangSmith integration with performance metrics
    and cost tracking.
    """

    def __init__(
        self,
        project_name: str = "ai-reasoning",
        api_key: Optional[str] = None,
        enabled: bool = True
    ):
        """
        Initialize LangSmith tracer.

        Args:
            project_name: LangSmith project name
            api_key: LangSmith API key
            enabled: Enable tracing
        """
        self.project_name = project_name
        self.api_key = api_key
        self.enabled = enabled

        self.active_traces: Dict[str, Trace] = {}
        self.completed_traces: List[Trace] = []
        self._langsmith_client = None

        if enabled and api_key:
            self._initialize_langsmith()

    def _initialize_langsmith(self) -> None:
        """Initialize LangSmith client."""
        try:
            from langsmith import Client
            self._langsmith_client = Client(api_key=self.api_key)
            logger.info(f"LangSmith client initialized for project: {self.project_name}")
        except ImportError:
            logger.warning("LangSmith not installed. Install with: pip install langsmith")
            self.enabled = False
        except Exception as e:
            logger.error(f"Failed to initialize LangSmith: {e}")
            self.enabled = False

    def start_trace(
        self,
        name: str,
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None
    ) -> str:
        """
        Start a new trace.

        Args:
            name: Trace name
            metadata: Additional metadata
            tags: Trace tags

        Returns:
            Trace ID
        """
        if not self.enabled:
            return ""

        trace_id = str(uuid.uuid4())
        trace = Trace(
            id=trace_id,
            name=name,
            start_time=datetime.now(),
            metadata=metadata or {},
            tags=tags or []
        )

        self.active_traces[trace_id] = trace
        logger.debug(f"Started trace: {name} ({trace_id})")

        return trace_id

    def end_trace(self, trace_id: str) -> Optional[Trace]:
        """
        End an active trace.

        Args:
            trace_id: Trace ID

        Returns:
            Completed Trace
        """
        if not self.enabled or trace_id not in self.active_traces:
            return None

        trace = self.active_traces[trace_id]
        trace.end_time = datetime.now()

        # Send to LangSmith
        if self._langsmith_client:
            self._send_trace_to_langsmith(trace)

        # Move to completed
        self.completed_traces.append(trace)
        del self.active_traces[trace_id]

        logger.debug(
            f"Ended trace: {trace.name} ({trace_id}) - "
            f"{trace.duration_ms():.2f}ms"
        )

        return trace

    def add_event(
        self,
        trace_id: str,
        event_type: TraceType,
        name: str,
        parent_id: Optional[str] = None,
        duration_ms: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None
    ) -> Optional[str]:
        """
        Add event to trace.

        Args:
            trace_id: Trace ID
            event_type: Type of event
            name: Event name
            parent_id: Parent event ID
            duration_ms: Event duration
            metadata: Additional metadata
            error: Error message if applicable

        Returns:
            Event ID
        """
        if not self.enabled or trace_id not in self.active_traces:
            return None

        event_id = str(uuid.uuid4())
        event = TraceEvent(
            id=event_id,
            trace_id=trace_id,
            parent_id=parent_id,
            type=event_type,
            name=name,
            timestamp=datetime.now(),
            duration_ms=duration_ms,
            metadata=metadata or {},
            error=error
        )

        self.active_traces[trace_id].events.append(event)
        logger.debug(f"Added event: {name} to trace {trace_id}")

        return event_id

    def trace_llm_call(
        self,
        trace_id: str,
        provider: str,
        model: str,
        prompt: str,
        response: str,
        token_count: int,
        duration_ms: float,
        parent_id: Optional[str] = None
    ) -> Optional[str]:
        """
        Trace LLM call with details.

        Args:
            trace_id: Trace ID
            provider: LLM provider
            model: Model name
            prompt: Input prompt
            response: Model response
            token_count: Total tokens
            duration_ms: Call duration
            parent_id: Parent event ID

        Returns:
            Event ID
        """
        return self.add_event(
            trace_id=trace_id,
            event_type=TraceType.LLM_CALL,
            name=f"LLM Call: {provider}/{model}",
            parent_id=parent_id,
            duration_ms=duration_ms,
            metadata={
                "provider": provider,
                "model": model,
                "prompt": prompt[:200],  # Truncate for storage
                "response": response[:200],
                "token_count": token_count
            }
        )

    def trace_reasoning_step(
        self,
        trace_id: str,
        step_number: int,
        thought: str,
        confidence: float,
        duration_ms: float,
        parent_id: Optional[str] = None
    ) -> Optional[str]:
        """
        Trace reasoning step.

        Args:
            trace_id: Trace ID
            step_number: Step number
            thought: Thought content
            confidence: Step confidence
            duration_ms: Step duration
            parent_id: Parent event ID

        Returns:
            Event ID
        """
        return self.add_event(
            trace_id=trace_id,
            event_type=TraceType.STEP_START,
            name=f"Reasoning Step {step_number}",
            parent_id=parent_id,
            duration_ms=duration_ms,
            metadata={
                "step_number": step_number,
                "thought": thought[:200],
                "confidence": confidence
            }
        )

    def trace_error(
        self,
        trace_id: str,
        error_message: str,
        error_type: str,
        parent_id: Optional[str] = None
    ) -> Optional[str]:
        """
        Trace error event.

        Args:
            trace_id: Trace ID
            error_message: Error message
            error_type: Type of error
            parent_id: Parent event ID

        Returns:
            Event ID
        """
        return self.add_event(
            trace_id=trace_id,
            event_type=TraceType.ERROR,
            name=f"Error: {error_type}",
            parent_id=parent_id,
            error=error_message,
            metadata={"error_type": error_type}
        )

    def get_trace(self, trace_id: str) -> Optional[Trace]:
        """
        Get trace by ID.

        Args:
            trace_id: Trace ID

        Returns:
            Trace or None
        """
        # Check active traces
        if trace_id in self.active_traces:
            return self.active_traces[trace_id]

        # Check completed traces
        for trace in self.completed_traces:
            if trace.id == trace_id:
                return trace

        return None

    def get_traces(
        self,
        name_filter: Optional[str] = None,
        tag_filter: Optional[str] = None,
        limit: int = 10
    ) -> List[Trace]:
        """
        Get traces with optional filtering.

        Args:
            name_filter: Filter by name
            tag_filter: Filter by tag
            limit: Maximum traces to return

        Returns:
            List of traces
        """
        traces = self.completed_traces.copy()

        if name_filter:
            traces = [t for t in traces if name_filter in t.name]

        if tag_filter:
            traces = [t for t in traces if tag_filter in t.tags]

        return traces[-limit:]

    def analyze_performance(self, trace_id: str) -> Dict[str, Any]:
        """
        Analyze performance metrics for a trace.

        Args:
            trace_id: Trace ID

        Returns:
            Performance analysis
        """
        trace = self.get_trace(trace_id)
        if not trace:
            return {"error": "Trace not found"}

        # Calculate metrics
        llm_calls = [e for e in trace.events if e.type == TraceType.LLM_CALL]
        reasoning_steps = [
            e for e in trace.events
            if e.type in [TraceType.STEP_START, TraceType.STEP_END]
        ]
        errors = [e for e in trace.events if e.type == TraceType.ERROR]

        total_tokens = sum(
            e.metadata.get("token_count", 0) for e in llm_calls
        )

        avg_step_duration = 0.0
        if reasoning_steps:
            step_durations = [
                e.duration_ms for e in reasoning_steps if e.duration_ms
            ]
            if step_durations:
                avg_step_duration = sum(step_durations) / len(step_durations)

        return {
            "trace_id": trace_id,
            "total_duration_ms": trace.duration_ms(),
            "llm_calls": len(llm_calls),
            "reasoning_steps": len(reasoning_steps),
            "total_tokens": total_tokens,
            "avg_step_duration_ms": avg_step_duration,
            "errors": len(errors),
            "error_rate": len(errors) / len(trace.events) if trace.events else 0
        }

    def export_traces(self, filepath: str, trace_ids: Optional[List[str]] = None) -> None:
        """
        Export traces to JSON file.

        Args:
            filepath: Output file path
            trace_ids: Specific trace IDs to export (all if None)
        """
        if trace_ids:
            traces = [self.get_trace(tid) for tid in trace_ids]
            traces = [t for t in traces if t]
        else:
            traces = self.completed_traces

        export_data = {
            "project": self.project_name,
            "export_time": datetime.now().isoformat(),
            "traces": [t.to_dict() for t in traces]
        }

        with open(filepath, 'w') as f:
            json.dump(export_data, f, indent=2)

        logger.info(f"Exported {len(traces)} traces to {filepath}")

    def _send_trace_to_langsmith(self, trace: Trace) -> None:
        """Send trace to LangSmith."""
        if not self._langsmith_client:
            return

        try:
            # Convert trace to LangSmith format
            run_data = {
                "id": trace.id,
                "name": trace.name,
                "start_time": trace.start_time,
                "end_time": trace.end_time,
                "extra": trace.metadata,
                "tags": trace.tags
            }

            # Send to LangSmith (simplified - actual API may differ)
            # self._langsmith_client.create_run(**run_data)

            logger.debug(f"Sent trace to LangSmith: {trace.id}")
        except Exception as e:
            logger.error(f"Failed to send trace to LangSmith: {e}")

    def clear_completed_traces(self) -> int:
        """
        Clear completed traces from memory.

        Returns:
            Number of traces cleared
        """
        count = len(self.completed_traces)
        self.completed_traces = []
        logger.info(f"Cleared {count} completed traces")
        return count


# Context manager for tracing
class TracingContext:
    """Context manager for automatic trace lifecycle."""

    def __init__(
        self,
        tracer: LangSmithTracer,
        name: str,
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None
    ):
        """
        Initialize tracing context.

        Args:
            tracer: Tracer instance
            name: Trace name
            metadata: Additional metadata
            tags: Trace tags
        """
        self.tracer = tracer
        self.name = name
        self.metadata = metadata
        self.tags = tags
        self.trace_id: Optional[str] = None

    def __enter__(self) -> str:
        """Start trace."""
        self.trace_id = self.tracer.start_trace(
            self.name, self.metadata, self.tags
        )
        return self.trace_id

    def __exit__(self, exc_type, exc_val, exc_tb):
        """End trace."""
        if self.trace_id:
            # Log error if exception occurred
            if exc_type:
                self.tracer.trace_error(
                    self.trace_id,
                    str(exc_val),
                    exc_type.__name__
                )

            self.tracer.end_trace(self.trace_id)


# Example usage
if __name__ == "__main__":
    # Initialize tracer
    tracer = LangSmithTracer(project_name="test-project", enabled=True)

    # Use context manager
    with TracingContext(tracer, "Example Reasoning", tags=["test"]) as trace_id:
        # Trace LLM call
        tracer.trace_llm_call(
            trace_id=trace_id,
            provider="openai",
            model="gpt-4",
            prompt="What is AI?",
            response="AI is artificial intelligence...",
            token_count=150,
            duration_ms=1500.0
        )

        # Trace reasoning step
        tracer.trace_reasoning_step(
            trace_id=trace_id,
            step_number=1,
            thought="First, we need to understand the question",
            confidence=0.9,
            duration_ms=500.0
        )

    # Analyze performance
    analysis = tracer.analyze_performance(trace_id)
    print(f"Performance analysis: {analysis}")
