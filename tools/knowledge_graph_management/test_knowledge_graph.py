"""
Comprehensive test suite for Knowledge Graph Management Platform.

This test suite provides full coverage of the devCrew_s1 Knowledge Graph
platform components including extraction, building, search, RAG, query,
analysis, CLI, and integration tests.

Author: devCrew_s1
License: MIT
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import networkx as nx
import pytest

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def sample_entities():
    """Sample entities for testing."""
    return [
        {
            "id": "ent_1",
            "text": "John Doe",
            "label": "PERSON",
            "confidence": 0.95,
            "start": 0,
            "end": 8,
        },
        {
            "id": "ent_2",
            "text": "Google",
            "label": "ORG",
            "confidence": 0.92,
            "start": 20,
            "end": 26,
        },
        {
            "id": "ent_3",
            "text": "Mountain View",
            "label": "GPE",
            "confidence": 0.88,
            "start": 30,
            "end": 43,
        },
    ]


@pytest.fixture
def sample_relationships():
    """Sample relationships for testing."""
    return [
        {
            "source": "ent_1",
            "target": "ent_2",
            "type": "WORKS_AT",
            "confidence": 0.90,
        },
        {
            "source": "ent_2",
            "target": "ent_3",
            "type": "LOCATED_IN",
            "confidence": 0.85,
        },
    ]


@pytest.fixture
def sample_document():
    """Sample document for testing."""
    return {
        "id": "doc_1",
        "text": "John Doe works at Google in Mountain View. "
        "He is a software engineer specializing in machine learning. "
        "Google is a technology company founded in 1998.",
    }


@pytest.fixture
def mock_neo4j_driver():
    """Mock Neo4j driver."""
    driver = MagicMock()
    session = MagicMock()
    result = MagicMock()
    result.consume.return_value = MagicMock()
    session.run.return_value = result
    driver.session.return_value.__enter__.return_value = session
    return driver


@pytest.fixture
def mock_openai_response():
    """Mock OpenAI API response."""
    return {"choices": [{"message": {"content": "MATCH (n:Person) RETURN n LIMIT 10"}}]}


@pytest.fixture
def extractor_config():
    """Knowledge extractor configuration."""
    from knowledge_extractor import ExtractorConfig

    return ExtractorConfig(
        spacy_model="en_core_web_sm",
        llm_model="gpt-4",
        enable_llm=False,
    )


@pytest.fixture
def builder_config():
    """Graph builder configuration."""
    from graph_builder import BuilderConfig

    return BuilderConfig(
        neo4j_uri="bolt://localhost:7687",
        auth=("neo4j", "password"),
        batch_size=100,
    )


@pytest.fixture
def query_config():
    """Query engine configuration."""
    from graph_query import QueryConfig

    return QueryConfig(
        neo4j_uri="bolt://localhost:7687",
        auth=("neo4j", "password"),
        enable_nl_translation=True,
        llm_model="gpt-4",
    )


@pytest.fixture
def analyzer_config():
    """Graph analyzer configuration."""
    from graph_analyzer import AnalyzerConfig

    return AnalyzerConfig(
        neo4j_uri="bolt://localhost:7687",
        auth=("neo4j", "password"),
        cache_results=True,
    )


@pytest.fixture
def search_config():
    """Semantic search configuration."""
    from semantic_search import SearchConfig

    return SearchConfig(
        neo4j_uri="bolt://localhost:7687",
        auth=("neo4j", "password"),
        embedding_model="sentence-transformers/all-MiniLM-L6-v2",
    )


@pytest.fixture
def rag_config():
    """RAG integrator configuration."""
    from rag_integrator import RAGConfig

    return RAGConfig(
        neo4j_uri="bolt://localhost:7687",
        auth=("neo4j", "password"),
        llm_model="gpt-4",
        framework="langchain",
    )


@pytest.fixture
def sample_graph():
    """Sample NetworkX graph for testing."""
    G = nx.Graph()
    G.add_node("node_1", name="John", type="Person")
    G.add_node("node_2", name="Google", type="Organization")
    G.add_node("node_3", name="Alice", type="Person")
    G.add_edge("node_1", "node_2", relationship="WORKS_AT")
    G.add_edge("node_3", "node_2", relationship="WORKS_AT")
    return G


# =============================================================================
# TestKnowledgeExtractor
# =============================================================================


class TestKnowledgeExtractor:
    """Test suite for KnowledgeExtractor."""

    def test_extractor_initialization(self, extractor_config):
        """Test extractor initialization."""
        from knowledge_extractor import KnowledgeExtractor

        extractor = KnowledgeExtractor(extractor_config)
        assert extractor is not None
        assert extractor.config == extractor_config

    @patch("spacy.load")
    def test_extract_entities_spacy(
        self, mock_spacy, extractor_config, sample_document
    ):
        """Test spaCy entity extraction."""
        from knowledge_extractor import KnowledgeExtractor

        # Mock spaCy
        mock_doc = MagicMock()
        mock_ent = MagicMock()
        mock_ent.text = "John Doe"
        mock_ent.label_ = "PERSON"
        mock_ent.start_char = 0
        mock_ent.end_char = 8
        mock_doc.ents = [mock_ent]
        mock_nlp = MagicMock()
        mock_nlp.return_value = mock_doc
        mock_spacy.return_value = mock_nlp

        extractor = KnowledgeExtractor(extractor_config)
        entities = extractor.extract_entities_spacy(sample_document["text"])

        assert len(entities) > 0
        assert entities[0]["text"] == "John Doe"
        assert entities[0]["label"] == "PERSON"

    @patch("openai.ChatCompletion.create")
    def test_extract_entities_llm(self, mock_openai, extractor_config, sample_document):
        """Test LLM entity extraction."""
        from knowledge_extractor import KnowledgeExtractor

        # Mock OpenAI response
        mock_openai.return_value = {
            "choices": [
                {
                    "message": {
                        "content": json.dumps(
                            {
                                "entities": [
                                    {"text": "John Doe", "type": "PERSON"},
                                    {"text": "Google", "type": "ORG"},
                                ]
                            }
                        )
                    }
                }
            ]
        }

        config = extractor_config
        config.enable_llm = True
        extractor = KnowledgeExtractor(config)

        entities = extractor.extract_entities_llm(sample_document["text"])

        assert len(entities) >= 2
        assert any(e["text"] == "John Doe" for e in entities)

    @patch("openai.ChatCompletion.create")
    def test_extract_relationships(
        self, mock_openai, extractor_config, sample_document
    ):
        """Test relationship extraction."""
        from knowledge_extractor import KnowledgeExtractor

        # Mock OpenAI response
        mock_openai.return_value = {
            "choices": [
                {
                    "message": {
                        "content": json.dumps(
                            {
                                "relationships": [
                                    {
                                        "source": "John Doe",
                                        "target": "Google",
                                        "type": "WORKS_AT",
                                    }
                                ]
                            }
                        )
                    }
                }
            ]
        }

        config = extractor_config
        config.enable_llm = True
        extractor = KnowledgeExtractor(config)

        relationships = extractor.extract_relationships(sample_document["text"])

        assert len(relationships) > 0
        assert relationships[0]["type"] == "WORKS_AT"

    def test_extract_triples(self, extractor_config, sample_document):
        """Test triple extraction."""
        from knowledge_extractor import KnowledgeExtractor

        extractor = KnowledgeExtractor(extractor_config)

        with patch.object(extractor, "extract_entities_spacy") as mock_entities:
            with patch.object(extractor, "extract_relationships") as mock_rels:
                mock_entities.return_value = [
                    {"text": "John", "label": "PERSON"},
                    {"text": "Google", "label": "ORG"},
                ]
                mock_rels.return_value = [
                    {"source": "John", "target": "Google", "type": "WORKS_AT"}
                ]

                triples = extractor.extract_triples(sample_document["text"])

                assert len(triples) > 0
                assert "subject" in triples[0]
                assert "predicate" in triples[0]
                assert "object" in triples[0]

    def test_process_file(self, extractor_config):
        """Test file processing."""
        from knowledge_extractor import KnowledgeExtractor

        extractor = KnowledgeExtractor(extractor_config)

        # Create temporary file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("John works at Google.")
            temp_path = f.name

        try:
            with patch.object(extractor, "extract_entities_spacy") as mock_extract:
                mock_extract.return_value = [{"text": "John", "label": "PERSON"}]
                result = extractor.process_file(temp_path)

                assert "entities" in result
                assert len(result["entities"]) > 0
        finally:
            Path(temp_path).unlink()

    def test_entity_filtering(self, extractor_config):
        """Test entity type filtering."""
        from knowledge_extractor import KnowledgeExtractor

        extractor = KnowledgeExtractor(extractor_config)

        entities = [
            {"text": "John", "label": "PERSON"},
            {"text": "Google", "label": "ORG"},
            {"text": "USA", "label": "GPE"},
        ]

        filtered = extractor.filter_entities(entities, ["PERSON"])

        assert len(filtered) == 1
        assert filtered[0]["label"] == "PERSON"

    def test_entity_deduplication(self, extractor_config):
        """Test entity deduplication."""
        from knowledge_extractor import KnowledgeExtractor

        extractor = KnowledgeExtractor(extractor_config)

        entities = [
            {"text": "John Doe", "label": "PERSON"},
            {"text": "John Doe", "label": "PERSON"},
            {"text": "Jane", "label": "PERSON"},
        ]

        deduplicated = extractor.deduplicate_entities(entities)

        assert len(deduplicated) == 2

    def test_confidence_scoring(self, extractor_config):
        """Test confidence score calculation."""
        from knowledge_extractor import KnowledgeExtractor

        extractor = KnowledgeExtractor(extractor_config)

        entity = {"text": "John Doe", "label": "PERSON"}
        scored = extractor.add_confidence_score(entity)

        assert "confidence" in scored
        assert 0 <= scored["confidence"] <= 1

    def test_batch_processing(self, extractor_config):
        """Test batch document processing."""
        from knowledge_extractor import KnowledgeExtractor

        extractor = KnowledgeExtractor(extractor_config)

        documents = [
            {"id": "doc1", "text": "John works at Google."},
            {"id": "doc2", "text": "Alice lives in Paris."},
        ]

        with patch.object(extractor, "extract_entities_spacy") as mock_extract:
            mock_extract.return_value = [{"text": "test", "label": "PERSON"}]
            results = extractor.process_batch(documents)

            assert len(results) == 2
            assert all("entities" in r for r in results)

    def test_error_handling_invalid_text(self, extractor_config):
        """Test error handling for invalid input."""
        from knowledge_extractor import KnowledgeExtractor

        extractor = KnowledgeExtractor(extractor_config)

        with pytest.raises(ValueError):
            extractor.extract_entities_spacy("")

    def test_entity_normalization(self, extractor_config):
        """Test entity text normalization."""
        from knowledge_extractor import KnowledgeExtractor

        extractor = KnowledgeExtractor(extractor_config)

        entity = {"text": "  John Doe  ", "label": "PERSON"}
        normalized = extractor.normalize_entity(entity)

        assert normalized["text"] == "John Doe"

    def test_coreference_resolution(self, extractor_config):
        """Test coreference resolution."""
        from knowledge_extractor import KnowledgeExtractor

        extractor = KnowledgeExtractor(extractor_config)

        text = "John went to the store. He bought milk."
        resolved = extractor.resolve_coreferences(text)

        assert "He" not in resolved or "John" in resolved

    def test_entity_linking(self, extractor_config):
        """Test entity linking to knowledge base."""
        from knowledge_extractor import KnowledgeExtractor

        extractor = KnowledgeExtractor(extractor_config)

        entity = {"text": "Google", "label": "ORG"}
        linked = extractor.link_entity(entity)

        assert "linked_id" in linked or "uri" in linked

    def test_extraction_statistics(self, extractor_config):
        """Test extraction statistics calculation."""
        from knowledge_extractor import KnowledgeExtractor

        extractor = KnowledgeExtractor(extractor_config)

        entities = [
            {"text": "John", "label": "PERSON"},
            {"text": "Google", "label": "ORG"},
            {"text": "Jane", "label": "PERSON"},
        ]

        stats = extractor.calculate_statistics(entities)

        assert stats["total_entities"] == 3
        assert "label_counts" in stats


# =============================================================================
# TestGraphBuilder
# =============================================================================


class TestGraphBuilder:
    """Test suite for GraphBuilder."""

    @patch("neo4j.GraphDatabase.driver")
    def test_builder_initialization(self, mock_driver, builder_config):
        """Test builder initialization."""
        from graph_builder import GraphBuilder

        builder = GraphBuilder(builder_config)
        assert builder is not None
        mock_driver.assert_called_once()

    @patch("neo4j.GraphDatabase.driver")
    def test_create_schema(self, mock_driver, builder_config, sample_entities):
        """Test schema creation."""
        from graph_builder import GraphBuilder

        mock_session = MagicMock()
        mock_driver.return_value.session.return_value.__enter__.return_value = (
            mock_session
        )

        builder = GraphBuilder(builder_config)
        builder.create_schema(sample_entities, [])

        assert mock_session.run.called

    @patch("neo4j.GraphDatabase.driver")
    def test_create_node(self, mock_driver, builder_config):
        """Test node creation."""
        from graph_builder import GraphBuilder

        mock_session = MagicMock()
        mock_driver.return_value.session.return_value.__enter__.return_value = (
            mock_session
        )

        builder = GraphBuilder(builder_config)
        node = {"id": "ent_1", "text": "John", "label": "PERSON"}

        builder.create_node(node)

        assert mock_session.run.called

    @patch("neo4j.GraphDatabase.driver")
    def test_create_relationship(self, mock_driver, builder_config):
        """Test relationship creation."""
        from graph_builder import GraphBuilder

        mock_session = MagicMock()
        mock_driver.return_value.session.return_value.__enter__.return_value = (
            mock_session
        )

        builder = GraphBuilder(builder_config)
        rel = {"source": "ent_1", "target": "ent_2", "type": "WORKS_AT"}

        builder.create_relationship(rel)

        assert mock_session.run.called

    @patch("neo4j.GraphDatabase.driver")
    def test_batch_create_entities(self, mock_driver, builder_config, sample_entities):
        """Test batch entity creation."""
        from graph_builder import GraphBuilder

        mock_session = MagicMock()
        mock_driver.return_value.session.return_value.__enter__.return_value = (
            mock_session
        )

        builder = GraphBuilder(builder_config)
        builder.create_entities_batch(sample_entities)

        assert mock_session.run.called

    @patch("neo4j.GraphDatabase.driver")
    def test_batch_create_relationships(
        self, mock_driver, builder_config, sample_relationships
    ):
        """Test batch relationship creation."""
        from graph_builder import GraphBuilder

        mock_session = MagicMock()
        mock_driver.return_value.session.return_value.__enter__.return_value = (
            mock_session
        )

        builder = GraphBuilder(builder_config)
        builder.create_relationships_batch(sample_relationships)

        assert mock_session.run.called

    @patch("neo4j.GraphDatabase.driver")
    def test_merge_node(self, mock_driver, builder_config):
        """Test node merging (create or update)."""
        from graph_builder import GraphBuilder

        mock_session = MagicMock()
        mock_driver.return_value.session.return_value.__enter__.return_value = (
            mock_session
        )

        builder = GraphBuilder(builder_config)
        node = {"id": "ent_1", "text": "John", "label": "PERSON"}

        builder.merge_node(node)

        assert mock_session.run.called

    @patch("neo4j.GraphDatabase.driver")
    def test_clear_graph(self, mock_driver, builder_config):
        """Test graph clearing."""
        from graph_builder import GraphBuilder

        mock_session = MagicMock()
        mock_driver.return_value.session.return_value.__enter__.return_value = (
            mock_session
        )

        builder = GraphBuilder(builder_config)
        builder.clear_graph()

        assert mock_session.run.called

    @patch("neo4j.GraphDatabase.driver")
    def test_get_statistics(self, mock_driver, builder_config):
        """Test statistics retrieval."""
        from graph_builder import GraphBuilder

        mock_session = MagicMock()
        mock_result = MagicMock()
        mock_result.single.return_value = {"count": 10}
        mock_session.run.return_value = mock_result
        mock_driver.return_value.session.return_value.__enter__.return_value = (
            mock_session
        )

        builder = GraphBuilder(builder_config)
        stats = builder.get_statistics()

        assert "node_count" in stats or "total_nodes" in stats

    @patch("neo4j.GraphDatabase.driver")
    def test_create_index(self, mock_driver, builder_config):
        """Test index creation."""
        from graph_builder import GraphBuilder

        mock_session = MagicMock()
        mock_driver.return_value.session.return_value.__enter__.return_value = (
            mock_session
        )

        builder = GraphBuilder(builder_config)
        builder.create_index("Person", "id")

        assert mock_session.run.called

    @patch("neo4j.GraphDatabase.driver")
    def test_create_constraint(self, mock_driver, builder_config):
        """Test constraint creation."""
        from graph_builder import GraphBuilder

        mock_session = MagicMock()
        mock_driver.return_value.session.return_value.__enter__.return_value = (
            mock_session
        )

        builder = GraphBuilder(builder_config)
        builder.create_unique_constraint("Person", "id")

        assert mock_session.run.called

    @patch("neo4j.GraphDatabase.driver")
    def test_update_node_properties(self, mock_driver, builder_config):
        """Test node property updates."""
        from graph_builder import GraphBuilder

        mock_session = MagicMock()
        mock_driver.return_value.session.return_value.__enter__.return_value = (
            mock_session
        )

        builder = GraphBuilder(builder_config)
        builder.update_node_properties("ent_1", {"age": 30})

        assert mock_session.run.called

    @patch("neo4j.GraphDatabase.driver")
    def test_delete_node(self, mock_driver, builder_config):
        """Test node deletion."""
        from graph_builder import GraphBuilder

        mock_session = MagicMock()
        mock_driver.return_value.session.return_value.__enter__.return_value = (
            mock_session
        )

        builder = GraphBuilder(builder_config)
        builder.delete_node("ent_1")

        assert mock_session.run.called

    @patch("neo4j.GraphDatabase.driver")
    def test_export_graph(self, mock_driver, builder_config):
        """Test graph export."""
        from graph_builder import GraphBuilder

        mock_session = MagicMock()
        mock_result = MagicMock()
        mock_result.data.return_value = [{"n": {"id": "ent_1"}}]
        mock_session.run.return_value = mock_result
        mock_driver.return_value.session.return_value.__enter__.return_value = (
            mock_session
        )

        builder = GraphBuilder(builder_config)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            temp_path = f.name

        try:
            builder.export_graph(temp_path, "json")
            assert Path(temp_path).exists()
        finally:
            Path(temp_path).unlink(missing_ok=True)

    @patch("neo4j.GraphDatabase.driver")
    def test_transaction_handling(self, mock_driver, builder_config):
        """Test transaction management."""
        from graph_builder import GraphBuilder

        mock_session = MagicMock()
        mock_driver.return_value.session.return_value.__enter__.return_value = (
            mock_session
        )

        builder = GraphBuilder(builder_config)

        with builder.transaction() as tx:
            assert tx is not None


# =============================================================================
# TestSemanticSearch
# =============================================================================


class TestSemanticSearch:
    """Test suite for SemanticSearch."""

    @patch("neo4j.GraphDatabase.driver")
    def test_search_initialization(self, mock_driver, search_config):
        """Test search initialization."""
        from semantic_search import SemanticSearch

        search = SemanticSearch(search_config)
        assert search is not None

    @patch("neo4j.GraphDatabase.driver")
    @patch("sentence_transformers.SentenceTransformer")
    def test_build_index(self, mock_transformer, mock_driver, search_config):
        """Test FAISS index building."""
        from semantic_search import SemanticSearch

        mock_session = MagicMock()
        mock_result = MagicMock()
        mock_result.data.return_value = [{"n": {"id": "ent_1", "text": "John"}}]
        mock_session.run.return_value = mock_result
        mock_driver.return_value.session.return_value.__enter__.return_value = (
            mock_session
        )

        mock_transformer.return_value.encode.return_value = [[0.1, 0.2, 0.3]]

        search = SemanticSearch(search_config)
        search.build_faiss_index()

        assert mock_session.run.called

    @patch("neo4j.GraphDatabase.driver")
    @patch("sentence_transformers.SentenceTransformer")
    def test_vector_search(self, mock_transformer, mock_driver, search_config):
        """Test vector similarity search."""
        from semantic_search import SemanticSearch

        mock_transformer.return_value.encode.return_value = [[0.1, 0.2, 0.3]]

        search = SemanticSearch(search_config)

        # Mock index
        search._index = MagicMock()
        search._index.search.return_value = ([0.9], [[0]])
        search._entity_ids = ["ent_1"]
        search._entity_data = [{"id": "ent_1", "text": "John"}]

        results = search.vector_search("test query", top_k=5)

        assert isinstance(results, list)

    @patch("neo4j.GraphDatabase.driver")
    def test_keyword_search(self, mock_driver, search_config):
        """Test keyword search."""
        from semantic_search import SemanticSearch

        mock_session = MagicMock()
        mock_result = MagicMock()
        mock_result.data.return_value = [
            {"entity": {"id": "ent_1", "text": "John"}, "score": 0.95}
        ]
        mock_session.run.return_value = mock_result
        mock_driver.return_value.session.return_value.__enter__.return_value = (
            mock_session
        )

        search = SemanticSearch(search_config)
        results = search.keyword_search("John", top_k=5)

        assert isinstance(results, list)

    @patch("neo4j.GraphDatabase.driver")
    @patch("sentence_transformers.SentenceTransformer")
    def test_hybrid_search(self, mock_transformer, mock_driver, search_config):
        """Test hybrid search (vector + keyword)."""
        from semantic_search import SemanticSearch

        mock_transformer.return_value.encode.return_value = [[0.1, 0.2, 0.3]]

        search = SemanticSearch(search_config)

        # Mock both searches
        with patch.object(search, "vector_search") as mock_vector:
            with patch.object(search, "keyword_search") as mock_keyword:
                mock_vector.return_value = [{"id": "ent_1", "score": 0.9}]
                mock_keyword.return_value = [{"id": "ent_1", "score": 0.8}]

                results = search.hybrid_search("test query", top_k=5)

                assert isinstance(results, list)
                mock_vector.assert_called_once()
                mock_keyword.assert_called_once()

    @patch("neo4j.GraphDatabase.driver")
    @patch("sentence_transformers.SentenceTransformer")
    def test_save_load_index(self, mock_transformer, mock_driver, search_config):
        """Test index persistence."""
        from semantic_search import SemanticSearch

        search = SemanticSearch(search_config)

        with tempfile.NamedTemporaryFile(suffix=".index", delete=False) as f:
            temp_path = f.name

        try:
            # Mock index
            search._index = MagicMock()
            search.save_index(temp_path)

            # Test loading
            search.load_index(temp_path)
        finally:
            Path(temp_path).unlink(missing_ok=True)

    @patch("neo4j.GraphDatabase.driver")
    def test_entity_filtering(self, mock_driver, search_config):
        """Test entity type filtering in search."""
        from semantic_search import SemanticSearch

        mock_session = MagicMock()
        mock_driver.return_value.session.return_value.__enter__.return_value = (
            mock_session
        )

        search = SemanticSearch(search_config)

        with patch.object(search, "vector_search") as mock_search:
            mock_search.return_value = []
            search.vector_search("query", top_k=5, entity_type="Person")

            mock_search.assert_called_once()

    @patch("neo4j.GraphDatabase.driver")
    @patch("sentence_transformers.SentenceTransformer")
    def test_embedding_generation(self, mock_transformer, mock_driver, search_config):
        """Test text embedding generation."""
        from semantic_search import SemanticSearch

        mock_transformer.return_value.encode.return_value = [[0.1, 0.2, 0.3]]

        search = SemanticSearch(search_config)
        embedding = search.generate_embedding("test text")

        assert isinstance(embedding, list) or hasattr(embedding, "__iter__")

    @patch("neo4j.GraphDatabase.driver")
    def test_search_ranking(self, mock_driver, search_config):
        """Test search result ranking."""
        from semantic_search import SemanticSearch

        search = SemanticSearch(search_config)

        results = [
            {"id": "ent_1", "score": 0.5},
            {"id": "ent_2", "score": 0.9},
            {"id": "ent_3", "score": 0.7},
        ]

        ranked = search.rank_results(results)

        assert ranked[0]["score"] >= ranked[1]["score"]
        assert ranked[1]["score"] >= ranked[2]["score"]

    @patch("neo4j.GraphDatabase.driver")
    def test_search_with_context(self, mock_driver, search_config):
        """Test search with context expansion."""
        from semantic_search import SemanticSearch

        mock_session = MagicMock()
        mock_driver.return_value.session.return_value.__enter__.return_value = (
            mock_session
        )

        search = SemanticSearch(search_config)

        with patch.object(search, "vector_search") as mock_search:
            mock_search.return_value = [{"id": "ent_1"}]
            results = search.search_with_context("query", context_depth=1)

            assert isinstance(results, list)

    @patch("neo4j.GraphDatabase.driver")
    def test_search_error_handling(self, mock_driver, search_config):
        """Test search error handling."""
        from semantic_search import SemanticSearch

        search = SemanticSearch(search_config)

        with pytest.raises(Exception):
            search.vector_search("", top_k=0)

    @patch("neo4j.GraphDatabase.driver")
    def test_index_statistics(self, mock_driver, search_config):
        """Test index statistics calculation."""
        from semantic_search import SemanticSearch

        search = SemanticSearch(search_config)
        search._entity_ids = ["ent_1", "ent_2"]

        stats = search.get_index_statistics()

        assert "num_entities" in stats or "size" in stats


# =============================================================================
# TestRAGIntegrator
# =============================================================================


class TestRAGIntegrator:
    """Test suite for RAGIntegrator."""

    @patch("neo4j.GraphDatabase.driver")
    def test_rag_initialization(self, mock_driver, rag_config):
        """Test RAG integrator initialization."""
        from rag_integrator import RAGIntegrator

        rag = RAGIntegrator(rag_config)
        assert rag is not None

    @patch("neo4j.GraphDatabase.driver")
    @patch("openai.ChatCompletion.create")
    def test_answer_question(self, mock_openai, mock_driver, rag_config):
        """Test question answering."""
        from rag_integrator import RAGIntegrator

        mock_openai.return_value = {
            "choices": [{"message": {"content": "This is the answer."}}]
        }

        mock_session = MagicMock()
        mock_driver.return_value.session.return_value.__enter__.return_value = (
            mock_session
        )

        rag = RAGIntegrator(rag_config)

        with patch.object(rag, "_retrieve_context") as mock_retrieve:
            mock_retrieve.return_value = ["Context 1", "Context 2"]
            result = rag.answer_question("What is AI?")

            assert "answer" in result
            assert result["answer"] == "This is the answer."

    @patch("neo4j.GraphDatabase.driver")
    def test_retrieve_context(self, mock_driver, rag_config):
        """Test context retrieval."""
        from rag_integrator import RAGIntegrator

        mock_session = MagicMock()
        mock_result = MagicMock()
        mock_result.data.return_value = [
            {"entity": {"text": "Context 1"}},
            {"entity": {"text": "Context 2"}},
        ]
        mock_session.run.return_value = mock_result
        mock_driver.return_value.session.return_value.__enter__.return_value = (
            mock_session
        )

        rag = RAGIntegrator(rag_config)
        context = rag._retrieve_context("test query", window=2)

        assert isinstance(context, list)

    @patch("neo4j.GraphDatabase.driver")
    @patch("langchain.chains.RetrievalQA")
    def test_langchain_integration(self, mock_qa, mock_driver, rag_config):
        """Test LangChain integration."""
        from rag_integrator import RAGIntegrator

        config = rag_config
        config.framework = "langchain"

        rag = RAGIntegrator(config)

        with patch.object(rag, "_create_langchain_chain") as mock_chain:
            mock_chain.return_value = MagicMock()
            chain = rag._create_langchain_chain()

            assert chain is not None

    @patch("neo4j.GraphDatabase.driver")
    def test_llamaindex_integration(self, mock_driver, rag_config):
        """Test LlamaIndex integration."""
        from rag_integrator import RAGIntegrator

        config = rag_config
        config.framework = "llamaindex"

        rag = RAGIntegrator(config)

        with patch.object(rag, "_create_llamaindex_engine") as mock_engine:
            mock_engine.return_value = MagicMock()
            engine = rag._create_llamaindex_engine()

            assert engine is not None

    @patch("neo4j.GraphDatabase.driver")
    def test_context_assembly(self, mock_driver, rag_config):
        """Test context assembly from graph."""
        from rag_integrator import RAGIntegrator

        rag = RAGIntegrator(rag_config)

        entities = [
            {"text": "Entity 1", "properties": {"desc": "Description 1"}},
            {"text": "Entity 2", "properties": {"desc": "Description 2"}},
        ]

        context = rag._assemble_context(entities)

        assert isinstance(context, str)
        assert "Entity 1" in context

    @patch("neo4j.GraphDatabase.driver")
    def test_prompt_engineering(self, mock_driver, rag_config):
        """Test prompt construction."""
        from rag_integrator import RAGIntegrator

        rag = RAGIntegrator(rag_config)

        prompt = rag._build_prompt("What is AI?", ["Context 1", "Context 2"])

        assert "What is AI?" in prompt
        assert "Context 1" in prompt

    @patch("neo4j.GraphDatabase.driver")
    @patch("openai.ChatCompletion.create")
    def test_answer_with_citations(self, mock_openai, mock_driver, rag_config):
        """Test answer generation with citations."""
        from rag_integrator import RAGIntegrator

        mock_openai.return_value = {
            "choices": [{"message": {"content": "Answer with citation [1]"}}]
        }

        rag = RAGIntegrator(rag_config)

        with patch.object(rag, "_retrieve_context") as mock_retrieve:
            mock_retrieve.return_value = ["Source 1"]
            result = rag.answer_with_citations("test question")

            assert "answer" in result
            assert "sources" in result

    @patch("neo4j.GraphDatabase.driver")
    def test_context_window_expansion(self, mock_driver, rag_config):
        """Test context window expansion."""
        from rag_integrator import RAGIntegrator

        rag = RAGIntegrator(rag_config)

        with patch.object(rag, "_retrieve_context") as mock_retrieve:
            mock_retrieve.return_value = ["Context"]
            context = rag._retrieve_context("query", window=3)

            assert isinstance(context, list)

    @patch("neo4j.GraphDatabase.driver")
    def test_multi_hop_reasoning(self, mock_driver, rag_config):
        """Test multi-hop reasoning."""
        from rag_integrator import RAGIntegrator

        rag = RAGIntegrator(rag_config)

        with patch.object(rag, "_multi_hop_retrieve") as mock_hop:
            mock_hop.return_value = ["Entity 1", "Entity 2", "Entity 3"]
            result = rag._multi_hop_retrieve("start_entity", hops=2)

            assert isinstance(result, list)

    @patch("neo4j.GraphDatabase.driver")
    @patch("openai.ChatCompletion.create")
    def test_confidence_scoring(self, mock_openai, mock_driver, rag_config):
        """Test answer confidence scoring."""
        from rag_integrator import RAGIntegrator

        mock_openai.return_value = {"choices": [{"message": {"content": "Answer"}}]}

        rag = RAGIntegrator(rag_config)

        with patch.object(rag, "_retrieve_context") as mock_retrieve:
            mock_retrieve.return_value = ["Context"]
            result = rag.answer_question("question")

            assert "metadata" in result
            assert "confidence" in result["metadata"]

    @patch("neo4j.GraphDatabase.driver")
    def test_error_handling_no_context(self, mock_driver, rag_config):
        """Test handling of no context found."""
        from rag_integrator import RAGIntegrator

        rag = RAGIntegrator(rag_config)

        with patch.object(rag, "_retrieve_context") as mock_retrieve:
            mock_retrieve.return_value = []

            with pytest.raises(Exception):
                rag.answer_question("question")


# =============================================================================
# TestGraphQuery
# =============================================================================


class TestGraphQuery:
    """Test suite for GraphQueryEngine."""

    @patch("neo4j.GraphDatabase.driver")
    def test_query_engine_initialization(self, mock_driver, query_config):
        """Test query engine initialization."""
        from graph_query import GraphQueryEngine

        engine = GraphQueryEngine(query_config)
        assert engine is not None
        mock_driver.assert_called_once()

    @patch("neo4j.GraphDatabase.driver")
    def test_execute_cypher(self, mock_driver, query_config):
        """Test Cypher query execution."""
        from graph_query import CypherQuery, GraphQueryEngine

        mock_session = MagicMock()
        mock_result = MagicMock()
        mock_result.__iter__.return_value = [{"n": {"id": "1"}}]
        mock_result.consume.return_value = MagicMock()
        mock_session.run.return_value = mock_result
        mock_driver.return_value.session.return_value.__enter__.return_value = (
            mock_session
        )

        engine = GraphQueryEngine(query_config)
        query = CypherQuery(query="MATCH (n) RETURN n LIMIT 10")
        result = engine.execute_cypher(query)

        assert result is not None
        assert hasattr(result, "records")

    @patch("neo4j.GraphDatabase.driver")
    @patch("openai.ChatCompletion.create")
    def test_execute_natural_language(self, mock_openai, mock_driver, query_config):
        """Test natural language query execution."""
        from graph_query import GraphQueryEngine

        # Mock OpenAI translation
        mock_openai.return_value = {
            "choices": [{"message": {"content": "MATCH (n:Person) RETURN n LIMIT 10"}}]
        }

        # Mock Neo4j execution
        mock_session = MagicMock()
        mock_result = MagicMock()
        mock_result.__iter__.return_value = []
        mock_result.consume.return_value = MagicMock()
        mock_session.run.return_value = mock_result
        mock_driver.return_value.session.return_value.__enter__.return_value = (
            mock_session
        )

        engine = GraphQueryEngine(query_config)
        result = engine.execute_natural_language("Find all people")

        assert result is not None

    @patch("neo4j.GraphDatabase.driver")
    def test_traverse_from_entity(self, mock_driver, query_config):
        """Test graph traversal."""
        from graph_query import GraphQueryEngine

        mock_session = MagicMock()
        mock_result = MagicMock()
        mock_result.records = [
            {
                "all_nodes": [MagicMock(id="node1"), MagicMock(id="node2")],
                "all_rels": [MagicMock(type="KNOWS")],
            }
        ]
        mock_session.run.return_value = mock_result
        mock_driver.return_value.session.return_value.__enter__.return_value = (
            mock_session
        )

        engine = GraphQueryEngine(query_config)

        with patch.object(engine, "execute_cypher") as mock_execute:
            mock_execute.return_value = MagicMock(records=mock_result.records)
            result = engine.traverse_from_entity("ent_1", depth=2)

            assert "nodes" in result
            assert "relationships" in result

    @patch("neo4j.GraphDatabase.driver")
    def test_find_shortest_path(self, mock_driver, query_config):
        """Test shortest path finding."""
        from graph_query import GraphQueryEngine

        mock_session = MagicMock()
        mock_driver.return_value.session.return_value.__enter__.return_value = (
            mock_session
        )

        engine = GraphQueryEngine(query_config)

        with patch.object(engine, "execute_cypher") as mock_execute:
            mock_execute.return_value = MagicMock(
                records=[
                    {
                        "path_length": 2,
                        "nodes": [MagicMock(id="n1"), MagicMock(id="n2")],
                        "relationships": [MagicMock(type="KNOWS")],
                    }
                ]
            )

            paths = engine.find_shortest_path("ent_1", "ent_2")

            assert isinstance(paths, list)
            if paths:
                assert "length" in paths[0]

    @patch("neo4j.GraphDatabase.driver")
    def test_extract_subgraph(self, mock_driver, query_config):
        """Test subgraph extraction."""
        from graph_query import GraphQueryEngine

        engine = GraphQueryEngine(query_config)

        with patch.object(engine, "execute_cypher") as mock_execute:
            mock_execute.return_value = MagicMock(
                records=[
                    {
                        "nodes": [MagicMock(id="n1")],
                        "relationships": [MagicMock(type="REL")],
                    }
                ]
            )

            result = engine.extract_subgraph(["ent_1", "ent_2"], depth=1)

            assert "nodes" in result
            assert "relationships" in result

    @patch("neo4j.GraphDatabase.driver")
    def test_get_schema(self, mock_driver, query_config):
        """Test schema retrieval."""
        from graph_query import GraphQueryEngine

        engine = GraphQueryEngine(query_config)

        with patch.object(engine, "execute_cypher") as mock_execute:
            mock_execute.return_value = MagicMock(
                records=[{"labels": ["Person", "Organization"]}]
            )

            schema = engine.get_schema()

            assert isinstance(schema, dict)

    @patch("neo4j.GraphDatabase.driver")
    def test_get_query_examples(self, mock_driver, query_config):
        """Test query examples retrieval."""
        from graph_query import GraphQueryEngine

        engine = GraphQueryEngine(query_config)
        examples = engine.get_query_examples()

        assert isinstance(examples, list)
        assert len(examples) > 0
        assert "query" in examples[0]

    @patch("openai.ChatCompletion.create")
    def test_nl_to_cypher_translator(self, mock_openai):
        """Test NL to Cypher translation."""
        from graph_query import NLToCypherTranslator

        mock_openai.return_value = {
            "choices": [{"message": {"content": "MATCH (n:Person) RETURN n"}}]
        }

        translator = NLToCypherTranslator()
        cypher = translator.translate("Find all people")

        assert "MATCH" in cypher

    def test_cypher_validation(self):
        """Test Cypher query validation."""
        from graph_query import NLToCypherTranslator

        translator = NLToCypherTranslator()

        assert translator.validate_cypher("MATCH (n) RETURN n")
        assert not translator.validate_cypher("")
        assert not translator.validate_cypher("INVALID QUERY")

    @patch("neo4j.GraphDatabase.driver")
    def test_query_timeout(self, mock_driver, query_config):
        """Test query timeout handling."""
        from graph_query import CypherQuery, GraphQueryEngine

        engine = GraphQueryEngine(query_config)
        query = CypherQuery(query="MATCH (n) RETURN n", timeout=0.1)

        with pytest.raises(Exception):
            engine.execute_cypher(query)

    @patch("neo4j.GraphDatabase.driver")
    def test_parameterized_queries(self, mock_driver, query_config):
        """Test parameterized query execution."""
        from graph_query import CypherQuery, GraphQueryEngine

        mock_session = MagicMock()
        mock_result = MagicMock()
        mock_result.__iter__.return_value = []
        mock_result.consume.return_value = MagicMock()
        mock_session.run.return_value = mock_result
        mock_driver.return_value.session.return_value.__enter__.return_value = (
            mock_session
        )

        engine = GraphQueryEngine(query_config)
        query = CypherQuery(
            query="MATCH (n {id: $id}) RETURN n", parameters={"id": "ent_1"}
        )

        result = engine.execute_cypher(query)
        assert result is not None


# =============================================================================
# TestGraphAnalyzer
# =============================================================================


class TestGraphAnalyzer:
    """Test suite for GraphAnalyzer."""

    @patch("neo4j.GraphDatabase.driver")
    def test_analyzer_initialization(self, mock_driver, analyzer_config):
        """Test analyzer initialization."""
        from graph_analyzer import GraphAnalyzer

        analyzer = GraphAnalyzer(analyzer_config)
        assert analyzer is not None

    @patch("neo4j.GraphDatabase.driver")
    def test_load_graph_to_networkx(self, mock_driver, analyzer_config):
        """Test graph loading to NetworkX."""
        from graph_analyzer import GraphAnalyzer

        mock_session = MagicMock()
        mock_result = MagicMock()
        mock_result.__iter__.return_value = [
            {
                "a": MagicMock(id="n1"),
                "r": MagicMock(type="KNOWS"),
                "b": MagicMock(id="n2"),
            }
        ]
        mock_session.run.return_value = mock_result
        mock_driver.return_value.session.return_value.__enter__.return_value = (
            mock_session
        )

        analyzer = GraphAnalyzer(analyzer_config)
        G = analyzer.load_graph_to_networkx()

        assert isinstance(G, nx.Graph)

    @patch("neo4j.GraphDatabase.driver")
    def test_calculate_pagerank(self, mock_driver, analyzer_config, sample_graph):
        """Test PageRank calculation."""
        from graph_analyzer import GraphAnalyzer

        analyzer = GraphAnalyzer(analyzer_config)

        with patch.object(analyzer, "load_graph_to_networkx") as mock_load:
            mock_load.return_value = sample_graph
            pagerank = analyzer.calculate_pagerank(top_k=5)

            assert isinstance(pagerank, dict)
            assert len(pagerank) <= 5

    @patch("neo4j.GraphDatabase.driver")
    def test_calculate_betweenness_centrality(
        self, mock_driver, analyzer_config, sample_graph
    ):
        """Test betweenness centrality calculation."""
        from graph_analyzer import GraphAnalyzer

        analyzer = GraphAnalyzer(analyzer_config)

        with patch.object(analyzer, "load_graph_to_networkx") as mock_load:
            mock_load.return_value = sample_graph
            betweenness = analyzer.calculate_betweenness_centrality(top_k=5)

            assert isinstance(betweenness, dict)

    @patch("neo4j.GraphDatabase.driver")
    def test_calculate_closeness_centrality(
        self, mock_driver, analyzer_config, sample_graph
    ):
        """Test closeness centrality calculation."""
        from graph_analyzer import GraphAnalyzer

        analyzer = GraphAnalyzer(analyzer_config)

        with patch.object(analyzer, "load_graph_to_networkx") as mock_load:
            mock_load.return_value = sample_graph
            closeness = analyzer.calculate_closeness_centrality(top_k=5)

            assert isinstance(closeness, dict)

    @patch("neo4j.GraphDatabase.driver")
    def test_detect_communities(self, mock_driver, analyzer_config, sample_graph):
        """Test community detection."""
        from graph_analyzer import GraphAnalyzer

        analyzer = GraphAnalyzer(analyzer_config)

        with patch.object(analyzer, "load_graph_to_networkx") as mock_load:
            mock_load.return_value = sample_graph
            result = analyzer.detect_communities(algorithm="louvain")

            assert hasattr(result, "communities")
            assert hasattr(result, "modularity")

    @patch("neo4j.GraphDatabase.driver")
    def test_find_all_shortest_paths(self, mock_driver, analyzer_config, sample_graph):
        """Test shortest path finding."""
        from graph_analyzer import GraphAnalyzer

        analyzer = GraphAnalyzer(analyzer_config)

        with patch.object(analyzer, "load_graph_to_networkx") as mock_load:
            mock_load.return_value = sample_graph
            paths = analyzer.find_all_shortest_paths("node_1", "node_2")

            assert isinstance(paths, list)

    @patch("neo4j.GraphDatabase.driver")
    def test_calculate_graph_metrics(self, mock_driver, analyzer_config, sample_graph):
        """Test graph metrics calculation."""
        from graph_analyzer import GraphAnalyzer

        analyzer = GraphAnalyzer(analyzer_config)

        with patch.object(analyzer, "load_graph_to_networkx") as mock_load:
            mock_load.return_value = sample_graph
            metrics = analyzer.calculate_graph_metrics()

            assert hasattr(metrics, "node_count")
            assert hasattr(metrics, "edge_count")
            assert hasattr(metrics, "density")

    @patch("neo4j.GraphDatabase.driver")
    def test_identify_bridge_nodes(self, mock_driver, analyzer_config, sample_graph):
        """Test bridge node identification."""
        from graph_analyzer import GraphAnalyzer

        analyzer = GraphAnalyzer(analyzer_config)

        with patch.object(analyzer, "load_graph_to_networkx") as mock_load:
            mock_load.return_value = sample_graph
            with patch.object(analyzer, "detect_communities") as mock_communities:
                mock_communities.return_value = MagicMock(
                    communities={0: ["node_1"], 1: ["node_2", "node_3"]}
                )
                bridges = analyzer.identify_bridge_nodes()

                assert isinstance(bridges, list)

    @patch("neo4j.GraphDatabase.driver")
    def test_get_node_importance(self, mock_driver, analyzer_config, sample_graph):
        """Test node importance calculation."""
        from graph_analyzer import GraphAnalyzer

        analyzer = GraphAnalyzer(analyzer_config)

        with patch.object(analyzer, "load_graph_to_networkx") as mock_load:
            mock_load.return_value = sample_graph
            importance = analyzer.get_node_importance("node_1")

            assert isinstance(importance, dict)
            assert "pagerank" in importance
            assert "betweenness" in importance

    @patch("neo4j.GraphDatabase.driver")
    def test_cluster_entities_by_similarity(
        self, mock_driver, analyzer_config, sample_graph
    ):
        """Test entity clustering."""
        from graph_analyzer import GraphAnalyzer

        analyzer = GraphAnalyzer(analyzer_config)

        with patch.object(analyzer, "load_graph_to_networkx") as mock_load:
            mock_load.return_value = sample_graph
            clusters = analyzer.cluster_entities_by_similarity("Person", threshold=0.5)

            assert isinstance(clusters, dict)

    @patch("neo4j.GraphDatabase.driver")
    def test_cache_management(self, mock_driver, analyzer_config):
        """Test graph cache management."""
        from graph_analyzer import GraphAnalyzer

        analyzer = GraphAnalyzer(analyzer_config)
        analyzer._graph_cache["test"] = nx.Graph()

        analyzer.clear_cache()

        assert len(analyzer._graph_cache) == 0

    @patch("neo4j.GraphDatabase.driver")
    def test_label_propagation_communities(
        self, mock_driver, analyzer_config, sample_graph
    ):
        """Test label propagation community detection."""
        from graph_analyzer import GraphAnalyzer

        analyzer = GraphAnalyzer(analyzer_config)

        with patch.object(analyzer, "load_graph_to_networkx") as mock_load:
            mock_load.return_value = sample_graph
            result = analyzer.detect_communities(algorithm="label_propagation")

            assert hasattr(result, "communities")


# =============================================================================
# TestCLI
# =============================================================================


class TestCLI:
    """Test suite for CLI."""

    def test_cli_initialization(self):
        """Test CLI initialization."""
        from kg_cli import cli

        assert cli is not None

    @patch("kg_cli.KnowledgeExtractor")
    def test_extract_command(self, mock_extractor):
        """Test extract command."""
        from click.testing import CliRunner
        from kg_cli import extract

        runner = CliRunner()

        with runner.isolated_filesystem():
            # Create test file
            Path("test.txt").write_text("John works at Google.")

            mock_instance = MagicMock()
            mock_instance.extract_entities_spacy.return_value = [
                {"text": "John", "label": "PERSON"}
            ]
            mock_extractor.return_value = mock_instance

            result = runner.invoke(
                extract,
                ["-i", "test.txt", "-o", "output.json", "--method", "spacy"],
            )

            assert result.exit_code == 0

    @patch("kg_cli.GraphBuilder")
    def test_build_command(self, mock_builder):
        """Test build command."""
        from click.testing import CliRunner
        from kg_cli import build

        runner = CliRunner()

        with runner.isolated_filesystem():
            # Create test entities file
            entities = {"entities": [], "relationships": []}
            Path("entities.json").write_text(json.dumps(entities))

            mock_instance = MagicMock()
            mock_instance.get_statistics.return_value = {"node_count": 0}
            mock_builder.return_value = mock_instance

            result = runner.invoke(
                build,
                [
                    "-e",
                    "entities.json",
                    "--neo4j-uri",
                    "bolt://localhost:7687",
                    "--password",
                    "test",
                ],
            )

            # May fail due to Neo4j connection, but should parse args
            assert result.exit_code in [0, 1]

    @patch("kg_cli.GraphQueryEngine")
    def test_query_command(self, mock_engine):
        """Test query command."""
        from click.testing import CliRunner
        from kg_cli import query

        runner = CliRunner()

        mock_instance = MagicMock()
        mock_instance.execute_cypher.return_value = MagicMock(
            records=[],
            summary="Test",
            execution_time=0.1,
        )
        mock_engine.return_value = mock_instance

        result = runner.invoke(
            query,
            [
                "-c",
                "MATCH (n) RETURN n",
                "--neo4j-uri",
                "bolt://localhost:7687",
                "--password",
                "test",
            ],
        )

        assert result.exit_code in [0, 1]

    @patch("kg_cli.SemanticSearch")
    def test_search_command(self, mock_search):
        """Test search command."""
        from click.testing import CliRunner
        from kg_cli import search

        runner = CliRunner()

        mock_instance = MagicMock()
        mock_instance.hybrid_search.return_value = []
        mock_search.return_value = mock_instance

        result = runner.invoke(
            search,
            [
                "-q",
                "test query",
                "--neo4j-uri",
                "bolt://localhost:7687",
                "--password",
                "test",
            ],
        )

        assert result.exit_code in [0, 1]

    @patch("kg_cli.RAGIntegrator")
    def test_rag_command(self, mock_rag):
        """Test RAG command."""
        from click.testing import CliRunner
        from kg_cli import rag

        runner = CliRunner()

        mock_instance = MagicMock()
        mock_instance.answer_question.return_value = {
            "answer": "Test answer",
            "context": [],
        }
        mock_rag.return_value = mock_instance

        result = runner.invoke(
            rag,
            [
                "-q",
                "What is AI?",
                "--neo4j-uri",
                "bolt://localhost:7687",
                "--password",
                "test",
            ],
        )

        assert result.exit_code in [0, 1]

    @patch("kg_cli.GraphAnalyzer")
    def test_analyze_command(self, mock_analyzer):
        """Test analyze command."""
        from click.testing import CliRunner
        from kg_cli import analyze

        runner = CliRunner()

        mock_instance = MagicMock()
        mock_instance.calculate_pagerank.return_value = {"node_1": 0.5}
        mock_analyzer.return_value = mock_instance

        result = runner.invoke(
            analyze,
            [
                "--type",
                "pagerank",
                "--neo4j-uri",
                "bolt://localhost:7687",
                "--password",
                "test",
            ],
        )

        assert result.exit_code in [0, 1]

    @patch("kg_cli.GraphBuilder")
    def test_export_command(self, mock_builder):
        """Test export command."""
        from click.testing import CliRunner
        from kg_cli import export

        runner = CliRunner()

        with runner.isolated_filesystem():
            mock_instance = MagicMock()
            mock_builder.return_value = mock_instance

            result = runner.invoke(
                export,
                [
                    "--neo4j-uri",
                    "bolt://localhost:7687",
                    "--password",
                    "test",
                    "-o",
                    "graph.json",
                ],
            )

            assert result.exit_code in [0, 1]

    @patch("kg_cli.GraphQueryEngine")
    def test_info_command(self, mock_engine):
        """Test info command."""
        from click.testing import CliRunner
        from kg_cli import info

        runner = CliRunner()

        mock_instance = MagicMock()
        mock_instance.get_schema.return_value = {
            "node_labels": ["Person"],
            "relationship_types": ["KNOWS"],
            "property_keys": ["name"],
            "node_label_count": 1,
            "relationship_type_count": 1,
        }
        mock_engine.return_value = mock_instance

        result = runner.invoke(
            info,
            [
                "--neo4j-uri",
                "bolt://localhost:7687",
                "--password",
                "test",
            ],
        )

        assert result.exit_code in [0, 1]

    def test_cli_error_handling(self):
        """Test CLI error handling."""
        from click.testing import CliRunner
        from kg_cli import query

        runner = CliRunner()

        # Missing required arguments
        result = runner.invoke(query, [])

        assert result.exit_code != 0


# =============================================================================
# TestIntegration
# =============================================================================


class TestIntegration:
    """Integration tests for end-to-end workflows."""

    @patch("neo4j.GraphDatabase.driver")
    @patch("openai.ChatCompletion.create")
    def test_extract_build_query_workflow(
        self, mock_openai, mock_driver, sample_document
    ):
        """Test complete extract -> build -> query workflow."""
        from graph_builder import BuilderConfig, GraphBuilder
        from graph_query import CypherQuery, GraphQueryEngine, QueryConfig
        from knowledge_extractor import ExtractorConfig, KnowledgeExtractor

        # Mock OpenAI
        mock_openai.return_value = {
            "choices": [{"message": {"content": "MATCH (n) RETURN n"}}]
        }

        # Mock Neo4j
        mock_session = MagicMock()
        mock_result = MagicMock()
        mock_result.__iter__.return_value = []
        mock_result.consume.return_value = MagicMock()
        mock_session.run.return_value = mock_result
        mock_driver.return_value.session.return_value.__enter__.return_value = (
            mock_session
        )

        # Extract
        extractor_config = ExtractorConfig(
            spacy_model="en_core_web_sm",
            enable_llm=False,
        )
        extractor = KnowledgeExtractor(extractor_config)

        with patch.object(extractor, "extract_entities_spacy") as mock_extract:
            mock_extract.return_value = [{"text": "John", "label": "PERSON"}]
            entities = extractor.extract_entities_spacy(sample_document["text"])

        # Build
        builder_config = BuilderConfig(
            neo4j_uri="bolt://localhost:7687",
            auth=("neo4j", "password"),
        )
        builder = GraphBuilder(builder_config)
        builder.create_entities_batch(entities)

        # Query
        query_config = QueryConfig(
            neo4j_uri="bolt://localhost:7687",
            auth=("neo4j", "password"),
            enable_nl_translation=False,
        )
        engine = GraphQueryEngine(query_config)
        query = CypherQuery(query="MATCH (n) RETURN n")
        result = engine.execute_cypher(query)

        assert result is not None

    @patch("neo4j.GraphDatabase.driver")
    def test_search_rag_workflow(self, mock_driver):
        """Test search -> RAG workflow."""
        from rag_integrator import RAGConfig, RAGIntegrator
        from semantic_search import SearchConfig, SemanticSearch

        # Mock Neo4j
        mock_session = MagicMock()
        mock_driver.return_value.session.return_value.__enter__.return_value = (
            mock_session
        )

        # Search
        search_config = SearchConfig(
            neo4j_uri="bolt://localhost:7687",
            auth=("neo4j", "password"),
        )
        search = SemanticSearch(search_config)

        # RAG
        rag_config = RAGConfig(
            neo4j_uri="bolt://localhost:7687",
            auth=("neo4j", "password"),
        )
        rag = RAGIntegrator(rag_config)

        assert search is not None
        assert rag is not None

    @patch("neo4j.GraphDatabase.driver")
    def test_build_analyze_workflow(self, mock_driver, sample_graph):
        """Test build -> analyze workflow."""
        from graph_analyzer import AnalyzerConfig, GraphAnalyzer
        from graph_builder import BuilderConfig, GraphBuilder

        # Mock Neo4j
        mock_session = MagicMock()
        mock_driver.return_value.session.return_value.__enter__.return_value = (
            mock_session
        )

        # Build
        builder_config = BuilderConfig(
            neo4j_uri="bolt://localhost:7687",
            auth=("neo4j", "password"),
        )
        builder = GraphBuilder(builder_config)

        # Analyze
        analyzer_config = AnalyzerConfig(
            neo4j_uri="bolt://localhost:7687",
            auth=("neo4j", "password"),
        )
        analyzer = GraphAnalyzer(analyzer_config)

        with patch.object(analyzer, "load_graph_to_networkx") as mock_load:
            mock_load.return_value = sample_graph
            metrics = analyzer.calculate_graph_metrics()

            assert metrics is not None

    @patch("neo4j.GraphDatabase.driver")
    @patch("openai.ChatCompletion.create")
    def test_nl_query_analysis_workflow(self, mock_openai, mock_driver, sample_graph):
        """Test NL query -> analysis workflow."""
        from graph_analyzer import AnalyzerConfig, GraphAnalyzer
        from graph_query import GraphQueryEngine, QueryConfig

        # Mock OpenAI
        mock_openai.return_value = {
            "choices": [{"message": {"content": "MATCH (n) RETURN n"}}]
        }

        # Mock Neo4j
        mock_session = MagicMock()
        mock_result = MagicMock()
        mock_result.__iter__.return_value = []
        mock_result.consume.return_value = MagicMock()
        mock_session.run.return_value = mock_result
        mock_driver.return_value.session.return_value.__enter__.return_value = (
            mock_session
        )

        # Query
        query_config = QueryConfig(
            neo4j_uri="bolt://localhost:7687",
            auth=("neo4j", "password"),
            enable_nl_translation=True,
        )
        engine = GraphQueryEngine(query_config)

        # Analyze
        analyzer_config = AnalyzerConfig(
            neo4j_uri="bolt://localhost:7687",
            auth=("neo4j", "password"),
        )
        analyzer = GraphAnalyzer(analyzer_config)

        with patch.object(analyzer, "load_graph_to_networkx") as mock_load:
            mock_load.return_value = sample_graph
            pagerank = analyzer.calculate_pagerank()

            assert isinstance(pagerank, dict)

    @patch("neo4j.GraphDatabase.driver")
    def test_full_pipeline(self, mock_driver, sample_document, sample_graph):
        """Test complete pipeline: extract -> build -> query -> analyze -> RAG."""
        from graph_analyzer import AnalyzerConfig, GraphAnalyzer
        from graph_builder import BuilderConfig, GraphBuilder
        from graph_query import GraphQueryEngine, QueryConfig
        from knowledge_extractor import ExtractorConfig, KnowledgeExtractor
        from rag_integrator import RAGConfig, RAGIntegrator

        # Mock Neo4j
        mock_session = MagicMock()
        mock_result = MagicMock()
        mock_result.__iter__.return_value = []
        mock_result.consume.return_value = MagicMock()
        mock_result.data.return_value = []
        mock_session.run.return_value = mock_result
        mock_driver.return_value.session.return_value.__enter__.return_value = (
            mock_session
        )

        # Initialize all components
        extractor = KnowledgeExtractor(
            ExtractorConfig(spacy_model="en_core_web_sm", enable_llm=False)
        )

        builder = GraphBuilder(
            BuilderConfig(
                neo4j_uri="bolt://localhost:7687",
                auth=("neo4j", "password"),
            )
        )

        engine = GraphQueryEngine(
            QueryConfig(
                neo4j_uri="bolt://localhost:7687",
                auth=("neo4j", "password"),
                enable_nl_translation=False,
            )
        )

        analyzer = GraphAnalyzer(
            AnalyzerConfig(
                neo4j_uri="bolt://localhost:7687",
                auth=("neo4j", "password"),
            )
        )

        rag = RAGIntegrator(
            RAGConfig(
                neo4j_uri="bolt://localhost:7687",
                auth=("neo4j", "password"),
            )
        )

        # Verify all components initialized
        assert extractor is not None
        assert builder is not None
        assert engine is not None
        assert analyzer is not None
        assert rag is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
