"""
Graph Analyzer for Knowledge Graph Management Platform.

This module provides advanced graph analytics capabilities including centrality
measures, community detection, path analysis, and graph metrics for the
devCrew_s1 Knowledge Graph platform.

Features:
- Centrality analysis (PageRank, Betweenness, Closeness, Degree)
- Community detection (Louvain, Label Propagation)
- Graph metrics calculation
- Bridge node identification
- Entity clustering by similarity

Author: devCrew_s1
License: MIT
"""

import logging
from collections import defaultdict
from typing import Any, Dict, List, Optional, Tuple

import community as community_louvain  # python-louvain
import networkx as nx
from neo4j import GraphDatabase
from neo4j import exceptions as neo4j_exceptions
from pydantic import BaseModel, Field, validator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AnalyzerError(Exception):
    """Base exception for analyzer errors."""

    pass


class GraphLoadError(AnalyzerError):
    """Exception raised when graph loading fails."""

    pass


class AnalyzerConfig(BaseModel):
    """Configuration for GraphAnalyzer.

    Attributes:
        neo4j_uri: Neo4j database URI
        auth: Authentication credentials (username, password)
        cache_results: Whether to cache NetworkX graphs in memory
        max_cache_size: Maximum number of cached graphs
    """

    neo4j_uri: str = Field(..., description="Neo4j database URI")
    auth: Tuple[str, str] = Field(..., description="Authentication credentials")
    cache_results: bool = Field(True, description="Enable result caching")
    max_cache_size: int = Field(5, description="Maximum cached graphs")

    class Config:
        """Pydantic config."""

        arbitrary_types_allowed = True

    @validator("neo4j_uri")
    def validate_uri(cls, v: str) -> str:
        """Validate Neo4j URI format."""
        if not v.startswith(("bolt://", "neo4j://", "bolt+s://", "neo4j+s://")):
            raise ValueError("Invalid Neo4j URI format")
        return v


class GraphMetrics(BaseModel):
    """Graph-level metrics.

    Attributes:
        node_count: Total number of nodes
        edge_count: Total number of edges
        density: Graph density (0-1)
        avg_degree: Average node degree
        diameter: Graph diameter (longest shortest path)
        clustering_coefficient: Global clustering coefficient
        avg_clustering: Average clustering coefficient
        connected_components: Number of connected components
    """

    node_count: int = Field(..., description="Number of nodes")
    edge_count: int = Field(..., description="Number of edges")
    density: float = Field(..., description="Graph density")
    avg_degree: float = Field(..., description="Average node degree")
    diameter: Optional[int] = Field(None, description="Graph diameter")
    clustering_coefficient: float = Field(..., description="Clustering coefficient")
    avg_clustering: float = Field(..., description="Average clustering")
    connected_components: int = Field(..., description="Connected components")
    is_connected: bool = Field(..., description="Whether graph is connected")


class CommunityResult(BaseModel):
    """Result of community detection.

    Attributes:
        communities: Mapping of community ID to list of node IDs
        modularity: Modularity score of the partition
        num_communities: Number of detected communities
        algorithm: Algorithm used for detection
        community_sizes: Size of each community
    """

    communities: Dict[int, List[str]] = Field(..., description="Community assignments")
    modularity: float = Field(..., description="Modularity score")
    num_communities: int = Field(..., description="Number of communities")
    algorithm: str = Field(..., description="Detection algorithm")
    community_sizes: Dict[int, int] = Field(..., description="Community sizes")


class PathResult(BaseModel):
    """Result of path analysis.

    Attributes:
        path: List of node IDs forming the path
        length: Path length (number of edges)
        cost: Path cost if weighted
    """

    path: List[str] = Field(..., description="Node IDs in path")
    length: int = Field(..., description="Path length")
    cost: float = Field(0.0, description="Path cost")


class GraphAnalyzer:
    """Advanced graph analytics engine.

    This class provides comprehensive graph analysis capabilities by loading
    Neo4j graphs into NetworkX and applying various algorithms.
    """

    def __init__(self, config: AnalyzerConfig):
        """Initialize the analyzer.

        Args:
            config: Analyzer configuration

        Raises:
            GraphLoadError: If Neo4j connection fails
        """
        self.config = config
        self.driver = None
        self._graph_cache: Dict[str, nx.Graph] = {}

        try:
            # Initialize Neo4j driver
            self.driver = GraphDatabase.driver(
                config.neo4j_uri, auth=config.auth, max_connection_lifetime=3600
            )

            # Test connection
            with self.driver.session() as session:
                session.run("RETURN 1")

            logger.info(f"GraphAnalyzer connected to Neo4j at {config.neo4j_uri}")

        except neo4j_exceptions.ServiceUnavailable as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            raise GraphLoadError(f"Neo4j connection failed: {e}")

    def load_graph_to_networkx(
        self, node_type: Optional[str] = None, relationship_type: Optional[str] = None
    ) -> nx.Graph:
        """Load graph from Neo4j into NetworkX.

        Args:
            node_type: Optional node label filter
            relationship_type: Optional relationship type filter

        Returns:
            NetworkX graph

        Raises:
            GraphLoadError: If loading fails
        """
        cache_key = f"{node_type}_{relationship_type}"

        # Check cache
        if self.config.cache_results and cache_key in self._graph_cache:
            logger.info(f"Returning cached graph for key: {cache_key}")
            return self._graph_cache[cache_key]

        try:
            # Build query based on filters
            if node_type and relationship_type:
                query = f"""
                MATCH (a:{node_type})-[r:{relationship_type}]-(b:{node_type})
                RETURN a, r, b
                """
            elif node_type:
                query = f"""
                MATCH (a:{node_type})-[r]-(b:{node_type})
                RETURN a, r, b
                """
            else:
                query = """
                MATCH (a)-[r]-(b)
                RETURN a, r, b
                """

            with self.driver.session() as session:
                result = session.run(query)
                records = list(result)

            # Convert to NetworkX
            G = self._convert_neo4j_to_networkx(records)

            logger.info(
                f"Loaded graph: {G.number_of_nodes()} nodes, "
                f"{G.number_of_edges()} edges"
            )

            # Cache if enabled
            if self.config.cache_results:
                if len(self._graph_cache) >= self.config.max_cache_size:
                    # Remove oldest entry
                    self._graph_cache.pop(next(iter(self._graph_cache)))
                self._graph_cache[cache_key] = G

            return G

        except Exception as e:
            logger.error(f"Failed to load graph: {e}")
            raise GraphLoadError(f"Graph loading failed: {e}")

    def calculate_pagerank(
        self, top_k: int = 10, node_type: Optional[str] = None
    ) -> Dict[str, float]:
        """Calculate PageRank centrality scores.

        Args:
            top_k: Number of top nodes to return
            node_type: Optional node type filter

        Returns:
            Dictionary mapping node IDs to PageRank scores

        Raises:
            AnalyzerError: If calculation fails
        """
        try:
            G = self.load_graph_to_networkx(node_type=node_type)

            if G.number_of_nodes() == 0:
                logger.warning("Empty graph, returning empty PageRank results")
                return {}

            # Calculate PageRank
            pagerank_scores = nx.pagerank(G, alpha=0.85, max_iter=100)

            # Sort and return top k
            sorted_scores = sorted(
                pagerank_scores.items(), key=lambda x: x[1], reverse=True
            )

            top_nodes = dict(sorted_scores[:top_k])

            logger.info(f"Calculated PageRank for {len(pagerank_scores)} nodes")

            return top_nodes

        except Exception as e:
            logger.error(f"PageRank calculation failed: {e}")
            raise AnalyzerError(f"PageRank failed: {e}")

    def calculate_betweenness_centrality(
        self, top_k: int = 10, node_type: Optional[str] = None
    ) -> Dict[str, float]:
        """Calculate betweenness centrality scores.

        Args:
            top_k: Number of top nodes to return
            node_type: Optional node type filter

        Returns:
            Dictionary mapping node IDs to betweenness scores

        Raises:
            AnalyzerError: If calculation fails
        """
        try:
            G = self.load_graph_to_networkx(node_type=node_type)

            if G.number_of_nodes() == 0:
                logger.warning("Empty graph, returning empty betweenness results")
                return {}

            # Calculate betweenness centrality
            betweenness_scores = nx.betweenness_centrality(G, normalized=True)

            # Sort and return top k
            sorted_scores = sorted(
                betweenness_scores.items(), key=lambda x: x[1], reverse=True
            )

            top_nodes = dict(sorted_scores[:top_k])

            logger.info(
                f"Calculated betweenness centrality for {len(betweenness_scores)} nodes"
            )

            return top_nodes

        except Exception as e:
            logger.error(f"Betweenness centrality calculation failed: {e}")
            raise AnalyzerError(f"Betweenness centrality failed: {e}")

    def calculate_closeness_centrality(
        self, top_k: int = 10, node_type: Optional[str] = None
    ) -> Dict[str, float]:
        """Calculate closeness centrality scores.

        Args:
            top_k: Number of top nodes to return
            node_type: Optional node type filter

        Returns:
            Dictionary mapping node IDs to closeness scores

        Raises:
            AnalyzerError: If calculation fails
        """
        try:
            G = self.load_graph_to_networkx(node_type=node_type)

            if G.number_of_nodes() == 0:
                logger.warning("Empty graph, returning empty closeness results")
                return {}

            # Calculate closeness centrality
            closeness_scores = nx.closeness_centrality(G)

            # Sort and return top k
            sorted_scores = sorted(
                closeness_scores.items(), key=lambda x: x[1], reverse=True
            )

            top_nodes = dict(sorted_scores[:top_k])

            logger.info(
                f"Calculated closeness centrality for {len(closeness_scores)} nodes"
            )

            return top_nodes

        except Exception as e:
            logger.error(f"Closeness centrality calculation failed: {e}")
            raise AnalyzerError(f"Closeness centrality failed: {e}")

    def detect_communities(
        self, algorithm: str = "louvain", node_type: Optional[str] = None
    ) -> CommunityResult:
        """Detect communities in the graph.

        Args:
            algorithm: Algorithm to use ('louvain' or 'label_propagation')
            node_type: Optional node type filter

        Returns:
            Community detection results

        Raises:
            AnalyzerError: If detection fails
        """
        if algorithm not in ["louvain", "label_propagation"]:
            raise ValueError("algorithm must be 'louvain' or 'label_propagation'")

        try:
            G = self.load_graph_to_networkx(node_type=node_type)

            if G.number_of_nodes() == 0:
                logger.warning("Empty graph, returning empty communities")
                return CommunityResult(
                    communities={},
                    modularity=0.0,
                    num_communities=0,
                    algorithm=algorithm,
                    community_sizes={},
                )

            # Detect communities based on algorithm
            if algorithm == "louvain":
                partition = community_louvain.best_partition(G)
            else:  # label_propagation
                communities_generator = (
                    nx.algorithms.community.label_propagation_communities(G)
                )
                communities_list = list(communities_generator)

                # Convert to partition format
                partition = {}
                for comm_id, community_nodes in enumerate(communities_list):
                    for node in community_nodes:
                        partition[node] = comm_id

            # Calculate modularity
            communities_sets = defaultdict(set)
            for node, comm_id in partition.items():
                communities_sets[comm_id].add(node)

            modularity = nx.algorithms.community.modularity(
                G, list(communities_sets.values())
            )

            # Convert to result format
            communities = {
                comm_id: list(nodes) for comm_id, nodes in communities_sets.items()
            }

            community_sizes = {
                comm_id: len(nodes) for comm_id, nodes in communities.items()
            }

            logger.info(
                f"Detected {len(communities)} communities using {algorithm}, "
                f"modularity: {modularity:.3f}"
            )

            return CommunityResult(
                communities=communities,
                modularity=modularity,
                num_communities=len(communities),
                algorithm=algorithm,
                community_sizes=community_sizes,
            )

        except Exception as e:
            logger.error(f"Community detection failed: {e}")
            raise AnalyzerError(f"Community detection failed: {e}")

    def find_all_shortest_paths(
        self, source: str, target: str, node_type: Optional[str] = None
    ) -> List[PathResult]:
        """Find all shortest paths between two nodes.

        Args:
            source: Source node ID
            target: Target node ID
            node_type: Optional node type filter

        Returns:
            List of shortest paths

        Raises:
            AnalyzerError: If path finding fails
        """
        try:
            G = self.load_graph_to_networkx(node_type=node_type)

            if source not in G or target not in G:
                logger.warning(f"Source or target not in graph")
                return []

            # Find all shortest paths
            try:
                paths_generator = nx.all_shortest_paths(G, source, target)
                paths = list(paths_generator)
            except nx.NetworkXNoPath:
                logger.info(f"No path found between {source} and {target}")
                return []

            # Convert to PathResult objects
            results = []
            for path in paths:
                results.append(
                    PathResult(path=path, length=len(path) - 1, cost=len(path) - 1)
                )

            logger.info(f"Found {len(results)} shortest path(s)")

            return results

        except Exception as e:
            logger.error(f"Shortest path finding failed: {e}")
            raise AnalyzerError(f"Path finding failed: {e}")

    def calculate_graph_metrics(self, node_type: Optional[str] = None) -> GraphMetrics:
        """Calculate comprehensive graph metrics.

        Args:
            node_type: Optional node type filter

        Returns:
            Graph metrics

        Raises:
            AnalyzerError: If calculation fails
        """
        try:
            G = self.load_graph_to_networkx(node_type=node_type)

            node_count = G.number_of_nodes()
            edge_count = G.number_of_edges()

            if node_count == 0:
                return GraphMetrics(
                    node_count=0,
                    edge_count=0,
                    density=0.0,
                    avg_degree=0.0,
                    diameter=None,
                    clustering_coefficient=0.0,
                    avg_clustering=0.0,
                    connected_components=0,
                    is_connected=False,
                )

            # Basic metrics
            density = nx.density(G)
            avg_degree = sum(dict(G.degree()).values()) / node_count

            # Clustering
            clustering_coefficient = nx.transitivity(G)
            avg_clustering = nx.average_clustering(G)

            # Connected components
            is_connected = nx.is_connected(G)
            num_components = nx.number_connected_components(G)

            # Diameter (only for connected graphs)
            diameter = None
            if is_connected:
                try:
                    diameter = nx.diameter(G)
                except Exception as e:
                    logger.warning(f"Could not calculate diameter: {e}")

            metrics = GraphMetrics(
                node_count=node_count,
                edge_count=edge_count,
                density=density,
                avg_degree=avg_degree,
                diameter=diameter,
                clustering_coefficient=clustering_coefficient,
                avg_clustering=avg_clustering,
                connected_components=num_components,
                is_connected=is_connected,
            )

            logger.info(
                f"Calculated graph metrics: {node_count} nodes, {edge_count} edges"
            )

            return metrics

        except Exception as e:
            logger.error(f"Graph metrics calculation failed: {e}")
            raise AnalyzerError(f"Metrics calculation failed: {e}")

    def identify_bridge_nodes(
        self, node_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Identify bridge nodes that connect different communities.

        Args:
            node_type: Optional node type filter

        Returns:
            List of bridge nodes with metadata

        Raises:
            AnalyzerError: If identification fails
        """
        try:
            G = self.load_graph_to_networkx(node_type=node_type)

            if G.number_of_nodes() < 3:
                return []

            # Detect communities first
            communities_result = self.detect_communities(node_type=node_type)
            partition = {}
            for comm_id, nodes in communities_result.communities.items():
                for node in nodes:
                    partition[node] = comm_id

            # Find bridge nodes - nodes with neighbors in multiple communities
            bridge_nodes = []

            for node in G.nodes():
                node_community = partition.get(node)
                if node_community is None:
                    continue

                # Get neighbor communities
                neighbor_communities = set()
                for neighbor in G.neighbors(node):
                    neighbor_comm = partition.get(neighbor)
                    if neighbor_comm is not None and neighbor_comm != node_community:
                        neighbor_communities.add(neighbor_comm)

                # If node connects to multiple other communities, it's a bridge
                if len(neighbor_communities) >= 2:
                    bridge_nodes.append(
                        {
                            "node_id": node,
                            "community": node_community,
                            "connected_communities": list(neighbor_communities),
                            "num_connections": len(neighbor_communities),
                            "degree": G.degree(node),
                        }
                    )

            # Sort by number of connections
            bridge_nodes.sort(key=lambda x: x["num_connections"], reverse=True)

            logger.info(f"Identified {len(bridge_nodes)} bridge nodes")

            return bridge_nodes

        except Exception as e:
            logger.error(f"Bridge node identification failed: {e}")
            raise AnalyzerError(f"Bridge identification failed: {e}")

    def get_node_importance(
        self, entity_id: str, node_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """Calculate multiple importance measures for a node.

        Args:
            entity_id: Node ID
            node_type: Optional node type filter

        Returns:
            Dictionary of importance metrics

        Raises:
            AnalyzerError: If calculation fails
        """
        try:
            G = self.load_graph_to_networkx(node_type=node_type)

            if entity_id not in G:
                raise ValueError(f"Node {entity_id} not found in graph")

            # Calculate various centrality measures
            pagerank = nx.pagerank(G, alpha=0.85)
            betweenness = nx.betweenness_centrality(G, normalized=True)
            closeness = nx.closeness_centrality(G)
            degree_centrality = nx.degree_centrality(G)

            # Local clustering coefficient
            clustering = nx.clustering(G, entity_id)

            importance = {
                "node_id": entity_id,
                "pagerank": pagerank.get(entity_id, 0.0),
                "betweenness": betweenness.get(entity_id, 0.0),
                "closeness": closeness.get(entity_id, 0.0),
                "degree_centrality": degree_centrality.get(entity_id, 0.0),
                "clustering_coefficient": clustering,
                "degree": G.degree(entity_id),
            }

            logger.info(f"Calculated importance metrics for node {entity_id}")

            return importance

        except Exception as e:
            logger.error(f"Node importance calculation failed: {e}")
            raise AnalyzerError(f"Importance calculation failed: {e}")

    def cluster_entities_by_similarity(
        self, entity_type: str, threshold: float = 0.8
    ) -> Dict[str, List[str]]:
        """Cluster entities by structural similarity.

        Args:
            entity_type: Node label to cluster
            threshold: Similarity threshold (0-1)

        Returns:
            Dictionary mapping cluster IDs to entity IDs

        Raises:
            AnalyzerError: If clustering fails
        """
        try:
            G = self.load_graph_to_networkx(node_type=entity_type)

            if G.number_of_nodes() < 2:
                return {"cluster_0": list(G.nodes())}

            # Calculate similarity based on common neighbors
            nodes = list(G.nodes())
            similarity_matrix = {}

            for i, node1 in enumerate(nodes):
                for node2 in nodes[i + 1 :]:
                    neighbors1 = set(G.neighbors(node1))
                    neighbors2 = set(G.neighbors(node2))

                    # Jaccard similarity
                    intersection = len(neighbors1 & neighbors2)
                    union = len(neighbors1 | neighbors2)

                    if union > 0:
                        similarity = intersection / union
                        if similarity >= threshold:
                            if node1 not in similarity_matrix:
                                similarity_matrix[node1] = []
                            if node2 not in similarity_matrix:
                                similarity_matrix[node2] = []
                            similarity_matrix[node1].append(node2)
                            similarity_matrix[node2].append(node1)

            # Build clusters using connected components
            visited = set()
            clusters = {}
            cluster_id = 0

            for node in nodes:
                if node not in visited:
                    # BFS to find connected component
                    cluster = []
                    queue = [node]
                    visited.add(node)

                    while queue:
                        current = queue.pop(0)
                        cluster.append(current)

                        for neighbor in similarity_matrix.get(current, []):
                            if neighbor not in visited:
                                visited.add(neighbor)
                                queue.append(neighbor)

                    clusters[f"cluster_{cluster_id}"] = cluster
                    cluster_id += 1

            logger.info(
                f"Clustered {len(nodes)} entities into {len(clusters)} clusters"
            )

            return clusters

        except Exception as e:
            logger.error(f"Entity clustering failed: {e}")
            raise AnalyzerError(f"Clustering failed: {e}")

    def _convert_neo4j_to_networkx(self, records: List[Any]) -> nx.Graph:
        """Convert Neo4j query results to NetworkX graph.

        Args:
            records: List of Neo4j records

        Returns:
            NetworkX graph
        """
        G = nx.Graph()

        for record in records:
            # Extract nodes
            node_a = record.get("a")
            node_b = record.get("b")
            rel = record.get("r")

            if node_a and node_b:
                # Add nodes with attributes
                node_a_id = self._get_node_id(node_a)
                node_b_id = self._get_node_id(node_b)

                G.add_node(node_a_id, **dict(node_a))
                G.add_node(node_b_id, **dict(node_b))

                # Add edge with attributes
                if rel:
                    G.add_edge(node_a_id, node_b_id, **dict(rel))
                else:
                    G.add_edge(node_a_id, node_b_id)

        return G

    def _get_node_id(self, node: Any) -> str:
        """Extract node ID from Neo4j node.

        Args:
            node: Neo4j node object

        Returns:
            Node ID as string
        """
        # Try common ID fields
        if hasattr(node, "get"):
            for id_field in ["id", "node_id", "entity_id", "name"]:
                if id_field in node:
                    return str(node[id_field])

        # Fall back to Neo4j internal ID
        if hasattr(node, "id"):
            return str(node.id)

        return str(node)

    def clear_cache(self) -> None:
        """Clear the graph cache."""
        self._graph_cache.clear()
        logger.info("Cleared graph cache")

    def close(self) -> None:
        """Close Neo4j driver connection."""
        if self.driver:
            self.driver.close()
            logger.info("Closed Neo4j connection")


# Utility functions


def create_analyzer(
    uri: str, username: str, password: str, cache_results: bool = True
) -> GraphAnalyzer:
    """Factory function to create a GraphAnalyzer.

    Args:
        uri: Neo4j URI
        username: Neo4j username
        password: Neo4j password
        cache_results: Enable result caching

    Returns:
        Configured GraphAnalyzer instance
    """
    config = AnalyzerConfig(
        neo4j_uri=uri, auth=(username, password), cache_results=cache_results
    )

    return GraphAnalyzer(config)
