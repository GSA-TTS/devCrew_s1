"""
Graph Builder for devCrew_s1 Knowledge Graph Management Platform.

This module provides Neo4j graph database operations including schema creation,
node/relationship management, and graph querying capabilities.

Part of TOOL-KNOWLEDGE-001 (Issue #54)
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from neo4j import GraphDatabase
from neo4j.exceptions import (AuthError, CypherSyntaxError, Neo4jError,
                              ServiceUnavailable)
from pydantic import BaseModel, Field, field_validator
from tenacity import (retry, retry_if_exception_type, stop_after_attempt,
                      wait_exponential)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GraphBuilderConfig(BaseModel):
    """Configuration for Neo4j graph builder."""

    neo4j_uri: str = Field(
        ..., description="Neo4j database URI (e.g., bolt://localhost:7687)"
    )
    auth: Tuple[str, str] = Field(
        ..., description="Authentication tuple (username, password)"
    )
    database: str = Field(default="neo4j", description="Database name")
    batch_size: int = Field(
        default=1000, gt=0, description="Batch size for bulk operations"
    )
    enable_constraints: bool = Field(
        default=True, description="Enable automatic constraint creation"
    )
    max_connection_lifetime: int = Field(
        default=3600, description="Max connection lifetime in seconds"
    )
    max_connection_pool_size: int = Field(
        default=50, description="Max connection pool size"
    )
    connection_timeout: float = Field(
        default=30.0, description="Connection timeout in seconds"
    )

    @field_validator("neo4j_uri")
    @classmethod
    def validate_uri(cls, v: str) -> str:
        """Validate Neo4j URI format."""
        if not v.startswith(("bolt://", "neo4j://", "bolt+s://", "neo4j+s://")):
            raise ValueError(
                "neo4j_uri must start with bolt://, neo4j://, "
                "bolt+s://, or neo4j+s://"
            )
        return v


class GraphSchema(BaseModel):
    """Schema definition for graph database."""

    node_types: List[str] = Field(
        default_factory=list, description="List of node label types"
    )
    relationship_types: List[str] = Field(
        default_factory=list, description="List of relationship types"
    )
    properties: Dict[str, List[str]] = Field(
        default_factory=dict,
        description="Properties for each node type",
    )
    constraints: List[str] = Field(
        default_factory=list, description="Constraint definitions (Cypher)"
    )
    indexes: List[str] = Field(
        default_factory=list, description="Index definitions (Cypher)"
    )


class GraphNode(BaseModel):
    """Representation of a graph node."""

    id: str = Field(..., description="Unique node identifier")
    labels: List[str] = Field(..., description="Node labels")
    properties: Dict[str, Any] = Field(
        default_factory=dict, description="Node properties"
    )

    @field_validator("labels")
    @classmethod
    def validate_labels(cls, v: List[str]) -> List[str]:
        """Ensure at least one label is provided."""
        if not v:
            raise ValueError("Node must have at least one label")
        return v

    def to_dict(self) -> Dict[str, Any]:
        """Convert node to dictionary representation."""
        return {
            "id": self.id,
            "labels": self.labels,
            "properties": self.properties,
        }


class GraphRelationship(BaseModel):
    """Representation of a graph relationship."""

    source_id: str = Field(..., description="Source node ID")
    target_id: str = Field(..., description="Target node ID")
    rel_type: str = Field(..., description="Relationship type")
    properties: Dict[str, Any] = Field(
        default_factory=dict, description="Relationship properties"
    )

    @field_validator("rel_type")
    @classmethod
    def validate_rel_type(cls, v: str) -> str:
        """Ensure relationship type is uppercase."""
        return v.upper()

    def to_dict(self) -> Dict[str, Any]:
        """Convert relationship to dictionary representation."""
        return {
            "source_id": self.source_id,
            "target_id": self.target_id,
            "rel_type": self.rel_type,
            "properties": self.properties,
        }


class GraphBuilderError(Exception):
    """Base exception for graph builder errors."""

    pass


class Neo4jConnectionError(GraphBuilderError):
    """Exception raised for Neo4j connection issues."""

    pass


class GraphBuilder:
    """
    Build and manage knowledge graphs in Neo4j.

    This class provides comprehensive graph database operations including
    schema management, node/relationship CRUD, batch operations, and querying.

    Supports context manager protocol for automatic connection management.
    """

    def __init__(self, config: GraphBuilderConfig):
        """
        Initialize the graph builder with Neo4j connection.

        Args:
            config: Configuration for graph builder

        Raises:
            Neo4jConnectionError: If connection fails
        """
        self.config = config
        self.logger = logging.getLogger(__name__)

        try:
            self.driver = GraphDatabase.driver(
                config.neo4j_uri,
                auth=config.auth,
                max_connection_lifetime=config.max_connection_lifetime,
                max_connection_pool_size=config.max_connection_pool_size,
                connection_timeout=config.connection_timeout,
            )

            # Verify connectivity
            self.driver.verify_connectivity()
            self.logger.info(
                f"Connected to Neo4j at {config.neo4j_uri}, database: {config.database}"  # noqa: E501
            )

        except AuthError as e:
            error_msg = f"Authentication failed: {str(e)}"
            self.logger.error(error_msg)
            raise Neo4jConnectionError(error_msg) from e

        except ServiceUnavailable as e:
            error_msg = f"Neo4j service unavailable: {str(e)}"
            self.logger.error(error_msg)
            raise Neo4jConnectionError(error_msg) from e

        except Exception as e:
            error_msg = f"Failed to connect to Neo4j: {str(e)}"
            self.logger.error(error_msg)
            raise Neo4jConnectionError(error_msg) from e

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - close connection."""
        self.close()
        return False

    def close(self) -> None:
        """Close Neo4j driver connection."""
        if hasattr(self, "driver"):
            self.driver.close()
            self.logger.info("Closed Neo4j connection")

    @retry(
        retry=retry_if_exception_type(ServiceUnavailable),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    def create_schema(self, schema: GraphSchema) -> bool:
        """
        Create database schema including constraints and indexes.

        Args:
            schema: Schema definition

        Returns:
            True if successful

        Raises:
            GraphBuilderError: If schema creation fails
        """
        try:
            with self.driver.session(database=self.config.database) as session:
                # Create constraints
                if self.config.enable_constraints:
                    for constraint in schema.constraints:
                        try:
                            session.run(constraint)
                            self.logger.debug(f"Created constraint: {constraint}")
                        except Neo4jError as e:
                            if "already exists" in str(e).lower():
                                self.logger.debug(
                                    f"Constraint already exists: {constraint}"
                                )
                            else:
                                raise

                # Create indexes
                for index in schema.indexes:
                    try:
                        session.run(index)
                        self.logger.debug(f"Created index: {index}")
                    except Neo4jError as e:
                        if "already exists" in str(e).lower():
                            self.logger.debug(f"Index already exists: {index}")
                        else:
                            raise

                self.logger.info(
                    f"Schema created: {len(schema.constraints)} constraints, "
                    f"{len(schema.indexes)} indexes"
                )
                return True

        except Exception as e:
            self.logger.error(f"Schema creation failed: {str(e)}")
            raise GraphBuilderError(f"Failed to create schema: {str(e)}") from e

    @retry(
        retry=retry_if_exception_type(ServiceUnavailable),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    def create_nodes(self, nodes: List[GraphNode]) -> int:
        """
        Create multiple nodes in batch.

        Args:
            nodes: List of nodes to create

        Returns:
            Number of nodes created

        Raises:
            GraphBuilderError: If node creation fails
        """
        if not nodes:
            return 0

        try:
            total_created = 0
            batches = [
                nodes[i : i + self.config.batch_size]
                for i in range(0, len(nodes), self.config.batch_size)
            ]

            with self.driver.session(database=self.config.database) as session:
                for batch_idx, batch in enumerate(batches):
                    # Prepare batch data
                    batch_data = [
                        {
                            "id": node.id,
                            "labels": node.labels,
                            "properties": {
                                **node.properties,
                                "created_at": datetime.utcnow().isoformat(),
                                "updated_at": datetime.utcnow().isoformat(),
                            },
                        }
                        for node in batch
                    ]

                    # Use UNWIND for efficient batch creation
                    query = """
                    UNWIND $batch AS node
                    CALL apoc.create.node(node.labels,
                        apoc.map.merge(node.properties, {id: node.id}))
                    YIELD node AS n
                    RETURN count(n) AS created
                    """

                    # Fallback query without APOC
                    fallback_query = """
                    UNWIND $batch AS node
                    CREATE (n)
                    SET n = node.properties
                    SET n.id = node.id
                    WITH n, node.labels AS labels
                    CALL apoc.create.addLabels(n, labels) YIELD node AS labeled
                    RETURN count(labeled) AS created
                    """

                    # Simple fallback for single label
                    simple_query = """
                    UNWIND $batch AS node
                    CREATE (n)
                    SET n = node.properties
                    SET n.id = node.id
                    RETURN count(n) AS created
                    """

                    try:
                        result = session.run(query, batch=batch_data)
                        count = result.single()["created"]
                    except Neo4jError:
                        # Try fallback without APOC
                        try:
                            result = session.run(fallback_query, batch=batch_data)
                            count = result.single()["created"]
                        except Neo4jError:
                            # Use simple query and set labels manually
                            count = 0
                            for node_data in batch_data:
                                labels_str = ":".join(node_data["labels"])
                                single_query = f"""
                                CREATE (n:{labels_str})
                                SET n = $properties
                                SET n.id = $id
                                RETURN n
                                """
                                session.run(
                                    single_query,
                                    properties=node_data["properties"],
                                    id=node_data["id"],
                                )
                                count += 1

                    total_created += count
                    self.logger.debug(
                        f"Created batch {batch_idx + 1}/{len(batches)}: "
                        f"{count} nodes"
                    )

            self.logger.info(f"Created {total_created} nodes in total")
            return total_created

        except Exception as e:
            self.logger.error(f"Node creation failed: {str(e)}")
            raise GraphBuilderError(f"Failed to create nodes: {str(e)}") from e

    @retry(
        retry=retry_if_exception_type(ServiceUnavailable),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    def create_relationships(self, rels: List[GraphRelationship]) -> int:
        """
        Create multiple relationships in batch.

        Args:
            rels: List of relationships to create

        Returns:
            Number of relationships created

        Raises:
            GraphBuilderError: If relationship creation fails
        """
        if not rels:
            return 0

        try:
            total_created = 0
            batches = [
                rels[i : i + self.config.batch_size]
                for i in range(0, len(rels), self.config.batch_size)
            ]

            with self.driver.session(database=self.config.database) as session:
                for batch_idx, batch in enumerate(batches):
                    # Prepare batch data
                    batch_data = [
                        {
                            "source_id": rel.source_id,
                            "target_id": rel.target_id,
                            "rel_type": rel.rel_type,
                            "properties": {
                                **rel.properties,
                                "created_at": datetime.utcnow().isoformat(),
                            },
                        }
                        for rel in batch
                    ]

                    # Use UNWIND for efficient batch creation
                    query = """
                    UNWIND $batch AS rel
                    MATCH (source {id: rel.source_id})
                    MATCH (target {id: rel.target_id})
                    CALL apoc.create.relationship(
                        source, rel.rel_type, rel.properties, target
                    ) YIELD rel AS r
                    RETURN count(r) AS created
                    """

                    # Fallback without APOC using dynamic query
                    try:
                        result = session.run(query, batch=batch_data)
                        count = result.single()["created"]
                    except Neo4jError:
                        # Create relationships individually
                        count = 0
                        for rel_data in batch_data:
                            single_query = f"""
                            MATCH (source {{id: $source_id}})
                            MATCH (target {{id: $target_id}})
                            CREATE (source)-[r:{rel_data['rel_type']}]->(target)
                            SET r = $properties
                            RETURN r
                            """
                            result = session.run(
                                single_query,
                                source_id=rel_data["source_id"],
                                target_id=rel_data["target_id"],
                                properties=rel_data["properties"],
                            )
                            if result.single():
                                count += 1

                    total_created += count
                    self.logger.debug(
                        f"Created batch {batch_idx + 1}/{len(batches)}: "
                        f"{count} relationships"
                    )

            self.logger.info(f"Created {total_created} relationships in total")
            return total_created

        except Exception as e:
            self.logger.error(f"Relationship creation failed: {str(e)}")
            raise GraphBuilderError(f"Failed to create relationships: {str(e)}") from e

    @retry(
        retry=retry_if_exception_type(ServiceUnavailable),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    def create_node(self, node: GraphNode) -> str:
        """
        Create a single node.

        Args:
            node: Node to create

        Returns:
            Node ID

        Raises:
            GraphBuilderError: If node creation fails
        """
        try:
            with self.driver.session(database=self.config.database) as session:
                labels_str = ":".join(node.labels)
                properties = {
                    **node.properties,
                    "id": node.id,
                    "created_at": datetime.utcnow().isoformat(),
                    "updated_at": datetime.utcnow().isoformat(),
                }

                query = f"""
                CREATE (n:{labels_str})
                SET n = $properties
                RETURN n.id AS id
                """

                result = session.run(query, properties=properties)
                node_id = result.single()["id"]

                self.logger.debug(f"Created node: {node_id}")
                return node_id

        except Exception as e:
            self.logger.error(f"Node creation failed: {str(e)}")
            raise GraphBuilderError(f"Failed to create node: {str(e)}") from e

    @retry(
        retry=retry_if_exception_type(ServiceUnavailable),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    def create_relationship(self, rel: GraphRelationship) -> bool:
        """
        Create a single relationship.

        Args:
            rel: Relationship to create

        Returns:
            True if successful

        Raises:
            GraphBuilderError: If relationship creation fails
        """
        try:
            with self.driver.session(database=self.config.database) as session:
                properties = {
                    **rel.properties,
                    "created_at": datetime.utcnow().isoformat(),
                }

                query = f"""
                MATCH (source {{id: $source_id}})
                MATCH (target {{id: $target_id}})
                CREATE (source)-[r:{rel.rel_type}]->(target)
                SET r = $properties
                RETURN r
                """

                result = session.run(
                    query,
                    source_id=rel.source_id,
                    target_id=rel.target_id,
                    properties=properties,
                )

                if result.single():
                    self.logger.debug(
                        f"Created relationship: {rel.source_id} "
                        f"-[{rel.rel_type}]-> {rel.target_id}"
                    )
                    return True
                return False

        except Exception as e:
            self.logger.error(f"Relationship creation failed: {str(e)}")
            raise GraphBuilderError(f"Failed to create relationship: {str(e)}") from e

    @retry(
        retry=retry_if_exception_type(ServiceUnavailable),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    def merge_duplicate_entities(
        self, entity_type: str, property_key: str = "name"
    ) -> int:
        """
        Merge duplicate nodes with the same property value.

        Args:
            entity_type: Node label to process
            property_key: Property to check for duplicates

        Returns:
            Number of nodes merged

        Raises:
            GraphBuilderError: If merge operation fails
        """
        try:
            with self.driver.session(database=self.config.database) as session:
                # Find duplicates
                find_query = f"""
                MATCH (n:{entity_type})
                WHERE n.{property_key} IS NOT NULL
                WITH n.{property_key} AS value, collect(n) AS nodes
                WHERE size(nodes) > 1
                RETURN value, nodes
                """

                result = session.run(find_query)
                duplicates = list(result)

                if not duplicates:
                    self.logger.info(
                        f"No duplicates found for {entity_type}.{property_key}"
                    )
                    return 0

                merged_count = 0
                for record in duplicates:
                    nodes = record["nodes"]
                    # Keep first node, merge others into it
                    primary = nodes[0]
                    duplicates_to_merge = nodes[1:]

                    for dup in duplicates_to_merge:
                        merge_query = """
                        MATCH (primary)
                        WHERE id(primary) = $primary_id
                        MATCH (dup)
                        WHERE id(dup) = $dup_id
                        OPTIONAL MATCH (dup)-[r]-()
                        WITH primary, dup, collect(r) AS rels
                        FOREACH (rel IN rels |
                            CREATE (primary)-[r2:MERGED_FROM]->(endNode(rel))
                            SET r2 = properties(rel)
                        )
                        DETACH DELETE dup
                        RETURN primary
                        """

                        session.run(
                            merge_query,
                            primary_id=primary.id,
                            dup_id=dup.id,
                        )
                        merged_count += 1

                self.logger.info(f"Merged {merged_count} duplicate {entity_type} nodes")
                return merged_count

        except Exception as e:
            self.logger.error(f"Merge operation failed: {str(e)}")
            raise GraphBuilderError(f"Failed to merge duplicates: {str(e)}") from e

    @retry(
        retry=retry_if_exception_type(ServiceUnavailable),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    def enrich_node_properties(self, node_id: str, properties: Dict[str, Any]) -> bool:
        """
        Add or update properties on an existing node.

        Args:
            node_id: Node identifier
            properties: Properties to add/update

        Returns:
            True if successful

        Raises:
            GraphBuilderError: If enrichment fails
        """
        try:
            with self.driver.session(database=self.config.database) as session:
                # Add updated_at timestamp
                enriched_props = {
                    **properties,
                    "updated_at": datetime.utcnow().isoformat(),
                }

                query = """
                MATCH (n {id: $node_id})
                SET n += $properties
                RETURN n
                """

                result = session.run(query, node_id=node_id, properties=enriched_props)

                if result.single():
                    self.logger.debug(
                        f"Enriched node {node_id} with {len(properties)} properties"
                    )
                    return True

                self.logger.warning(f"Node not found: {node_id}")
                return False

        except Exception as e:
            self.logger.error(f"Node enrichment failed: {str(e)}")
            raise GraphBuilderError(
                f"Failed to enrich node properties: {str(e)}"
            ) from e

    @retry(
        retry=retry_if_exception_type(ServiceUnavailable),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    def execute_cypher(
        self, query: str, parameters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Execute raw Cypher query.

        Args:
            query: Cypher query string
            parameters: Query parameters

        Returns:
            List of result records as dictionaries

        Raises:
            GraphBuilderError: If query execution fails
        """
        try:
            with self.driver.session(database=self.config.database) as session:
                result = session.run(query, parameters or {})
                records = [dict(record) for record in result]

                self.logger.debug(f"Executed query, returned {len(records)} records")
                return records

        except CypherSyntaxError as e:
            self.logger.error(f"Cypher syntax error: {str(e)}")
            raise GraphBuilderError(f"Invalid Cypher query: {str(e)}") from e

        except Exception as e:
            self.logger.error(f"Query execution failed: {str(e)}")
            raise GraphBuilderError(f"Failed to execute query: {str(e)}") from e

    @retry(
        retry=retry_if_exception_type(ServiceUnavailable),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    def get_node_by_id(self, node_id: str) -> Optional[GraphNode]:
        """
        Retrieve a node by its ID.

        Args:
            node_id: Node identifier

        Returns:
            GraphNode if found, None otherwise

        Raises:
            GraphBuilderError: If retrieval fails
        """
        try:
            with self.driver.session(database=self.config.database) as session:
                query = """
                MATCH (n {id: $node_id})
                RETURN n, labels(n) AS labels
                """

                result = session.run(query, node_id=node_id)
                record = result.single()

                if not record:
                    return None

                node_data = dict(record["n"])
                labels = record["labels"]

                # Extract ID and remove from properties
                node_id_value = node_data.pop("id", node_id)

                return GraphNode(
                    id=node_id_value,
                    labels=labels,
                    properties=node_data,
                )

        except Exception as e:
            self.logger.error(f"Node retrieval failed: {str(e)}")
            raise GraphBuilderError(f"Failed to retrieve node: {str(e)}") from e

    @retry(
        retry=retry_if_exception_type(ServiceUnavailable),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    def delete_node(self, node_id: str) -> bool:
        """
        Delete a node and all its relationships.

        Args:
            node_id: Node identifier

        Returns:
            True if deleted, False if not found

        Raises:
            GraphBuilderError: If deletion fails
        """
        try:
            with self.driver.session(database=self.config.database) as session:
                query = """
                MATCH (n {id: $node_id})
                DETACH DELETE n
                RETURN count(n) AS deleted
                """

                result = session.run(query, node_id=node_id)
                deleted = result.single()["deleted"]

                if deleted > 0:
                    self.logger.info(f"Deleted node: {node_id}")
                    return True

                self.logger.warning(f"Node not found for deletion: {node_id}")
                return False

        except Exception as e:
            self.logger.error(f"Node deletion failed: {str(e)}")
            raise GraphBuilderError(f"Failed to delete node: {str(e)}") from e

    @retry(
        retry=retry_if_exception_type(ServiceUnavailable),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    def get_graph_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about the graph database.

        Returns:
            Dictionary containing graph statistics

        Raises:
            GraphBuilderError: If statistics retrieval fails
        """
        try:
            with self.driver.session(database=self.config.database) as session:
                # Count nodes
                node_count_query = "MATCH (n) RETURN count(n) AS count"
                node_count = session.run(node_count_query).single()["count"]

                # Count relationships
                rel_count_query = "MATCH ()-[r]->() RETURN count(r) AS count"
                rel_count = session.run(rel_count_query).single()["count"]

                # Count by node type
                node_types_query = """
                MATCH (n)
                UNWIND labels(n) AS label
                RETURN label, count(*) AS count
                ORDER BY count DESC
                """
                node_types = {
                    record["label"]: record["count"]
                    for record in session.run(node_types_query)
                }

                # Count by relationship type
                rel_types_query = """
                MATCH ()-[r]->()
                RETURN type(r) AS type, count(*) AS count
                ORDER BY count DESC
                """
                rel_types = {
                    record["type"]: record["count"]
                    for record in session.run(rel_types_query)
                }

                # Database info
                db_info_query = "CALL dbms.components() YIELD versions"
                try:
                    db_info = session.run(db_info_query).single()
                    version = db_info["versions"][0] if db_info else "unknown"
                except Exception:
                    version = "unknown"

                statistics = {
                    "total_nodes": node_count,
                    "total_relationships": rel_count,
                    "node_types": node_types,
                    "relationship_types": rel_types,
                    "database": self.config.database,
                    "neo4j_version": version,
                    "timestamp": datetime.utcnow().isoformat(),
                }

                self.logger.info(
                    f"Graph statistics: {node_count} nodes, {rel_count} relationships"
                )
                return statistics

        except Exception as e:
            self.logger.error(f"Statistics retrieval failed: {str(e)}")
            raise GraphBuilderError(f"Failed to retrieve statistics: {str(e)}") from e

    @retry(
        retry=retry_if_exception_type(ServiceUnavailable),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    def export_subgraph(self, entity_id: str, depth: int = 2) -> Dict[str, Any]:
        """
        Export a subgraph centered on an entity up to specified depth.

        Args:
            entity_id: Central entity ID
            depth: Maximum traversal depth (default: 2)

        Returns:
            Dictionary containing nodes and relationships

        Raises:
            GraphBuilderError: If export fails
        """
        try:
            with self.driver.session(database=self.config.database) as session:
                query = (
                    """
                MATCH path = (center {id: $entity_id})-[*0..%d]-(connected)
                WITH collect(DISTINCT center) + collect(DISTINCT connected) AS nodes,
                     [r IN relationships(path) | r] AS rels
                UNWIND nodes AS node
                WITH collect(DISTINCT node) AS unique_nodes, rels
                UNWIND rels AS rel
                WITH unique_nodes, collect(DISTINCT rel) AS unique_rels
                RETURN unique_nodes AS nodes, unique_rels AS relationships
                """
                    % depth
                )

                result = session.run(query, entity_id=entity_id)
                record = result.single()

                if not record:
                    return {"nodes": [], "relationships": [], "center": entity_id}

                # Process nodes
                nodes = []
                for node in record["nodes"]:
                    node_dict = dict(node)
                    nodes.append(
                        {
                            "id": node_dict.get("id", "unknown"),
                            "labels": list(node.labels),
                            "properties": node_dict,
                        }
                    )

                # Process relationships
                relationships = []
                for rel in record["relationships"]:
                    rel_dict = dict(rel)
                    relationships.append(
                        {
                            "source_id": rel.start_node.get("id", "unknown"),
                            "target_id": rel.end_node.get("id", "unknown"),
                            "type": rel.type,
                            "properties": rel_dict,
                        }
                    )

                subgraph = {
                    "center": entity_id,
                    "depth": depth,
                    "nodes": nodes,
                    "relationships": relationships,
                    "node_count": len(nodes),
                    "relationship_count": len(relationships),
                    "exported_at": datetime.utcnow().isoformat(),
                }

                self.logger.info(
                    f"Exported subgraph: {len(nodes)} nodes, "
                    f"{len(relationships)} relationships"
                )
                return subgraph

        except Exception as e:
            self.logger.error(f"Subgraph export failed: {str(e)}")
            raise GraphBuilderError(f"Failed to export subgraph: {str(e)}") from e

    def create_full_text_index(
        self, index_name: str, node_label: str, properties: List[str]
    ) -> bool:
        """
        Create full-text search index.

        Args:
            index_name: Name for the index
            node_label: Node label to index
            properties: List of properties to include

        Returns:
            True if successful

        Raises:
            GraphBuilderError: If index creation fails
        """
        try:
            with self.driver.session(database=self.config.database) as session:
                props_str = ", ".join([f"n.{prop}" for prop in properties])
                query = f"""
                CREATE FULLTEXT INDEX {index_name} IF NOT EXISTS
                FOR (n:{node_label})
                ON EACH [{props_str}]
                """

                session.run(query)
                self.logger.info(
                    f"Created full-text index: {index_name} on {node_label}"
                )
                return True

        except Exception as e:
            self.logger.error(f"Full-text index creation failed: {str(e)}")
            raise GraphBuilderError(
                f"Failed to create full-text index: {str(e)}"
            ) from e

    def search_nodes(
        self, index_name: str, search_term: str, limit: int = 10
    ) -> List[GraphNode]:
        """
        Search nodes using full-text index.

        Args:
            index_name: Name of full-text index
            search_term: Search query
            limit: Maximum results to return

        Returns:
            List of matching nodes

        Raises:
            GraphBuilderError: If search fails
        """
        try:
            with self.driver.session(database=self.config.database) as session:
                query = """
                CALL db.index.fulltext.queryNodes($index_name, $search_term)
                YIELD node, score
                RETURN node, labels(node) AS labels, score
                ORDER BY score DESC
                LIMIT $limit
                """

                result = session.run(
                    query,
                    index_name=index_name,
                    search_term=search_term,
                    limit=limit,
                )

                nodes = []
                for record in result:
                    node_data = dict(record["node"])
                    node_id = node_data.pop("id", "unknown")
                    labels = record["labels"]

                    nodes.append(
                        GraphNode(
                            id=node_id,
                            labels=labels,
                            properties={**node_data, "score": record["score"]},
                        )
                    )

                self.logger.info(
                    f"Search returned {len(nodes)} results for '{search_term}'"
                )
                return nodes

        except Exception as e:
            self.logger.error(f"Node search failed: {str(e)}")
            raise GraphBuilderError(f"Failed to search nodes: {str(e)}") from e


def main():
    """Example usage of GraphBuilder."""
    # Configure builder
    config = GraphBuilderConfig(
        neo4j_uri="bolt://localhost:7687",
        auth=("neo4j", "password"),
        database="neo4j",
        batch_size=100,
    )

    try:
        # Initialize builder with context manager
        with GraphBuilder(config) as builder:
            # Create schema
            schema = GraphSchema(
                node_types=["Person", "Organization", "Technology"],
                relationship_types=["WORKS_AT", "USES"],
                constraints=[
                    "CREATE CONSTRAINT person_id IF NOT EXISTS "
                    "FOR (p:Person) REQUIRE p.id IS UNIQUE",
                    "CREATE CONSTRAINT org_id IF NOT EXISTS "
                    "FOR (o:Organization) REQUIRE o.id IS UNIQUE",
                ],
                indexes=[
                    "CREATE INDEX person_name IF NOT EXISTS "
                    "FOR (p:Person) ON (p.name)",
                    "CREATE INDEX org_name IF NOT EXISTS "
                    "FOR (o:Organization) ON (o.name)",
                ],
            )

            builder.create_schema(schema)

            # Create sample nodes
            nodes = [
                GraphNode(
                    id="person_1",
                    labels=["Person"],
                    properties={"name": "John Smith", "role": "Engineer"},
                ),
                GraphNode(
                    id="org_1",
                    labels=["Organization"],
                    properties={"name": "Google", "industry": "Technology"},
                ),
                GraphNode(
                    id="tech_1",
                    labels=["Technology"],
                    properties={"name": "Python", "type": "Language"},
                ),
            ]

            created_nodes = builder.create_nodes(nodes)
            logger.info(f"Created {created_nodes} nodes")

            # Create relationships
            relationships = [
                GraphRelationship(
                    source_id="person_1",
                    target_id="org_1",
                    rel_type="WORKS_AT",
                    properties={"since": "2020"},
                ),
                GraphRelationship(
                    source_id="person_1",
                    target_id="tech_1",
                    rel_type="USES",
                    properties={"proficiency": "expert"},
                ),
            ]

            created_rels = builder.create_relationships(relationships)
            logger.info(f"Created {created_rels} relationships")

            # Get statistics
            stats = builder.get_graph_statistics()
            logger.info(f"Graph statistics:\n{json.dumps(stats, indent=2)}")

            # Export subgraph
            subgraph = builder.export_subgraph("person_1", depth=2)
            logger.info(
                f"Exported subgraph: {subgraph['node_count']} nodes, "
                f"{subgraph['relationship_count']} relationships"
            )

    except Neo4jConnectionError as e:
        logger.error(f"Connection error: {str(e)}")
    except GraphBuilderError as e:
        logger.error(f"Graph operation error: {str(e)}")


if __name__ == "__main__":
    main()
