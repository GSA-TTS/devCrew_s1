"""
Knowledge Extractor for devCrew_s1 Knowledge Graph Management Platform.

This module provides entity extraction, relationship detection, and triple
extraction from unstructured text using spaCy NLP and optional LLM
enhancement.

Part of TOOL-KNOWLEDGE-001 (Issue #54)
"""

import json
import logging
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import spacy
from pydantic import BaseModel, Field, field_validator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EntityType(str, Enum):
    """Entity types supported by the knowledge extractor."""

    PERSON = "PERSON"
    ORGANIZATION = "ORGANIZATION"
    LOCATION = "LOCATION"
    TECHNOLOGY = "TECHNOLOGY"
    CONCEPT = "CONCEPT"
    EVENT = "EVENT"
    DATE = "DATE"
    PRODUCT = "PRODUCT"
    SKILL = "SKILL"
    TOOL = "TOOL"
    LANGUAGE = "LANGUAGE"
    FRAMEWORK = "FRAMEWORK"
    METHOD = "METHOD"
    METRIC = "METRIC"
    OTHER = "OTHER"


class RelationshipType(str, Enum):
    """Relationship types between entities."""

    WORKS_AT = "WORKS_AT"
    LOCATED_IN = "LOCATED_IN"
    USES = "USES"
    CREATED_BY = "CREATED_BY"
    PART_OF = "PART_OF"
    RELATED_TO = "RELATED_TO"
    DEVELOPS = "DEVELOPS"
    MANAGES = "MANAGES"
    COLLABORATES_WITH = "COLLABORATES_WITH"
    DEPENDS_ON = "DEPENDS_ON"
    IMPLEMENTS = "IMPLEMENTS"
    OCCURRED_AT = "OCCURRED_AT"
    OCCURRED_ON = "OCCURRED_ON"
    FOUNDED = "FOUNDED"
    ACQUIRED = "ACQUIRED"
    BASED_IN = "BASED_IN"
    SPECIALIZES_IN = "SPECIALIZES_IN"
    OWNS = "OWNS"


class ExtractionConfig(BaseModel):
    """Configuration for knowledge extraction."""

    model: str = Field(
        default="en_core_web_lg",
        description="spaCy model name to use for extraction",
    )
    use_llm: bool = Field(
        default=False, description="Enable LLM-based entity extraction"
    )
    llm_provider: Optional[str] = Field(
        default=None, description="LLM provider (openai, anthropic)"
    )
    confidence_threshold: float = Field(
        default=0.7, ge=0.0, le=1.0, description="Minimum confidence threshold"
    )
    max_entities: int = Field(
        default=1000, gt=0, description="Maximum entities to extract"
    )
    enable_coreference: bool = Field(
        default=True, description="Enable coreference resolution"
    )
    extract_triples: bool = Field(
        default=True, description="Extract subject-predicate-object triples"
    )

    @field_validator("llm_provider")
    @classmethod
    def validate_llm_provider(cls, v: Optional[str], info) -> Optional[str]:
        """Validate LLM provider if use_llm is enabled."""
        if info.data.get("use_llm") and v is None:
            raise ValueError("llm_provider must be specified when use_llm is True")
        if v and v not in ["openai", "anthropic"]:
            raise ValueError("llm_provider must be 'openai' or 'anthropic'")
        return v


class Entity(BaseModel):
    """Extracted entity with metadata."""

    text: str = Field(..., description="Entity text")
    entity_type: EntityType = Field(..., description="Type of entity")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    start_pos: int = Field(..., ge=0, description="Start position in text")
    end_pos: int = Field(..., gt=0, description="End position in text")
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )

    @field_validator("end_pos")
    @classmethod
    def validate_positions(cls, v: int, info) -> int:
        """Ensure end_pos > start_pos."""
        if "start_pos" in info.data and v <= info.data["start_pos"]:
            raise ValueError("end_pos must be greater than start_pos")
        return v

    def __hash__(self) -> int:
        """Make Entity hashable for set operations."""
        return hash((self.text, self.entity_type, self.start_pos, self.end_pos))

    def __eq__(self, other: object) -> bool:
        """Entity equality based on text, type, and position."""
        if not isinstance(other, Entity):
            return False
        return (
            self.text == other.text
            and self.entity_type == other.entity_type
            and self.start_pos == other.start_pos
            and self.end_pos == other.end_pos
        )


class Relationship(BaseModel):
    """Relationship between two entities."""

    source: Entity = Field(..., description="Source entity")
    target: Entity = Field(..., description="Target entity")
    rel_type: RelationshipType = Field(..., description="Relationship type")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    context: str = Field(default="", description="Context sentence")
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )

    def __hash__(self) -> int:
        """Make Relationship hashable."""
        return hash((self.source, self.target, self.rel_type, self.context))


class Triple(BaseModel):
    """Subject-Predicate-Object triple."""

    subject: str = Field(..., description="Subject of the triple")
    predicate: str = Field(..., description="Predicate/relation")
    object: str = Field(..., description="Object of the triple")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )


class ExtractionError(Exception):
    """Base exception for extraction errors."""

    pass


class ModelNotFoundError(ExtractionError):
    """Exception raised when spaCy model is not found."""

    pass


class KnowledgeExtractor:
    """
    Extract entities, relationships, and triples from unstructured text.

    This class uses spaCy for NLP tasks and optionally integrates with LLMs
    for enhanced extraction capabilities.
    """

    def __init__(self, config: ExtractionConfig):
        """
        Initialize the knowledge extractor.

        Args:
            config: Configuration for extraction

        Raises:
            ModelNotFoundError: If spaCy model is not found
        """
        self.config = config
        self.logger = logging.getLogger(__name__)

        try:
            self.nlp = spacy.load(config.model)
            self.logger.info(f"Loaded spaCy model: {config.model}")
        except OSError as e:
            error_msg = (
                f"spaCy model '{config.model}' not found. "
                f"Install with: python -m spacy download {config.model}"
            )
            self.logger.error(error_msg)
            raise ModelNotFoundError(error_msg) from e

        # Technology-related keywords for classification
        self.tech_keywords = {
            "python",
            "java",
            "javascript",
            "typescript",
            "rust",
            "go",
            "c++",
            "docker",
            "kubernetes",
            "aws",
            "azure",
            "gcp",
            "tensorflow",
            "pytorch",
            "react",
            "vue",
            "angular",
            "api",
            "database",
            "sql",
            "nosql",
            "microservices",
            "ml",
            "ai",
            "llm",
        }

        # Dependency patterns for relationship extraction
        self.dep_patterns = {
            RelationshipType.WORKS_AT: ["work", "works", "employed", "employee"],
            RelationshipType.USES: ["use", "uses", "using", "utilized"],
            RelationshipType.DEVELOPS: ["develop", "develops", "developed", "building"],
            RelationshipType.MANAGES: ["manage", "manages", "managed", "oversees"],
            RelationshipType.CREATED_BY: ["created", "founded", "established"],
        }

    def extract_entities(self, text: str) -> List[Entity]:
        """
        Extract named entities from text using spaCy NER.

        Args:
            text: Input text to process

        Returns:
            List of extracted entities

        Raises:
            ExtractionError: If extraction fails
        """
        try:
            if not text or not text.strip():
                self.logger.warning("Empty text provided for entity extraction")
                return []

            # Preprocess text
            if self.config.enable_coreference:
                text = self._resolve_coreferences(text)

            doc = self.nlp(text)
            entities = []

            for ent in doc.ents:
                entity_type = self._map_spacy_label_to_entity_type(ent.label_)

                # Calculate confidence (spaCy doesn't provide direct confidence)
                confidence = self._calculate_entity_confidence(ent)

                if confidence >= self.config.confidence_threshold:
                    entity = Entity(
                        text=ent.text,
                        entity_type=entity_type,
                        confidence=confidence,
                        start_pos=ent.start_char,
                        end_pos=ent.end_char,
                        metadata={
                            "label": ent.label_,
                            "lemma": ent.lemma_,
                            "sentence": ent.sent.text if ent.sent else "",
                        },
                    )
                    entities.append(entity)

                if len(entities) >= self.config.max_entities:
                    self.logger.warning(
                        f"Reached max_entities limit ({self.config.max_entities})"
                    )
                    break

            # Optional LLM enhancement
            if self.config.use_llm and self.config.llm_provider:
                llm_entities = self._llm_extract_entities(text)
                entities = self._merge_entities(entities, llm_entities)

            self.logger.info(f"Extracted {len(entities)} entities from text")
            return entities

        except Exception as e:
            self.logger.error(f"Entity extraction failed: {str(e)}")
            raise ExtractionError(f"Failed to extract entities: {str(e)}") from e

    def extract_relationships(
        self, text: str, entities: List[Entity]
    ) -> List[Relationship]:
        """
        Extract relationships between entities using dependency parsing.

        Args:
            text: Input text
            entities: List of extracted entities

        Returns:
            List of relationships between entities

        Raises:
            ExtractionError: If relationship extraction fails
        """
        try:
            if not entities:
                self.logger.debug("No entities provided for relationship extraction")
                return []

            doc = self.nlp(text)
            relationships = []

            # Create entity lookup by position
            entity_map = {(e.start_pos, e.end_pos): e for e in entities}

            # Extract relationships using dependency parsing
            for sent in doc.sents:
                sent_rels = self._extract_relationships_from_sentence(sent, entity_map)
                relationships.extend(sent_rels)

            # Deduplicate relationships
            relationships = list(set(relationships))

            self.logger.info(
                f"Extracted {len(relationships)} relationships from {len(entities)} entities"  # noqa: E501
            )
            return relationships

        except Exception as e:
            self.logger.error(f"Relationship extraction failed: {str(e)}")
            raise ExtractionError(f"Failed to extract relationships: {str(e)}") from e

    def extract_triples(self, text: str) -> List[Triple]:
        """
        Extract subject-predicate-object triples from text.

        Args:
            text: Input text

        Returns:
            List of extracted triples

        Raises:
            ExtractionError: If triple extraction fails
        """
        try:
            doc = self.nlp(text)
            triples = []

            for sent in doc.sents:
                sent_triples = self._extract_triples_from_sentence(sent)
                triples.extend(sent_triples)

            self.logger.info(f"Extracted {len(triples)} triples from text")
            return triples

        except Exception as e:
            self.logger.error(f"Triple extraction failed: {str(e)}")
            raise ExtractionError(f"Failed to extract triples: {str(e)}") from e

    def extract_from_document(
        self, doc_path: str
    ) -> Tuple[List[Entity], List[Relationship]]:
        """
        Extract entities and relationships from a document file.

        Supports: .txt, .md, .pdf

        Args:
            doc_path: Path to document file

        Returns:
            Tuple of (entities, relationships)

        Raises:
            ExtractionError: If document processing fails
        """
        try:
            path = Path(doc_path)
            if not path.exists():
                raise FileNotFoundError(f"Document not found: {doc_path}")

            self.logger.info(f"Processing document: {doc_path}")

            # Read document content
            text = self._read_document(path)

            # Extract entities and relationships
            entities = self.extract_entities(text)
            relationships = self.extract_relationships(text, entities)

            self.logger.info(
                f"Extracted {len(entities)} entities and {len(relationships)} "
                f"relationships from {doc_path}"
            )

            return entities, relationships

        except Exception as e:
            self.logger.error(f"Document extraction failed: {str(e)}")
            raise ExtractionError(f"Failed to extract from document: {str(e)}") from e

    def get_entity_statistics(self, entities: List[Entity]) -> Dict[str, Any]:
        """
        Calculate statistics about extracted entities.

        Args:
            entities: List of entities

        Returns:
            Dictionary containing statistics
        """
        if not entities:
            return {
                "total_count": 0,
                "by_type": {},
                "avg_confidence": 0.0,
                "confidence_range": (0.0, 0.0),
            }

        # Count by type
        type_counts = {}
        for entity in entities:
            type_name = entity.entity_type.value
            type_counts[type_name] = type_counts.get(type_name, 0) + 1

        # Calculate confidence statistics
        confidences = [e.confidence for e in entities]
        avg_confidence = sum(confidences) / len(confidences)
        min_confidence = min(confidences)
        max_confidence = max(confidences)

        return {
            "total_count": len(entities),
            "by_type": type_counts,
            "avg_confidence": round(avg_confidence, 3),
            "confidence_range": (round(min_confidence, 3), round(max_confidence, 3)),
            "unique_texts": len(set(e.text for e in entities)),
        }

    def _map_spacy_label_to_entity_type(self, label: str) -> EntityType:
        """
        Map spaCy NER labels to EntityType enum.

        Args:
            label: spaCy entity label

        Returns:
            Mapped EntityType
        """
        mapping = {
            "PERSON": EntityType.PERSON,
            "ORG": EntityType.ORGANIZATION,
            "GPE": EntityType.LOCATION,
            "LOC": EntityType.LOCATION,
            "DATE": EntityType.DATE,
            "TIME": EntityType.DATE,
            "EVENT": EntityType.EVENT,
            "PRODUCT": EntityType.PRODUCT,
            "WORK_OF_ART": EntityType.PRODUCT,
            "LANGUAGE": EntityType.LANGUAGE,
            "NORP": EntityType.ORGANIZATION,
            "FAC": EntityType.LOCATION,
        }

        return mapping.get(label, EntityType.OTHER)

    def _calculate_entity_confidence(self, ent) -> float:
        """
        Calculate confidence score for an entity.

        spaCy doesn't provide confidence directly, so we use heuristics:
        - Entity length
        - POS tags consistency
        - Named entity recognizer internal scores if available

        Args:
            ent: spaCy entity

        Returns:
            Confidence score between 0 and 1
        """
        base_confidence = 0.8

        # Adjust based on entity length
        if len(ent.text) < 2:
            base_confidence -= 0.2
        elif len(ent.text) > 20:
            base_confidence -= 0.1

        # Check if entity is all uppercase (likely acronym)
        if ent.text.isupper() and len(ent.text) > 1:
            base_confidence += 0.1

        # Check for technology keywords
        if any(keyword in ent.text.lower() for keyword in self.tech_keywords):
            base_confidence += 0.05

        return min(max(base_confidence, 0.0), 1.0)

    def _resolve_coreferences(self, text: str) -> str:
        """
        Basic coreference resolution (he/she/it -> actual names).

        This is a simplified implementation. For production, consider
        using neuralcoref or coreferee libraries.

        Args:
            text: Input text

        Returns:
            Text with resolved coreferences
        """
        # Basic pronoun patterns
        doc = self.nlp(text)

        # Simple heuristic: replace pronouns with nearest preceding named entity
        resolved_text = text
        last_person = None

        for token in doc:
            if token.pos_ == "PROPN" and token.ent_type_ == "PERSON":
                last_person = token.text
            elif token.text.lower() in ["he", "she", "they"] and last_person:
                resolved_text = resolved_text.replace(token.text, last_person, 1)

        return resolved_text

    def _llm_extract_entities(self, text: str) -> List[Entity]:
        """
        Use LLM to extract entities (OpenAI or Anthropic).

        This is a placeholder for LLM integration. In production, you would:
        1. Format prompt with entity types
        2. Call LLM API
        3. Parse JSON response
        4. Create Entity objects

        Args:
            text: Input text

        Returns:
            List of entities extracted by LLM
        """
        self.logger.info(
            f"LLM extraction not implemented for provider: {self.config.llm_provider}"
        )
        # Placeholder - implement actual LLM calls as needed
        return []

    def _merge_entities(
        self, spacy_entities: List[Entity], llm_entities: List[Entity]
    ) -> List[Entity]:
        """
        Merge entities from spaCy and LLM, removing duplicates.

        Args:
            spacy_entities: Entities from spaCy
            llm_entities: Entities from LLM

        Returns:
            Merged list of entities
        """
        # Use set to remove exact duplicates
        all_entities = set(spacy_entities + llm_entities)

        # Remove overlapping entities (keep higher confidence)
        merged = []
        sorted_entities = sorted(all_entities, key=lambda e: e.confidence, reverse=True)

        for entity in sorted_entities:
            overlaps = False
            for existing in merged:
                if self._entities_overlap(entity, existing):
                    overlaps = True
                    break
            if not overlaps:
                merged.append(entity)

        return merged

    def _entities_overlap(self, e1: Entity, e2: Entity) -> bool:
        """Check if two entities overlap in text position."""
        return not (e1.end_pos <= e2.start_pos or e2.end_pos <= e1.start_pos)

    def _extract_relationships_from_sentence(
        self, sent, entity_map: Dict[Tuple[int, int], Entity]
    ) -> List[Relationship]:
        """
        Extract relationships from a single sentence.

        Args:
            sent: spaCy sentence
            entity_map: Mapping of position to entities

        Returns:
            List of relationships found in sentence
        """
        relationships = []

        # Find entities in this sentence
        sent_entities = []
        for (start, end), entity in entity_map.items():
            if sent.start_char <= start < sent.end_char:
                sent_entities.append(entity)

        if len(sent_entities) < 2:
            return relationships

        # Extract relationships using dependency parsing
        for token in sent:
            if token.pos_ == "VERB":
                # Find subject and object
                subjects = [
                    child
                    for child in token.children
                    if child.dep_ in ["nsubj", "nsubjpass"]
                ]
                objects = [
                    child
                    for child in token.children
                    if child.dep_ in ["dobj", "pobj", "attr"]
                ]

                for subj in subjects:
                    for obj in objects:
                        # Find matching entities
                        subj_entity = self._find_entity_at_position(subj, entity_map)
                        obj_entity = self._find_entity_at_position(obj, entity_map)

                        if subj_entity and obj_entity:
                            rel_type = self._infer_relationship_type(
                                token.lemma_, subj_entity, obj_entity
                            )
                            relationship = Relationship(
                                source=subj_entity,
                                target=obj_entity,
                                rel_type=rel_type,
                                confidence=0.75,
                                context=sent.text,
                                metadata={
                                    "verb": token.text,
                                    "verb_lemma": token.lemma_,
                                },
                            )
                            relationships.append(relationship)

        return relationships

    def _find_entity_at_position(self, token, entity_map):
        """Find entity that contains the given token."""
        for (start, end), entity in entity_map.items():
            if start <= token.idx < end:
                return entity
        return None

    def _infer_relationship_type(
        self, verb_lemma: str, source: Entity, target: Entity
    ) -> RelationshipType:
        """
        Infer relationship type from verb and entity types.

        Args:
            verb_lemma: Lemmatized verb
            source: Source entity
            target: Target entity

        Returns:
            Inferred RelationshipType
        """
        # Check verb patterns
        for rel_type, verbs in self.dep_patterns.items():
            if verb_lemma in verbs:
                return rel_type

        # Infer from entity types
        if (
            source.entity_type == EntityType.PERSON
            and target.entity_type == EntityType.ORGANIZATION
        ):
            return RelationshipType.WORKS_AT

        if target.entity_type == EntityType.LOCATION:
            return RelationshipType.LOCATED_IN

        if target.entity_type in [
            EntityType.TECHNOLOGY,
            EntityType.TOOL,
            EntityType.FRAMEWORK,
        ]:
            return RelationshipType.USES

        return RelationshipType.RELATED_TO

    def _extract_triples_from_sentence(self, sent) -> List[Triple]:
        """
        Extract subject-predicate-object triples from sentence.

        Args:
            sent: spaCy sentence

        Returns:
            List of triples
        """
        triples = []

        for token in sent:
            if token.pos_ == "VERB":
                # Find subject
                subjects = [
                    child
                    for child in token.children
                    if child.dep_ in ["nsubj", "nsubjpass"]
                ]

                # Find object
                objects = [
                    child
                    for child in token.children
                    if child.dep_ in ["dobj", "pobj", "attr"]
                ]

                for subj in subjects:
                    for obj in objects:
                        # Get full noun phrases if available
                        subj_text = self._get_noun_phrase(subj)
                        obj_text = self._get_noun_phrase(obj)

                        triple = Triple(
                            subject=subj_text,
                            predicate=token.lemma_,
                            object=obj_text,
                            confidence=0.7,
                            metadata={
                                "sentence": sent.text,
                                "verb_text": token.text,
                            },
                        )
                        triples.append(triple)

        return triples

    def _get_noun_phrase(self, token) -> str:
        """
        Get the full noun phrase containing the token.

        Args:
            token: spaCy token

        Returns:
            Full noun phrase text
        """
        # Get subtree (all children)
        subtree = list(token.subtree)
        return " ".join([t.text for t in subtree])

    def _read_document(self, path: Path) -> str:
        """
        Read document content from file.

        Args:
            path: Path to document

        Returns:
            Document text content

        Raises:
            ExtractionError: If file format is unsupported or reading fails
        """
        suffix = path.suffix.lower()

        try:
            if suffix in [".txt", ".md"]:
                with open(path, "r", encoding="utf-8") as f:
                    return f.read()

            elif suffix == ".pdf":
                try:
                    import PyPDF2

                    text = []
                    with open(path, "rb") as f:
                        reader = PyPDF2.PdfReader(f)
                        for page in reader.pages:
                            text.append(page.extract_text())
                    return "\n".join(text)
                except ImportError:
                    raise ExtractionError(
                        "PyPDF2 not installed. Install with: pip install PyPDF2"
                    )

            else:
                raise ExtractionError(
                    f"Unsupported file format: {suffix}. " f"Supported: .txt, .md, .pdf"
                )

        except Exception as e:
            raise ExtractionError(f"Failed to read document: {str(e)}") from e


def main():
    """Example usage of KnowledgeExtractor."""
    # Configure extractor
    config = ExtractionConfig(
        model="en_core_web_lg",
        confidence_threshold=0.7,
        max_entities=100,
    )

    # Initialize extractor
    try:
        extractor = KnowledgeExtractor(config)
    except ModelNotFoundError as e:
        logger.error(str(e))
        return

    # Sample text
    sample_text = """
    John Smith works at Google in Mountain View, California.
    He develops machine learning models using Python and TensorFlow.
    The team is building an AI system for natural language processing.
    Google was founded in 1998 by Larry Page and Sergey Brin.
    """

    # Extract entities
    entities = extractor.extract_entities(sample_text)
    logger.info(f"Found {len(entities)} entities:")
    for entity in entities:
        logger.info(
            f"  {entity.text} ({entity.entity_type.value}) - "
            f"confidence: {entity.confidence:.2f}"
        )

    # Extract relationships
    relationships = extractor.extract_relationships(sample_text, entities)
    logger.info(f"\nFound {len(relationships)} relationships:")
    for rel in relationships:
        logger.info(
            f"  {rel.source.text} --[{rel.rel_type.value}]--> {rel.target.text}"
        )

    # Extract triples
    triples = extractor.extract_triples(sample_text)
    logger.info(f"\nFound {len(triples)} triples:")
    for triple in triples:
        logger.info(f"  ({triple.subject}, {triple.predicate}, {triple.object})")

    # Get statistics
    stats = extractor.get_entity_statistics(entities)
    logger.info(f"\nEntity Statistics: {json.dumps(stats, indent=2)}")


if __name__ == "__main__":
    main()
