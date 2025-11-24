"""
Graph Query Engine for Knowledge Graph Management Platform.

This module provides natural language to Cypher translation and advanced
graph querying capabilities for the devCrew_s1 Knowledge Graph platform.

Features:
- Natural language query translation to Cypher using LLMs
- Direct Cypher query execution
- Graph traversal and path finding
- Subgraph extraction
- Schema introspection

Author: devCrew_s1
License: MIT
"""

import logging
import time
from typing import Any, Dict, List, Optional, Tuple

import openai
from neo4j import GraphDatabase
from neo4j import exceptions as neo4j_exceptions
from pydantic import BaseModel, Field, validator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class QueryError(Exception):
    """Base exception for query-related errors."""

    pass


class TranslationError(QueryError):
    """Exception raised when NL to Cypher translation fails."""

    pass


class Neo4jError(QueryError):
    """Exception raised when Neo4j operations fail."""

    pass


class QueryConfig(BaseModel):
    """Configuration for GraphQueryEngine.

    Attributes:
        neo4j_uri: Neo4j database URI (e.g., bolt://localhost:7687)
        auth: Tuple of (username, password) for authentication
        enable_nl_translation: Enable natural language to Cypher translation
        llm_model: LLM model to use for translation (default: gpt-4)
        llm_api_key: OpenAI API key for LLM access
        max_retries: Maximum number of retry attempts for queries
    """

    neo4j_uri: str = Field(..., description="Neo4j database URI")
    auth: Tuple[str, str] = Field(..., description="Neo4j authentication credentials")
    enable_nl_translation: bool = Field(
        True, description="Enable NL to Cypher translation"
    )
    llm_model: str = Field("gpt-4", description="LLM model for translation")
    llm_api_key: Optional[str] = Field(None, description="OpenAI API key")
    max_retries: int = Field(3, description="Maximum retry attempts")

    class Config:
        """Pydantic config."""

        arbitrary_types_allowed = True

    @validator("neo4j_uri")
    def validate_uri(cls, v: str) -> str:
        """Validate Neo4j URI format."""
        if not v.startswith(("bolt://", "neo4j://", "bolt+s://", "neo4j+s://")):
            raise ValueError(
                "URI must start with bolt://, neo4j://, bolt+s://, or neo4j+s://"
            )
        return v


class CypherQuery(BaseModel):
    """Cypher query specification.

    Attributes:
        query: Cypher query string
        parameters: Query parameters for parameterized queries
        timeout: Query timeout in seconds
    """

    query: str = Field(..., description="Cypher query string")
    parameters: Dict[str, Any] = Field(
        default_factory=dict, description="Query parameters"
    )
    timeout: float = Field(30.0, description="Query timeout in seconds")

    @validator("query")
    def validate_query(cls, v: str) -> str:
        """Validate query is not empty."""
        if not v.strip():
            raise ValueError("Query cannot be empty")
        return v.strip()


class QueryResult(BaseModel):
    """Result of a query execution.

    Attributes:
        records: List of result records as dictionaries
        summary: Query execution summary
        execution_time: Time taken to execute query in seconds
        query: Original query that was executed
        node_count: Number of nodes returned
        relationship_count: Number of relationships returned
    """

    records: List[Dict[str, Any]] = Field(..., description="Result records")
    summary: str = Field(..., description="Execution summary")
    execution_time: float = Field(..., description="Execution time in seconds")
    query: str = Field(..., description="Original query")
    node_count: int = Field(0, description="Number of nodes returned")
    relationship_count: int = Field(0, description="Number of relationships returned")

    class Config:
        """Pydantic config."""

        arbitrary_types_allowed = True


class NLToCypherTranslator:
    """Translates natural language queries to Cypher using LLMs.

    This class leverages large language models to convert natural language
    questions into Cypher queries for Neo4j graph databases.
    """

    def __init__(self, llm_model: str = "gpt-4", api_key: Optional[str] = None):
        """Initialize the translator.

        Args:
            llm_model: OpenAI model to use (default: gpt-4)
            api_key: OpenAI API key
        """
        self.llm_model = llm_model
        if api_key:
            openai.api_key = api_key
        logger.info(f"Initialized NLToCypherTranslator with model {llm_model}")

    def translate(
        self, natural_language_query: str, schema_info: Optional[Dict[str, Any]] = None
    ) -> str:
        """Convert natural language query to Cypher.

        Args:
            natural_language_query: User's natural language question
            schema_info: Graph schema information to help with translation

        Returns:
            Cypher query string

        Raises:
            TranslationError: If translation fails
        """
        try:
            # Build system prompt with schema information
            system_prompt = self._build_system_prompt(schema_info)

            # Call OpenAI API
            response = openai.ChatCompletion.create(
                model=self.llm_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": natural_language_query},
                ],
                temperature=0.1,
                max_tokens=500,
            )

            cypher_query = response.choices[0].message.content.strip()

            # Extract Cypher from markdown code blocks if present
            cypher_query = self._extract_cypher_from_markdown(cypher_query)

            # Validate the generated Cypher
            if not self.validate_cypher(cypher_query):
                raise TranslationError(f"Generated invalid Cypher: {cypher_query}")

            logger.info(f"Translated NL query to Cypher: {cypher_query}")
            return cypher_query

        except openai.error.OpenAIError as e:
            logger.error(f"OpenAI API error during translation: {e}")
            raise TranslationError(f"LLM translation failed: {e}")
        except Exception as e:
            logger.error(f"Unexpected error during translation: {e}")
            raise TranslationError(f"Translation failed: {e}")

    def _build_system_prompt(self, schema_info: Optional[Dict[str, Any]]) -> str:
        """Build system prompt for LLM with schema context.

        Args:
            schema_info: Graph schema information

        Returns:
            System prompt string
        """
        base_prompt = """You are an expert in converting natural language questions
into Cypher queries for Neo4j graph databases.

Your task is to generate a valid, efficient Cypher query based on the user's question.

Rules:
1. Return ONLY the Cypher query, no explanations
2. Use MATCH clauses for pattern matching
3. Use WHERE clauses for filtering
4. Use RETURN to specify what data to retrieve
5. Use relationship patterns like -[:RELATIONSHIP_TYPE]->
6. Always use parameter syntax $param for values
7. Include LIMIT clauses to prevent excessive results
8. Use appropriate aggregation functions when needed

Common patterns:
- Find nodes: MATCH (n:Label {property: $value}) RETURN n
- Find relationships: MATCH (a)-[r:REL_TYPE]->(b) RETURN a, r, b
- Path queries: MATCH path = (a)-[*1..3]->(b) RETURN path
- Aggregation: MATCH (n) RETURN count(n), collect(n.name)
"""

        if schema_info:
            schema_text = "\n\nGraph Schema:\n"
            if "node_labels" in schema_info:
                schema_text += f"Node Labels: {', '.join(schema_info['node_labels'])}\n"
            if "relationship_types" in schema_info:
                rel_types = ', '.join(schema_info['relationship_types'])
                schema_text += f"Relationship Types: {rel_types}\n"
            if "node_properties" in schema_info:
                schema_text += f"Node Properties: {schema_info['node_properties']}\n"
            base_prompt += schema_text

        return base_prompt

    def _extract_cypher_from_markdown(self, text: str) -> str:
        """Extract Cypher query from markdown code blocks.

        Args:
            text: Text potentially containing markdown

        Returns:
            Extracted Cypher query
        """
        # Check for code block markers
        if "```" in text:
            lines = text.split("\n")
            in_code_block = False
            cypher_lines = []

            for line in lines:
                if line.strip().startswith("```"):
                    in_code_block = not in_code_block
                    continue
                if in_code_block:
                    cypher_lines.append(line)

            if cypher_lines:
                return "\n".join(cypher_lines).strip()

        return text

    def validate_cypher(self, cypher: str) -> bool:
        """Perform basic Cypher syntax validation.

        Args:
            cypher: Cypher query to validate

        Returns:
            True if query appears valid, False otherwise
        """
        if not cypher or not cypher.strip():
            return False

        cypher_upper = cypher.upper()

        # Check for basic Cypher keywords
        has_match = "MATCH" in cypher_upper
        has_return = "RETURN" in cypher_upper
        has_create = "CREATE" in cypher_upper
        has_merge = "MERGE" in cypher_upper

        # Must have at least one main clause
        if not (has_match or has_create or has_merge):
            return False

        # Read queries must have RETURN
        if has_match and not (has_return or has_create or has_merge):
            return False

        # Check for balanced parentheses
        if cypher.count("(") != cypher.count(")"):
            return False

        # Check for balanced brackets
        if cypher.count("[") != cypher.count("]"):
            return False

        return True


class GraphQueryEngine:
    """Advanced graph query engine with NL translation support.

    This class provides comprehensive graph querying capabilities including
    direct Cypher execution, natural language translation, graph traversal,
    path finding, and subgraph extraction.
    """

    def __init__(self, config: QueryConfig):
        """Initialize the query engine.

        Args:
            config: Query engine configuration

        Raises:
            Neo4jError: If connection to Neo4j fails
        """
        self.config = config
        self.driver = None
        self.translator = None

        try:
            # Initialize Neo4j driver
            self.driver = GraphDatabase.driver(
                config.neo4j_uri, auth=config.auth, max_connection_lifetime=3600
            )

            # Test connection
            with self.driver.session() as session:
                session.run("RETURN 1")

            logger.info(f"Connected to Neo4j at {config.neo4j_uri}")

            # Initialize NL translator if enabled
            if config.enable_nl_translation:
                self.translator = NLToCypherTranslator(
                    config.llm_model, config.llm_api_key
                )

        except neo4j_exceptions.ServiceUnavailable as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            raise Neo4jError(f"Neo4j connection failed: {e}")
        except Exception as e:
            logger.error(f"Unexpected error during initialization: {e}")
            raise Neo4jError(f"Initialization failed: {e}")

    def execute_cypher(self, query: CypherQuery) -> QueryResult:
        """Execute a Cypher query against the graph database.

        Args:
            query: Cypher query specification

        Returns:
            Query result with records and metadata

        Raises:
            QueryError: If query execution fails
        """
        start_time = time.time()

        try:
            with self.driver.session() as session:
                result = session.run(
                    query.query, query.parameters, timeout=query.timeout
                )

                # Convert records to dictionaries
                records = [dict(record) for record in result]

                # Get summary information
                summary = result.consume()
                execution_time = time.time() - start_time

                # Count nodes and relationships
                node_count = 0
                relationship_count = 0
                for record in records:
                    for value in record.values():
                        if hasattr(value, "labels"):  # Node
                            node_count += 1
                        elif hasattr(value, "type"):  # Relationship
                            relationship_count += 1

                summary_text = (
                    f"Query returned {len(records)} records "
                    f"({node_count} nodes, {relationship_count} relationships)"
                )

                logger.info(f"Executed query in {execution_time:.3f}s: {summary_text}")

                return QueryResult(
                    records=records,
                    summary=summary_text,
                    execution_time=execution_time,
                    query=query.query,
                    node_count=node_count,
                    relationship_count=relationship_count,
                )

        except neo4j_exceptions.CypherSyntaxError as e:
            logger.error(f"Cypher syntax error: {e}")
            raise QueryError(f"Invalid Cypher syntax: {e}")
        except neo4j_exceptions.Neo4jError as e:
            logger.error(f"Neo4j error during query execution: {e}")
            raise Neo4jError(f"Query execution failed: {e}")
        except Exception as e:
            logger.error(f"Unexpected error during query execution: {e}")
            raise QueryError(f"Query failed: {e}")

    def execute_natural_language(self, nl_query: str) -> QueryResult:
        """Execute a natural language query.

        Args:
            nl_query: Natural language query string

        Returns:
            Query result

        Raises:
            TranslationError: If NL translation is disabled or fails
            QueryError: If query execution fails
        """
        if not self.config.enable_nl_translation or not self.translator:
            raise TranslationError(
                "Natural language translation is not enabled. "
                "Set enable_nl_translation=True in config."
            )

        try:
            # Get schema information to help with translation
            schema = self.get_schema()

            # Translate NL to Cypher
            cypher_query = self.translator.translate(nl_query, schema)

            logger.info(f"Translated NL query: '{nl_query}' -> '{cypher_query}'")

            # Execute the generated Cypher
            query = CypherQuery(query=cypher_query)
            return self.execute_cypher(query)

        except TranslationError:
            raise
        except Exception as e:
            logger.error(f"Failed to execute NL query: {e}")
            raise QueryError(f"NL query execution failed: {e}")

    def traverse_from_entity(
        self, entity_id: str, depth: int = 2, direction: str = "both"
    ) -> Dict[str, Any]:
        """Traverse the graph from a starting entity.

        Args:
            entity_id: ID of the starting entity
            depth: Maximum depth to traverse (default: 2)
            direction: Traversal direction - 'outgoing', 'incoming', or 'both'

        Returns:
            Dictionary containing nodes and relationships

        Raises:
            QueryError: If traversal fails
        """
        if direction not in ["outgoing", "incoming", "both"]:
            raise ValueError("direction must be 'outgoing', 'incoming', or 'both'")

        # Build direction pattern
        if direction == "outgoing":
            rel_pattern = f"-[*1..{depth}]->"
        elif direction == "incoming":
            rel_pattern = f"<-[*1..{depth}]-"
        else:  # both
            rel_pattern = f"-[*1..{depth}]-"

        query = f"""
        MATCH path = (start {{id: $entity_id}}){rel_pattern}(end)
        WITH nodes(path) as nodes, relationships(path) as rels
        UNWIND nodes as node
        WITH collect(DISTINCT node) as all_nodes, rels
        UNWIND rels as rel_list
        UNWIND rel_list as rel
        WITH all_nodes, collect(DISTINCT rel) as all_rels
        RETURN all_nodes, all_rels
        """

        try:
            result = self.execute_cypher(
                CypherQuery(query=query, parameters={"entity_id": entity_id})
            )

            if not result.records:
                return {"nodes": [], "relationships": [], "entity_id": entity_id}

            record = result.records[0]
            nodes = [self._node_to_dict(node) for node in record.get("all_nodes", [])]
            relationships = [
                self._relationship_to_dict(rel) for rel in record.get("all_rels", [])
            ]

            return {
                "entity_id": entity_id,
                "depth": depth,
                "direction": direction,
                "nodes": nodes,
                "relationships": relationships,
                "node_count": len(nodes),
                "relationship_count": len(relationships),
            }

        except Exception as e:
            logger.error(f"Graph traversal failed: {e}")
            raise QueryError(f"Traversal failed: {e}")

    def find_shortest_path(
        self, source_id: str, target_id: str, max_hops: int = 5
    ) -> List[Dict[str, Any]]:
        """Find shortest path(s) between two entities.

        Args:
            source_id: Source entity ID
            target_id: Target entity ID
            max_hops: Maximum number of hops to consider

        Returns:
            List of path dictionaries

        Raises:
            QueryError: If path finding fails
        """
        query = f"""
        MATCH path = shortestPath(
            (source {{id: $source_id}})-[*1..{max_hops}]-(target {{id: $target_id}})
        )
        RETURN path,
               length(path) as path_length,
               nodes(path) as nodes,
               relationships(path) as relationships
        """

        try:
            result = self.execute_cypher(
                CypherQuery(
                    query=query,
                    parameters={"source_id": source_id, "target_id": target_id},
                )
            )

            if not result.records:
                logger.info(f"No path found between {source_id} and {target_id}")
                return []

            paths = []
            for record in result.records:
                nodes = [self._node_to_dict(n) for n in record["nodes"]]
                rels = [self._relationship_to_dict(r) for r in record["relationships"]]

                paths.append(
                    {
                        "source_id": source_id,
                        "target_id": target_id,
                        "length": record["path_length"],
                        "nodes": nodes,
                        "relationships": rels,
                    }
                )

            logger.info(f"Found {len(paths)} shortest path(s)")
            return paths

        except Exception as e:
            logger.error(f"Shortest path search failed: {e}")
            raise QueryError(f"Path finding failed: {e}")

    def extract_subgraph(self, entity_ids: List[str], depth: int = 1) -> Dict[str, Any]:
        """Extract a subgraph around specified entities.

        Args:
            entity_ids: List of entity IDs to include
            depth: Depth of neighborhood to include (default: 1)

        Returns:
            Dictionary containing subgraph nodes and relationships

        Raises:
            QueryError: If extraction fails
        """
        query = f"""
        MATCH (n)
        WHERE n.id IN $entity_ids
        OPTIONAL MATCH path = (n)-[*1..{depth}]-(connected)
        WITH collect(DISTINCT n) + collect(DISTINCT connected) as all_nodes
        UNWIND all_nodes as node
        WITH collect(DISTINCT node) as nodes
        MATCH (a)-[r]-(b)
        WHERE a IN nodes AND b IN nodes
        RETURN nodes, collect(DISTINCT r) as relationships
        """

        try:
            result = self.execute_cypher(
                CypherQuery(query=query, parameters={"entity_ids": entity_ids})
            )

            if not result.records:
                return {
                    "entity_ids": entity_ids,
                    "nodes": [],
                    "relationships": [],
                }

            record = result.records[0]
            nodes = [self._node_to_dict(node) for node in record["nodes"]]
            relationships = [
                self._relationship_to_dict(rel) for rel in record["relationships"]
            ]

            logger.info(
                f"Extracted subgraph: {len(nodes)} nodes, "
                f"{len(relationships)} relationships"
            )

            return {
                "entity_ids": entity_ids,
                "depth": depth,
                "nodes": nodes,
                "relationships": relationships,
                "node_count": len(nodes),
                "relationship_count": len(relationships),
            }

        except Exception as e:
            logger.error(f"Subgraph extraction failed: {e}")
            raise QueryError(f"Extraction failed: {e}")

    def get_schema(self) -> Dict[str, Any]:
        """Retrieve graph schema information.

        Returns:
            Dictionary containing schema information

        Raises:
            QueryError: If schema retrieval fails
        """
        try:
            # Get node labels
            labels_result = self.execute_cypher(
                CypherQuery(
                    query="CALL db.labels() YIELD label RETURN collect(label) as labels"
                )
            )
            node_labels = (
                labels_result.records[0]["labels"] if labels_result.records else []
            )

            # Get relationship types
            rels_result = self.execute_cypher(
                CypherQuery(
                    query="CALL db.relationshipTypes() YIELD relationshipType "
                    "RETURN collect(relationshipType) as types"
                )
            )
            rel_types = rels_result.records[0]["types"] if rels_result.records else []

            # Get property keys
            props_result = self.execute_cypher(
                CypherQuery(
                    query="CALL db.propertyKeys() YIELD propertyKey "
                    "RETURN collect(propertyKey) as keys"
                )
            )
            property_keys = (
                props_result.records[0]["keys"] if props_result.records else []
            )

            # Get sample node properties for each label
            node_properties = {}
            for label in node_labels[:10]:  # Limit to first 10 labels
                sample_query = f"""
                MATCH (n:{label})
                WITH n LIMIT 1
                RETURN keys(n) as properties
                """
                try:
                    sample_result = self.execute_cypher(CypherQuery(query=sample_query))
                    if sample_result.records:
                        node_properties[label] = sample_result.records[0]["properties"]
                except Exception:
                    continue

            schema = {
                "node_labels": node_labels,
                "relationship_types": rel_types,
                "property_keys": property_keys,
                "node_properties": node_properties,
                "node_label_count": len(node_labels),
                "relationship_type_count": len(rel_types),
            }

            logger.info(
                f"Retrieved schema: {len(node_labels)} labels, "
                f"{len(rel_types)} relationship types"
            )

            return schema

        except Exception as e:
            logger.error(f"Schema retrieval failed: {e}")
            raise QueryError(f"Failed to retrieve schema: {e}")

    def get_query_examples(self) -> List[Dict[str, str]]:
        """Return common Cypher query examples.

        Returns:
            List of query examples with descriptions
        """
        examples = [
            {
                "description": "Find all nodes with a specific label",
                "query": "MATCH (n:Person) RETURN n LIMIT 25",
            },
            {
                "description": "Find nodes by property value",
                "query": "MATCH (n:Person {name: 'John Doe'}) RETURN n",
            },
            {
                "description": "Find relationships between nodes",
                "query": (
                    "MATCH (a:Person)-[r:KNOWS]->(b:Person) "
                    "RETURN a, r, b LIMIT 25"
                ),
            },
            {
                "description": "Find paths of specific length",
                "query": (
                    "MATCH path = (a:Person)-[*2]-(b:Person) "
                    "RETURN path LIMIT 10"
                ),
            },
            {
                "description": "Count nodes by label",
                "query": "MATCH (n:Person) RETURN count(n) as total",
            },
            {
                "description": "Find nodes with multiple relationships",
                "query": """
                MATCH (n:Person)-[r]-()
                WITH n, count(r) as rel_count
                WHERE rel_count > 5
                RETURN n, rel_count
                ORDER BY rel_count DESC
                LIMIT 10
                """,
            },
            {
                "description": "Find common neighbors",
                "query": """
                MATCH (a:Person {id: $person1})-[:KNOWS]-(common)
                      -[:KNOWS]-(b:Person {id: $person2})
                RETURN common
                """,
            },
            {
                "description": "Aggregate properties",
                "query": """
                MATCH (n:Person)
                RETURN
                    count(n) as total_people,
                    avg(n.age) as average_age,
                    collect(DISTINCT n.department) as departments
                """,
            },
        ]

        return examples

    def _node_to_dict(self, node: Any) -> Dict[str, Any]:
        """Convert Neo4j node to dictionary.

        Args:
            node: Neo4j node object

        Returns:
            Dictionary representation
        """
        if node is None:
            return {}

        node_dict = dict(node)
        node_dict["_labels"] = list(node.labels) if hasattr(node, "labels") else []
        node_dict["_id"] = node.id if hasattr(node, "id") else None

        return node_dict

    def _relationship_to_dict(self, rel: Any) -> Dict[str, Any]:
        """Convert Neo4j relationship to dictionary.

        Args:
            rel: Neo4j relationship object

        Returns:
            Dictionary representation
        """
        if rel is None:
            return {}

        rel_dict = dict(rel)
        rel_dict["_type"] = rel.type if hasattr(rel, "type") else None
        rel_dict["_id"] = rel.id if hasattr(rel, "id") else None
        rel_dict["_start_node_id"] = (
            rel.start_node.id if hasattr(rel, "start_node") else None
        )
        rel_dict["_end_node_id"] = rel.end_node.id if hasattr(rel, "end_node") else None

        return rel_dict

    def close(self) -> None:
        """Close the Neo4j driver connection."""
        if self.driver:
            self.driver.close()
            logger.info("Closed Neo4j connection")


# Utility functions


def create_query_engine(
    uri: str,
    username: str,
    password: str,
    enable_nl: bool = True,
    llm_model: str = "gpt-4",
    api_key: Optional[str] = None,
) -> GraphQueryEngine:
    """Factory function to create a GraphQueryEngine.

    Args:
        uri: Neo4j URI
        username: Neo4j username
        password: Neo4j password
        enable_nl: Enable natural language translation
        llm_model: LLM model for translation
        api_key: OpenAI API key

    Returns:
        Configured GraphQueryEngine instance
    """
    config = QueryConfig(
        neo4j_uri=uri,
        auth=(username, password),
        enable_nl_translation=enable_nl,
        llm_model=llm_model,
        llm_api_key=api_key,
    )

    return GraphQueryEngine(config)
