# P-CONTEXT-VALIDATION: Context Validation and Integrity Protocol

**Version**: 1.0
**Last Updated**: 2025-11-13
**Status**: Active
**Owner**: BackendEngineer

## Objective

Establish context validation and integrity protocol ensuring accurate context extraction, semantic coherence verification, temporal relevance validation, source credibility assessment, context completeness checking, and hallucination detection enabling trustworthy AI responses with verified information accuracy and appropriate context boundaries.

## Tool Requirements

- **TOOL-AI-001** (AI Reasoning): Context validation, semantic coherence verification, and hallucination detection
  - Execute: Context validation, semantic coherence verification, hallucination detection, context reasoning, validation coordination
  - Integration: AI platforms, validation systems, semantic analysis tools, hallucination detection, context validation frameworks
  - Usage: Context validation, semantic verification, hallucination detection, AI-powered validation, context integrity

- **TOOL-KNOWLEDGE-001** (Knowledge Management): Context extraction, source validation, and knowledge integrity management
  - Execute: Context extraction, source validation, knowledge integrity management, context management, source verification
  - Integration: Knowledge management systems, source validation tools, context extraction, integrity frameworks, knowledge platforms
  - Usage: Context extraction, source validation, knowledge integrity, context management, source verification

- **TOOL-DATA-002** (Statistical Analysis): Context quality assessment, relevance scoring, and validation analytics
  - Execute: Context quality assessment, relevance scoring, validation analytics, quality metrics, validation analysis
  - Integration: Analytics platforms, quality assessment tools, relevance scoring systems, validation analytics, quality frameworks
  - Usage: Context quality assessment, relevance scoring, validation analytics, quality measurement, context analysis

- **TOOL-WEB-001** (Web Research): Source credibility assessment, external validation, and fact-checking coordination
  - Execute: Source credibility assessment, external validation, fact-checking coordination, source verification, credibility analysis
  - Integration: Web research tools, credibility assessment platforms, fact-checking systems, source validation, verification tools
  - Usage: Source credibility assessment, external validation, fact-checking, source verification, credibility coordination

## Trigger

- RAG context retrieval requiring validation
- LLM response generation needing context verification
- Context window management requiring relevance filtering
- Multi-source context aggregation requiring coherence check
- Fact-checking requirement for AI-generated content
- Context freshness validation for time-sensitive information

## Agents

**Primary**: BackendEngineer
**Supporting**: QATester, AI-Engineer
**Review**: Technical-Lead
**Orchestration**: Orchestrator (CORE-COORD-002)

## Prerequisites

- Context retrieval system (RAG, knowledge graph)
- Semantic similarity models
- Fact-checking APIs or databases
- Temporal information extractors
- Source credibility scoring system
- Hallucination detection models

## Steps

### Step 1: Context Extraction and Boundary Definition (Estimated Time: 5 minutes)
**Action**: Extract context with clear boundaries and metadata

**Context Structure**:
```python
from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime

@dataclass
class ContextChunk:
    chunk_id: str
    content: str
    source: str
    source_type: str  # document, knowledge_graph, database, api
    timestamp: datetime
    relevance_score: float
    credibility_score: float
    metadata: dict

@dataclass
class ValidatedContext:
    chunks: List[ContextChunk]
    total_tokens: int
    semantic_coherence: float
    temporal_relevance: float
    source_credibility: float
    completeness_score: float
    validation_status: str  # valid, partial, invalid
    warnings: List[str]

class ContextExtractor:
    def extract_context(self, query: str, sources: List[str], max_tokens: int = 2000) -> ValidatedContext:
        """Extract context with boundaries"""
        chunks = []
        total_tokens = 0

        for source in sources:
            chunk = self._extract_chunk(source, query)
            if total_tokens + chunk['tokens'] <= max_tokens:
                chunks.append(ContextChunk(
                    chunk_id=chunk['id'],
                    content=chunk['content'],
                    source=source,
                    source_type=chunk['type'],
                    timestamp=datetime.now(),
                    relevance_score=chunk['relevance'],
                    credibility_score=self._assess_credibility(source),
                    metadata=chunk['metadata']
                ))
                total_tokens += chunk['tokens']

        return ValidatedContext(
            chunks=chunks,
            total_tokens=total_tokens,
            semantic_coherence=0.0,  # To be calculated
            temporal_relevance=0.0,
            source_credibility=0.0,
            completeness_score=0.0,
            validation_status='pending',
            warnings=[]
        )

    def _extract_chunk(self, source: str, query: str) -> dict:
        """Extract relevant chunk from source"""
        return {
            'id': f"chunk_{hash(source)}",
            'content': "Sample context content",
            'tokens': 100,
            'type': 'document',
            'relevance': 0.85,
            'metadata': {}
        }

    def _assess_credibility(self, source: str) -> float:
        """Assess source credibility (0-1)"""
        # Check source reputation, verification status, etc.
        return 0.9
```

**Expected Outcome**: Context extracted with clear boundaries and metadata
**Validation**: Chunks within token limit, sources identified

### Step 2: Semantic Coherence Verification (Estimated Time: 10 minutes)
**Action**: Verify semantic coherence across context chunks

**Coherence Validation**:
```python
from sentence_transformers import SentenceTransformer
import numpy as np

class SemanticCoherenceValidator:
    def __init__(self):
        self.model = SentenceTransformer('all-MiniLM-L6-v2')

    def validate_coherence(self, context: ValidatedContext) -> float:
        """Calculate semantic coherence across chunks"""
        if len(context.chunks) < 2:
            return 1.0  # Single chunk is coherent

        # Generate embeddings for each chunk
        embeddings = self.model.encode([chunk.content for chunk in context.chunks])

        # Calculate pairwise cosine similarities
        similarities = []
        for i in range(len(embeddings) - 1):
            similarity = self._cosine_similarity(embeddings[i], embeddings[i + 1])
            similarities.append(similarity)

        # Average similarity as coherence score
        coherence = np.mean(similarities)

        if coherence < 0.5:
            context.warnings.append(f"Low semantic coherence: {coherence:.2f}")

        return float(coherence)

    def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Calculate cosine similarity"""
        return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))

    def detect_contradictions(self, context: ValidatedContext) -> List[dict]:
        """Detect contradictory information in context"""
        contradictions = []

        # Simple contradiction detection (enhanced version would use NLI models)
        for i, chunk1 in enumerate(context.chunks):
            for j, chunk2 in enumerate(context.chunks[i+1:], start=i+1):
                if self._are_contradictory(chunk1.content, chunk2.content):
                    contradictions.append({
                        'chunk1_id': chunk1.chunk_id,
                        'chunk2_id': chunk2.chunk_id,
                        'severity': 'high'
                    })

        return contradictions

    def _are_contradictory(self, text1: str, text2: str) -> bool:
        """Check if two texts are contradictory"""
        # Placeholder: Use NLI model (e.g., DeBERTa) for actual implementation
        negation_words = ['not', 'never', 'no', 'contrary']
        return any(word in text1.lower() and word in text2.lower() for word in negation_words)
```

**Expected Outcome**: Semantic coherence verified, contradictions detected
**Validation**: Coherence ≥0.7, no critical contradictions

### Step 3: Temporal Relevance Validation (Estimated Time: 10 minutes)
**Action**: Validate temporal relevance of context for query

**Temporal Validation**:
```python
from datetime import datetime, timedelta
import re

class TemporalValidator:
    def validate_temporal_relevance(self, context: ValidatedContext, query: str) -> float:
        """Validate temporal relevance of context"""
        # Extract temporal requirements from query
        query_time_requirement = self._extract_time_requirement(query)

        if not query_time_requirement:
            return 1.0  # No temporal requirement

        # Check each chunk's timestamp
        relevant_chunks = 0
        for chunk in context.chunks:
            if self._is_temporally_relevant(chunk, query_time_requirement):
                relevant_chunks += 1

        relevance = relevant_chunks / len(context.chunks) if context.chunks else 0.0

        if relevance < 0.5:
            context.warnings.append(f"Low temporal relevance: {relevance:.2f}")

        return relevance

    def _extract_time_requirement(self, query: str) -> Optional[dict]:
        """Extract temporal requirements from query"""
        patterns = {
            'recent': r'\b(recent|latest|current|today|this week)\b',
            'specific_year': r'\b(20\d{2})\b',
            'relative': r'\b(last|past)\s+(\d+)\s+(day|week|month|year)s?\b'
        }

        for req_type, pattern in patterns.items():
            if re.search(pattern, query, re.IGNORECASE):
                return {'type': req_type, 'pattern': pattern}

        return None

    def _is_temporally_relevant(self, chunk: ContextChunk, requirement: dict) -> bool:
        """Check if chunk meets temporal requirement"""
        now = datetime.now()

        if requirement['type'] == 'recent':
            # Recent: within last 7 days
            return (now - chunk.timestamp) <= timedelta(days=7)

        elif requirement['type'] == 'specific_year':
            year_match = re.search(r'20\d{2}', requirement['pattern'])
            if year_match:
                target_year = int(year_match.group())
                return chunk.timestamp.year == target_year

        return True
```

**Expected Outcome**: Temporal relevance validated, outdated context flagged
**Validation**: Relevance ≥0.7, warnings for stale data

### Step 4: Source Credibility Assessment (Estimated Time: 10 minutes)
**Action**: Assess credibility of context sources

**Credibility Assessment**:
```python
class SourceCredibilityAssessor:
    def __init__(self):
        self.trusted_sources = {
            'official_docs': 1.0,
            'verified_database': 0.95,
            'knowledge_graph': 0.9,
            'user_generated': 0.6,
            'web_scrape': 0.5
        }

    def assess_credibility(self, context: ValidatedContext) -> float:
        """Assess overall source credibility"""
        if not context.chunks:
            return 0.0

        credibility_scores = []
        for chunk in context.chunks:
            score = self._score_source(chunk)
            chunk.credibility_score = score
            credibility_scores.append(score)

        overall_credibility = np.mean(credibility_scores)

        if overall_credibility < 0.7:
            context.warnings.append(f"Low source credibility: {overall_credibility:.2f}")

        return float(overall_credibility)

    def _score_source(self, chunk: ContextChunk) -> float:
        """Score individual source credibility"""
        base_score = self.trusted_sources.get(chunk.source_type, 0.5)

        # Adjust based on metadata
        if chunk.metadata.get('verified'):
            base_score += 0.1
        if chunk.metadata.get('peer_reviewed'):
            base_score += 0.1
        if chunk.metadata.get('citations', 0) > 5:
            base_score += 0.05

        return min(base_score, 1.0)

    def flag_unreliable_sources(self, context: ValidatedContext) -> List[str]:
        """Flag unreliable sources"""
        unreliable = []
        for chunk in context.chunks:
            if chunk.credibility_score < 0.6:
                unreliable.append(chunk.chunk_id)
        return unreliable
```

**Expected Outcome**: Source credibility assessed, unreliable sources flagged
**Validation**: Average credibility ≥0.7, critical sources verified

### Step 5: Context Completeness Checking (Estimated Time: 10 minutes)
**Action**: Verify context completeness for query requirements

**Completeness Validation**:
```python
class CompletenessValidator:
    def validate_completeness(self, context: ValidatedContext, query: str) -> float:
        """Validate context completeness"""
        # Extract query requirements (entities, topics, relationships)
        requirements = self._extract_requirements(query)

        # Check coverage of requirements
        covered = 0
        for req in requirements:
            if self._is_covered(req, context):
                covered += 1

        completeness = covered / len(requirements) if requirements else 1.0

        if completeness < 0.8:
            missing = [req for req in requirements if not self._is_covered(req, context)]
            context.warnings.append(f"Incomplete context. Missing: {', '.join(missing)}")

        return completeness

    def _extract_requirements(self, query: str) -> List[str]:
        """Extract information requirements from query"""
        # Simple keyword extraction (enhance with NER)
        keywords = query.lower().split()
        requirements = [kw for kw in keywords if len(kw) > 3]
        return requirements

    def _is_covered(self, requirement: str, context: ValidatedContext) -> bool:
        """Check if requirement is covered in context"""
        for chunk in context.chunks:
            if requirement.lower() in chunk.content.lower():
                return True
        return False

    def identify_gaps(self, context: ValidatedContext, query: str) -> List[str]:
        """Identify information gaps"""
        requirements = self._extract_requirements(query)
        gaps = [req for req in requirements if not self._is_covered(req, context)]
        return gaps
```

**Expected Outcome**: Context completeness validated, gaps identified
**Validation**: Completeness ≥0.8, critical information present

### Step 6: Hallucination Detection (Estimated Time: 10 minutes)
**Action**: Detect potential hallucinations or unsupported claims

**Hallucination Detection**:
```python
class HallucinationDetector:
    def detect_hallucinations(self, context: ValidatedContext, generated_response: str) -> dict:
        """Detect potential hallucinations in generated response"""
        claims = self._extract_claims(generated_response)

        hallucinations = []
        for claim in claims:
            if not self._is_supported(claim, context):
                hallucinations.append({
                    'claim': claim,
                    'severity': self._assess_severity(claim),
                    'confidence': 0.8
                })

        return {
            'hallucinations_detected': len(hallucinations),
            'hallucinations': hallucinations,
            'response_reliability': 1.0 - (len(hallucinations) / max(len(claims), 1))
        }

    def _extract_claims(self, text: str) -> List[str]:
        """Extract factual claims from text"""
        # Simple sentence splitting (enhance with claim extraction model)
        sentences = text.split('.')
        return [s.strip() for s in sentences if s.strip()]

    def _is_supported(self, claim: str, context: ValidatedContext) -> bool:
        """Check if claim is supported by context"""
        claim_lower = claim.lower()
        for chunk in context.chunks:
            if any(word in chunk.content.lower() for word in claim_lower.split() if len(word) > 3):
                return True
        return False

    def _assess_severity(self, claim: str) -> str:
        """Assess severity of potential hallucination"""
        critical_keywords = ['critical', 'emergency', 'fatal', 'urgent']
        if any(kw in claim.lower() for kw in critical_keywords):
            return 'high'
        return 'medium'
```

**Expected Outcome**: Hallucinations detected, unsupported claims flagged
**Validation**: Hallucination rate <5%, response reliability ≥0.95

### Step 7: Comprehensive Validation Report (Estimated Time: 5 minutes)
**Action**: Generate comprehensive validation report

**Report Generation**:
```python
class ContextValidator:
    def __init__(self):
        self.coherence_validator = SemanticCoherenceValidator()
        self.temporal_validator = TemporalValidator()
        self.credibility_assessor = SourceCredibilityAssessor()
        self.completeness_validator = CompletenessValidator()
        self.hallucination_detector = HallucinationDetector()

    def validate_full_context(self, context: ValidatedContext, query: str) -> ValidatedContext:
        """Perform comprehensive context validation"""
        # Run all validations
        context.semantic_coherence = self.coherence_validator.validate_coherence(context)
        context.temporal_relevance = self.temporal_validator.validate_temporal_relevance(context, query)
        context.source_credibility = self.credibility_assessor.assess_credibility(context)
        context.completeness_score = self.completeness_validator.validate_completeness(context, query)

        # Determine overall validation status
        scores = [
            context.semantic_coherence,
            context.temporal_relevance,
            context.source_credibility,
            context.completeness_score
        ]

        avg_score = np.mean(scores)

        if avg_score >= 0.8 and all(s >= 0.7 for s in scores):
            context.validation_status = 'valid'
        elif avg_score >= 0.6:
            context.validation_status = 'partial'
        else:
            context.validation_status = 'invalid'

        return context
```

**Expected Outcome**: Comprehensive validation report generated
**Validation**: Overall validation status determined, actionable warnings provided

## Expected Outputs

- **Validated Context**: Context chunks with validation scores
- **Coherence Report**: Semantic coherence score, contradictions detected
- **Temporal Report**: Relevance score, outdated sources flagged
- **Credibility Report**: Source credibility scores, unreliable sources identified
- **Completeness Report**: Coverage score, information gaps listed
- **Hallucination Report**: Unsupported claims detected, severity assessment
- **Success Indicators**: Validation status "valid", all scores ≥0.7, <5% hallucination rate

## Rollback/Recovery

**Trigger**: Invalid context detected, high hallucination risk, low credibility

**P-RECOVERY Integration**:
1. Reject invalid context, request fresh retrieval
2. Filter out low-credibility sources
3. Augment incomplete context with additional sources
4. Flag response generation as high-risk

**Verification**: Validated context meets thresholds
**Data Integrity**: High - Validation ensures quality

## Failure Handling

### Failure Scenario 1: Low Semantic Coherence Across Chunks
- **Symptoms**: Contradictory information, incoherent context
- **Root Cause**: Poor retrieval ranking, multi-topic query ambiguity
- **Impact**: High - AI generates inconsistent responses
- **Resolution**: Re-rank chunks by relevance, filter contradictions
- **Prevention**: Better retrieval algorithms, query disambiguation

### Failure Scenario 2: Outdated Context for Time-Sensitive Query
- **Symptoms**: Stale data provided for current events query
- **Root Cause**: No temporal filtering, old cache entries
- **Impact**: High - Incorrect information, user trust loss
- **Resolution**: Apply temporal filters, refresh cache
- **Prevention**: Timestamp-based retrieval, freshness scoring

### Failure Scenario 3: Low Source Credibility
- **Symptoms**: Unreliable sources dominating context
- **Root Cause**: Insufficient source vetting, equal weighting
- **Impact**: Critical - Misinformation risk, hallucinations
- **Resolution**: Filter low-credibility sources, prefer verified
- **Prevention**: Source credibility scoring, whitelist trusted sources

### Failure Scenario 4: Incomplete Context Missing Critical Information
- **Symptoms**: Key information absent, partial answers
- **Root Cause**: Retrieval scope too narrow, insufficient sources
- **Impact**: High - Incomplete AI responses, user frustration
- **Resolution**: Expand retrieval scope, add sources
- **Prevention**: Completeness checking, gap detection

### Failure Scenario 5: High Hallucination Rate in Generated Response
- **Symptoms**: Claims not supported by context
- **Root Cause**: LLM overconfidence, poor context grounding
- **Impact**: Critical - Misinformation, loss of trust
- **Resolution**: Increase context grounding, use citation mechanism
- **Prevention**: Hallucination detection, response validation

### Failure Scenario 6: Context Validation Overhead Causing Latency
- **Symptoms**: Slow response times due to validation
- **Root Cause**: Complex validation, synchronous processing
- **Impact**: Medium - User experience degraded
- **Resolution**: Parallel validation, caching, async processing
- **Prevention**: Optimize validation, selective depth

## Validation Criteria

### Quantitative Thresholds
- Semantic coherence: ≥0.7
- Temporal relevance: ≥0.7
- Source credibility: ≥0.7
- Completeness score: ≥0.8
- Hallucination rate: <5%
- Validation latency: <500ms

### Boolean Checks
- Context extracted: Pass/Fail
- Coherence validated: Pass/Fail
- Temporal relevance checked: Pass/Fail
- Source credibility assessed: Pass/Fail
- Completeness verified: Pass/Fail
- Hallucinations detected: Pass/Fail

### Qualitative Assessments
- Context quality: User feedback (≥4/5)
- AI response accuracy: QA team (≥4/5)
- Validation effectiveness: Backend team (≥4/5)

**Overall Success**: Thresholds met AND boolean checks pass AND assessments ≥4/5

## HITL Escalation

### Automatic Triggers
- Validation status "invalid"
- Hallucination rate >10%
- Source credibility <0.5

### Manual Triggers
- Context quality disputes
- Validation threshold adjustments
- Hallucination detection tuning

### Escalation Procedure
1. **Level 1**: BackendEngineer context re-retrieval
2. **Level 2**: QATester validation tuning
3. **Level 3**: Technical-Lead strategy review

## Related Protocols

### Upstream
- **P-KNOW-RAG**: Provides context requiring validation
- **P-KNOW-KG-INTERACTION**: Retrieves graph context

### Downstream
- **LLM Response Generation**: Uses validated context
- **Fact-Checking**: Verifies generated responses

### Alternatives
- **No Validation**: Direct context usage vs. validated
- **Post-Generation Validation**: Validate response vs. context

## Test Scenarios

### Happy Path
#### Scenario 1: Valid Context Passing All Checks
- **Setup**: High-quality context from verified sources
- **Execution**: Run P-CONTEXT-VALIDATION
- **Expected Result**: All scores ≥0.8, status "valid", zero warnings
- **Validation**: Context approved for LLM use

### Failure Scenarios
#### Scenario 2: Contradictory Context Detection
- **Setup**: Context chunks with conflicting information
- **Execution**: Coherence validation detects contradiction
- **Expected Result**: Low coherence score, contradiction flagged, warning issued
- **Validation**: Contradictory chunks filtered

### Edge Cases
#### Scenario 3: Time-Sensitive Query with Mixed-Age Context
- **Setup**: "Latest developments" query with 6-month-old context
- **Execution**: Temporal validation flags old sources
- **Expected Result**: Low temporal relevance, stale sources removed
- **Validation**: Only recent context retained

## Metadata

### Version History
| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0 | 2025-10-10 | Initial protocol for Epic 111. Context validation with coherence, temporal, credibility, completeness, hallucination detection, 6 failure scenarios. | BackendEngineer |

### Review Cycle
- **Frequency**: Quarterly
- **Next Review**: 2026-01-10
- **Reviewers**: BackendEngineer lead, QATester lead, AI-Engineer

### Compliance Status
- **Framework Standards**: ✅ Compliant
- **Context Validation**: Required
- **Last Validation**: 2025-10-10

## Performance SLOs

- **Semantic coherence**: ≥0.7
- **Temporal relevance**: ≥0.7
- **Source credibility**: ≥0.7
- **Completeness**: ≥0.8
- **Hallucination rate**: <5%
- **Validation latency**: <500ms
