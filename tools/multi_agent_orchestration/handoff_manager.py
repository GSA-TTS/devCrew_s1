"""
Handoff Manager - Seamless agent-to-agent handoffs with context preservation.

Implements agent context serialization, transfer, validation, rollback,
and audit trail for multi-agent orchestration workflows.

Issue #46: Multi-Agent Orchestration Platform - Handoff Manager
"""

import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor
from pydantic import BaseModel, Field, field_validator
from redis import Redis


class AgentContext(BaseModel):
    """
    Agent context model containing conversation, files, and state.

    This model encapsulates all information needed to transfer execution
    from one agent to another in a workflow.
    """

    agent_id: str = Field(..., description="Unique agent identifier")
    agent_type: str = Field(..., description="Type of agent (e.g., backend-engineer)")
    conversation_history: List[Dict[str, str]] = Field(
        default_factory=list,
        description="Conversation history with role and content",
    )
    files_created: List[str] = Field(
        default_factory=list,
        description="List of files created by agent",
    )
    files_modified: List[str] = Field(
        default_factory=list,
        description="List of files modified by agent",
    )
    state: Dict[str, Any] = Field(
        default_factory=dict,
        description="Agent state (tests_passing, coverage, etc.)",
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata for handoff",
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Context creation timestamp",
    )

    @field_validator("conversation_history")
    @classmethod
    def validate_conversation(cls, v: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Validate conversation history format."""
        for entry in v:
            if "role" not in entry or "content" not in entry:
                raise ValueError(
                    "Each conversation entry must have 'role' and 'content'"
                )
            if entry["role"] not in ["user", "assistant", "system"]:
                raise ValueError("Role must be one of: user, assistant, system")
        return v


class HandoffPrecondition(BaseModel):
    """
    Handoff validation rule model.

    Defines conditions that must be met before a handoff can occur.
    """

    condition_type: str = Field(
        ...,
        description="Type of condition (tests_passing, coverage, etc.)",
    )
    expected_value: Any = Field(
        ...,
        description="Expected value for the condition",
    )
    operator: str = Field(
        default="==",
        description="Comparison operator (==, !=, >=, <=, >, <, in, " "exists)",
    )
    required: bool = Field(
        default=True,
        description="Whether this condition is required for handoff",
    )
    error_message: Optional[str] = Field(
        default=None,
        description="Custom error message if condition fails",
    )

    @field_validator("operator")
    @classmethod
    def validate_operator(cls, v: str) -> str:
        """Validate operator."""
        valid_operators = {"==", "!=", ">=", "<=", ">", "<", "in", "exists"}
        if v not in valid_operators:
            raise ValueError(f"Operator must be one of {valid_operators}")
        return v


class HandoffResult(BaseModel):
    """
    Handoff execution result model.

    Contains information about the handoff execution including success,
    validation results, and any errors.
    """

    handoff_id: str = Field(..., description="Unique handoff identifier")
    workflow_id: str = Field(..., description="Workflow identifier")
    source_agent_id: str = Field(..., description="Source agent ID")
    source_agent_type: str = Field(..., description="Source agent type")
    target_agent_id: Optional[str] = Field(
        default=None,
        description="Target agent ID (assigned after handoff)",
    )
    target_agent_type: str = Field(..., description="Target agent type")
    success: bool = Field(..., description="Whether handoff succeeded")
    validation_passed: bool = Field(
        ...,
        description="Whether precondition validation passed",
    )
    failed_preconditions: List[str] = Field(
        default_factory=list,
        description="List of failed precondition messages",
    )
    error: Optional[str] = Field(
        default=None,
        description="Error message if handoff failed",
    )
    context_transferred: bool = Field(
        default=False,
        description="Whether context was successfully transferred",
    )
    rollback_performed: bool = Field(
        default=False,
        description="Whether rollback was performed",
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Handoff creation timestamp",
    )
    completed_at: Optional[datetime] = Field(
        default=None,
        description="Handoff completion timestamp",
    )


class HandoffManager:
    """
    Manage agent-to-agent handoffs with context preservation.

    Handles context serialization, transfer, validation, rollback,
    and maintains an audit trail of all handoffs.
    """

    def __init__(
        self,
        redis_client: Optional[Redis] = None,
        postgres_config: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize the handoff manager.

        Args:
            redis_client: Redis client for temporary context storage
            postgres_config: PostgreSQL configuration for audit trail
                {
                    "host": "localhost",
                    "port": 5432,
                    "database": "multi_agent_platform",
                    "user": "postgres",
                    "password": "password",
                    "minconn": 1,
                    "maxconn": 10
                }
        """
        self.redis_client = redis_client
        self.postgres_config = postgres_config
        self.pg_pool: Optional[pool.SimpleConnectionPool] = None

        # Initialize PostgreSQL connection pool
        if postgres_config:
            self._initialize_postgres()

    def _initialize_postgres(self) -> None:
        """Initialize PostgreSQL connection pool and create tables."""
        if not self.postgres_config:
            return

        try:
            # Create connection pool
            self.pg_pool = pool.SimpleConnectionPool(
                self.postgres_config.get("minconn", 1),
                self.postgres_config.get("maxconn", 10),
                host=self.postgres_config["host"],
                port=self.postgres_config.get("port", 5432),
                database=self.postgres_config["database"],
                user=self.postgres_config["user"],
                password=self.postgres_config["password"],
            )

            # Create tables if they don't exist
            self._create_tables()

        except psycopg2.Error as e:
            raise RuntimeError(f"Failed to initialize PostgreSQL: {e}") from e

    def _create_tables(self) -> None:
        """Create handoff audit tables if they don't exist."""
        if not self.pg_pool:
            return

        conn = None
        try:
            conn = self.pg_pool.getconn()
            with conn.cursor() as cursor:
                # Create handoffs table
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS handoffs (
                        handoff_id VARCHAR(255) PRIMARY KEY,
                        workflow_id VARCHAR(255) NOT NULL,
                        source_agent_id VARCHAR(255) NOT NULL,
                        source_agent_type VARCHAR(100) NOT NULL,
                        target_agent_id VARCHAR(255),
                        target_agent_type VARCHAR(100) NOT NULL,
                        context_data JSONB NOT NULL,
                        preconditions JSONB,
                        validation_result JSONB NOT NULL,
                        success BOOLEAN NOT NULL,
                        error TEXT,
                        context_transferred BOOLEAN DEFAULT FALSE,
                        rollback_performed BOOLEAN DEFAULT FALSE,
                        created_at TIMESTAMP WITH TIME ZONE NOT NULL,
                        completed_at TIMESTAMP WITH TIME ZONE,
                        CONSTRAINT workflow_id_idx
                            CHECK (workflow_id IS NOT NULL AND workflow_id != '')
                    );
                """
                )

                # Create indexes
                cursor.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_handoffs_workflow_id
                    ON handoffs(workflow_id);
                """
                )

                cursor.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_handoffs_source_agent
                    ON handoffs(source_agent_id);
                """
                )

                cursor.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_handoffs_target_agent
                    ON handoffs(target_agent_id);
                """
                )

                cursor.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_handoffs_created_at
                    ON handoffs(created_at);
                """
                )

                conn.commit()

        except psycopg2.Error as e:
            if conn:
                conn.rollback()
            raise RuntimeError(f"Failed to create tables: {e}") from e
        finally:
            if conn:
                self.pg_pool.putconn(conn)

    def create_context(
        self,
        agent_id: str,
        agent_type: str,
        conversation: List[Dict[str, str]],
        files: Dict[str, List[str]],
        state: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> AgentContext:
        """
        Create agent context from components.

        Args:
            agent_id: Agent identifier
            agent_type: Type of agent
            conversation: Conversation history
            files: Dictionary with 'created' and 'modified' file lists
            state: Agent state
            metadata: Additional metadata

        Returns:
            AgentContext object

        Raises:
            ValueError: If required fields are missing
        """
        if not agent_id:
            raise ValueError("agent_id is required")
        if not agent_type:
            raise ValueError("agent_type is required")

        return AgentContext(
            agent_id=agent_id,
            agent_type=agent_type,
            conversation_history=conversation,
            files_created=files.get("created", []),
            files_modified=files.get("modified", []),
            state=state,
            metadata=metadata or {},
        )

    def serialize_context(self, context: AgentContext) -> str:
        """
        Serialize agent context to JSON string.

        Args:
            context: AgentContext object

        Returns:
            JSON string representation

        Raises:
            ValueError: If serialization fails
        """
        try:
            # Convert to dict and handle datetime serialization
            context_dict = context.model_dump()
            context_dict["created_at"] = context.created_at.isoformat()

            return json.dumps(context_dict, ensure_ascii=False)

        except (TypeError, ValueError) as e:
            raise ValueError(f"Failed to serialize context: {e}") from e

    def deserialize_context(self, data: str) -> AgentContext:
        """
        Deserialize agent context from JSON string.

        Args:
            data: JSON string

        Returns:
            AgentContext object

        Raises:
            ValueError: If deserialization fails
        """
        try:
            context_dict = json.loads(data)

            # Handle datetime deserialization
            if "created_at" in context_dict:
                context_dict["created_at"] = datetime.fromisoformat(
                    context_dict["created_at"]
                )

            return AgentContext(**context_dict)

        except (json.JSONDecodeError, TypeError, ValueError) as e:
            raise ValueError(f"Failed to deserialize context: {e}") from e

    def validate_preconditions(
        self, context: AgentContext, preconditions: List[HandoffPrecondition]
    ) -> Tuple[bool, List[str]]:
        """
        Validate handoff preconditions against agent context.

        Args:
            context: Agent context to validate
            preconditions: List of preconditions to check

        Returns:
            Tuple of (all_passed, failed_messages)
        """
        failed_messages = []

        for precondition in preconditions:
            # Get actual value from context state
            actual_value = context.state.get(precondition.condition_type)

            passed = self._evaluate_condition(
                actual_value,
                precondition.expected_value,
                precondition.operator,
            )

            if not passed and precondition.required:
                error_msg = precondition.error_message or (
                    f"Condition '{precondition.condition_type}' failed: "
                    f"expected {precondition.operator} "
                    f"{precondition.expected_value}, got {actual_value}"
                )
                failed_messages.append(error_msg)

        return len(failed_messages) == 0, failed_messages

    def _evaluate_condition(self, actual: Any, expected: Any, operator: str) -> bool:
        """
        Evaluate a single condition.

        Args:
            actual: Actual value
            expected: Expected value
            operator: Comparison operator

        Returns:
            True if condition passes
        """
        try:
            if operator == "exists":
                return actual is not None

            if actual is None:
                return False

            if operator == "==":
                return actual == expected
            elif operator == "!=":
                return actual != expected
            elif operator == ">=":
                return float(actual) >= float(expected)
            elif operator == "<=":
                return float(actual) <= float(expected)
            elif operator == ">":
                return float(actual) > float(expected)
            elif operator == "<":
                return float(actual) < float(expected)
            elif operator == "in":
                return actual in expected

            return False

        except (TypeError, ValueError):
            return False

    def handoff(
        self,
        source_context: AgentContext,
        target_agent_type: str,
        workflow_id: str,
        preconditions: Optional[List[HandoffPrecondition]] = None,
        target_agent_id: Optional[str] = None,
    ) -> HandoffResult:
        """
        Perform agent handoff with validation and context transfer.

        Args:
            source_context: Source agent context
            target_agent_type: Type of target agent
            workflow_id: Workflow identifier
            preconditions: List of preconditions to validate
            target_agent_id: Optional target agent ID (generated if not
                provided)

        Returns:
            HandoffResult object

        Raises:
            ValueError: If required fields are missing
            RuntimeError: If handoff fails critically
        """
        if not workflow_id:
            raise ValueError("workflow_id is required")

        handoff_id = str(uuid.uuid4())
        target_agent_id = (
            target_agent_id or f"{target_agent_type}-{uuid.uuid4().hex[:8]}"
        )

        # Initialize result
        result = HandoffResult(
            handoff_id=handoff_id,
            workflow_id=workflow_id,
            source_agent_id=source_context.agent_id,
            source_agent_type=source_context.agent_type,
            target_agent_id=target_agent_id,
            target_agent_type=target_agent_type,
            success=False,
            validation_passed=False,
        )

        try:
            # Validate preconditions
            if preconditions:
                validation_passed, failed_messages = self.validate_preconditions(
                    source_context, preconditions
                )

                result.validation_passed = validation_passed
                result.failed_preconditions = failed_messages

                if not validation_passed:
                    result.error = (
                        f"Precondition validation failed: "
                        f"{'; '.join(failed_messages)}"
                    )
                    self._log_handoff(result, source_context, preconditions)
                    return result
            else:
                result.validation_passed = True

            # Transfer context
            transfer_success = self.transfer_context(
                source_context.agent_id, target_agent_id, source_context
            )

            result.context_transferred = transfer_success

            if not transfer_success:
                result.error = "Context transfer failed"
                self._log_handoff(result, source_context, preconditions)
                return result

            # Handoff successful
            result.success = True
            result.completed_at = datetime.now(timezone.utc)

            # Log successful handoff
            self._log_handoff(result, source_context, preconditions)

            return result

        except Exception as e:
            # Handle critical failure
            result.error = f"Handoff failed: {str(e)}"

            # Attempt rollback
            try:
                rollback_success = self.rollback(handoff_id)
                result.rollback_performed = rollback_success
            except Exception:
                pass

            # Log failed handoff
            self._log_handoff(result, source_context, preconditions)

            raise RuntimeError(f"Critical handoff failure: {e}") from e

    def transfer_context(
        self, source_agent_id: str, target_agent_id: str, context: AgentContext
    ) -> bool:
        """
        Transfer context from source to target agent via Redis.

        Args:
            source_agent_id: Source agent identifier
            target_agent_id: Target agent identifier
            context: Agent context to transfer

        Returns:
            True if transfer successful
        """
        if not self.redis_client:
            # No Redis, context transfer not available
            return False

        try:
            # Serialize context
            serialized_context = self.serialize_context(context)

            # Store in Redis with target agent key
            context_key = f"handoff:context:{target_agent_id}"
            self.redis_client.setex(
                context_key,
                3600,  # 1 hour expiration
                serialized_context,
            )

            # Store metadata for tracking
            metadata_key = f"handoff:metadata:{target_agent_id}"
            metadata = {
                "source_agent_id": source_agent_id,
                "target_agent_id": target_agent_id,
                "transferred_at": datetime.now(timezone.utc).isoformat(),
            }
            self.redis_client.setex(
                metadata_key,
                3600,
                json.dumps(metadata),
            )

            return True

        except Exception:
            return False

    def get_transferred_context(self, agent_id: str) -> Optional[AgentContext]:
        """
        Retrieve transferred context for an agent.

        Args:
            agent_id: Agent identifier

        Returns:
            AgentContext if found, None otherwise
        """
        if not self.redis_client:
            return None

        try:
            context_key = f"handoff:context:{agent_id}"
            serialized_context = self.redis_client.get(context_key)

            if not serialized_context:
                return None

            return self.deserialize_context(serialized_context.decode("utf-8"))

        except Exception:
            return None

    def rollback(self, handoff_id: str) -> bool:
        """
        Rollback a handoff operation.

        Removes transferred context from Redis and marks handoff as
        rolled back.

        Args:
            handoff_id: Handoff identifier

        Returns:
            True if rollback successful
        """
        if not self.pg_pool:
            return False

        conn = None
        try:
            conn = self.pg_pool.getconn()
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                # Get handoff details
                cursor.execute(
                    "SELECT target_agent_id FROM handoffs " "WHERE handoff_id = %s",
                    (handoff_id,),
                )
                result = cursor.fetchone()

                if not result:
                    return False

                target_agent_id = result["target_agent_id"]

                # Remove context from Redis
                if self.redis_client and target_agent_id:
                    context_key = f"handoff:context:{target_agent_id}"
                    metadata_key = f"handoff:metadata:{target_agent_id}"
                    self.redis_client.delete(context_key)
                    self.redis_client.delete(metadata_key)

                # Mark as rolled back
                cursor.execute(
                    """
                    UPDATE handoffs
                    SET rollback_performed = TRUE,
                        completed_at = %s
                    WHERE handoff_id = %s
                    """,
                    (datetime.now(timezone.utc), handoff_id),
                )

                conn.commit()
                return True

        except psycopg2.Error:
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                self.pg_pool.putconn(conn)

    def get_handoff_history(
        self, workflow_id: str, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get handoff history for a workflow.

        Args:
            workflow_id: Workflow identifier
            limit: Maximum number of handoffs to return

        Returns:
            List of handoff records
        """
        if not self.pg_pool:
            return []

        conn = None
        try:
            conn = self.pg_pool.getconn()
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(
                    """
                    SELECT
                        handoff_id,
                        workflow_id,
                        source_agent_id,
                        source_agent_type,
                        target_agent_id,
                        target_agent_type,
                        success,
                        context_transferred,
                        rollback_performed,
                        created_at,
                        completed_at
                    FROM handoffs
                    WHERE workflow_id = %s
                    ORDER BY created_at DESC
                    LIMIT %s
                    """,
                    (workflow_id, limit),
                )

                results = cursor.fetchall()

                return [
                    {
                        **dict(row),
                        "created_at": (
                            row["created_at"].isoformat() if row["created_at"] else None
                        ),
                        "completed_at": (
                            row["completed_at"].isoformat()
                            if row["completed_at"]
                            else None
                        ),
                    }
                    for row in results
                ]

        except psycopg2.Error:
            return []
        finally:
            if conn:
                self.pg_pool.putconn(conn)

    def get_handoff_audit(self, handoff_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed audit information for a specific handoff.

        Args:
            handoff_id: Handoff identifier

        Returns:
            Detailed handoff audit record or None if not found
        """
        if not self.pg_pool:
            return None

        conn = None
        try:
            conn = self.pg_pool.getconn()
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(
                    """
                    SELECT *
                    FROM handoffs
                    WHERE handoff_id = %s
                    """,
                    (handoff_id,),
                )

                result = cursor.fetchone()

                if not result:
                    return None

                return {
                    **dict(result),
                    "created_at": (
                        result["created_at"].isoformat()
                        if result["created_at"]
                        else None
                    ),
                    "completed_at": (
                        result["completed_at"].isoformat()
                        if result["completed_at"]
                        else None
                    ),
                }

        except psycopg2.Error:
            return None
        finally:
            if conn:
                self.pg_pool.putconn(conn)

    def _log_handoff(
        self,
        result: HandoffResult,
        context: AgentContext,
        preconditions: Optional[List[HandoffPrecondition]],
    ) -> None:
        """
        Log handoff to PostgreSQL audit trail.

        Args:
            result: Handoff result
            context: Agent context
            preconditions: List of preconditions
        """
        if not self.pg_pool:
            return

        conn = None
        try:
            conn = self.pg_pool.getconn()
            with conn.cursor() as cursor:
                # Prepare data
                context_data = json.loads(self.serialize_context(context))
                preconditions_data = (
                    [p.model_dump() for p in preconditions] if preconditions else None
                )
                validation_result = {
                    "passed": result.validation_passed,
                    "failed_preconditions": result.failed_preconditions,
                }

                # Insert handoff record
                cursor.execute(
                    """
                    INSERT INTO handoffs (
                        handoff_id,
                        workflow_id,
                        source_agent_id,
                        source_agent_type,
                        target_agent_id,
                        target_agent_type,
                        context_data,
                        preconditions,
                        validation_result,
                        success,
                        error,
                        context_transferred,
                        rollback_performed,
                        created_at,
                        completed_at
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                    """,
                    (
                        result.handoff_id,
                        result.workflow_id,
                        result.source_agent_id,
                        result.source_agent_type,
                        result.target_agent_id,
                        result.target_agent_type,
                        json.dumps(context_data),
                        json.dumps(preconditions_data) if preconditions_data else None,
                        json.dumps(validation_result),
                        result.success,
                        result.error,
                        result.context_transferred,
                        result.rollback_performed,
                        result.created_at,
                        result.completed_at,
                    ),
                )

                conn.commit()

        except psycopg2.Error:
            if conn:
                conn.rollback()
        finally:
            if conn:
                self.pg_pool.putconn(conn)

    def close(self) -> None:
        """Close PostgreSQL connection pool."""
        if self.pg_pool:
            self.pg_pool.closeall()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
