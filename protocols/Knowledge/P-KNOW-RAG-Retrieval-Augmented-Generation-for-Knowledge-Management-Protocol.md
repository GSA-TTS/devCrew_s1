# P-KNOW-RAG: Retrieval-Augmented Generation for Knowledge Management Protocol

**Version**: 1.0
**Last Updated**: 2025-11-13
**Status**: Active
**Owner**: AI-Engineer

## Objective

Establish Retrieval-Augmented Generation (RAG) protocol enabling intelligent document retrieval, context extraction and ranking, prompt augmentation with retrieved context, response generation with source attribution, answer grounding verification, and continuous learning from user feedback ensuring accurate AI-generated responses grounded in verified knowledge sources.

## Tool Requirements

- **TOOL-AI-001** (AI Reasoning): RAG processing, retrieval coordination, and AI-powered knowledge synthesis
  - Execute: RAG processing, retrieval coordination, AI-powered knowledge synthesis, intelligent retrieval, knowledge generation
  - Integration: AI platforms, RAG frameworks, retrieval systems, knowledge synthesis tools, AI orchestration
  - Usage: RAG coordination, intelligent retrieval, knowledge synthesis, AI-powered processing, retrieval-augmented generation

- **TOOL-KNOWLEDGE-001** (Knowledge Management): Knowledge base management, document retrieval, and knowledge organization
  - Execute: Knowledge base management, document retrieval, knowledge organization, content management, knowledge indexing
  - Integration: Knowledge management systems, document databases, content repositories, knowledge bases, information systems
  - Usage: Knowledge management, document retrieval, content organization, knowledge indexing, information coordination

- **TOOL-WEB-001** (Web Research): External knowledge retrieval, web content extraction, and source validation
  - Execute: External knowledge retrieval, web content extraction, source validation, web research automation, content aggregation
  - Integration: Web research tools, content extraction systems, source validation, web scraping, research automation
  - Usage: External research, content extraction, source validation, web knowledge retrieval, research automation

- **TOOL-DATA-002** (Statistical Analysis): Retrieval relevance scoring, knowledge quality assessment, and RAG analytics
  - Execute: Retrieval relevance scoring, knowledge quality assessment, RAG analytics, relevance analysis, quality metrics
  - Integration: Analytics platforms, relevance scoring systems, quality assessment tools, RAG analytics, performance measurement
  - Usage: Relevance scoring, quality assessment, RAG analytics, performance analysis, knowledge quality validation

## Trigger

- User query requiring knowledge base consultation
- LLM response generation needing factual grounding
- Document search and summarization request
- Question answering over enterprise knowledge
- Chatbot interaction requiring accurate information
- Knowledge synthesis from multiple sources

## Agents

**Primary**: AI-Engineer
**Supporting**: BackendEngineer, QATester
**Review**: Technical-Lead
**Orchestration**: Orchestrator (CORE-COORD-002)

## Prerequisites

- Vector database (Pinecone, Weaviate, Chroma, FAISS)
- Embedding model (OpenAI ada-002, sentence-transformers)
- LLM API access (GPT-4, Claude, Llama)
- Document corpus indexed with embeddings
- Prompt templates for RAG
- Evaluation metrics and feedback system

## Steps

### Step 1: Query Understanding and Expansion (Estimated Time: 2 minutes)
**Action**: Parse user query, expand with synonyms, extract intent

**Query Processing**:
```python
from dataclasses import dataclass
from typing import List, Dict
import openai

@dataclass
class ProcessedQuery:
    original_query: str
    expanded_query: str
    intent: str
    entities: List[str]
    keywords: List[str]
    filters: Dict

class QueryProcessor:
    def process_query(self, user_query: str) -> ProcessedQuery:
        """Process and expand user query"""
        # Extract entities and keywords
        entities = self._extract_entities(user_query)
        keywords = self._extract_keywords(user_query)

        # Expand query with synonyms
        expanded = self._expand_query(user_query, keywords)

        # Classify intent
        intent = self._classify_intent(user_query)

        return ProcessedQuery(
            original_query=user_query,
            expanded_query=expanded,
            intent=intent,
            entities=entities,
            keywords=keywords,
            filters={}
        )

    def _extract_entities(self, query: str) -> List[str]:
        """Extract named entities"""
        # Use NER model
        return []

    def _extract_keywords(self, query: str) -> List[str]:
        """Extract key terms"""
        words = query.lower().split()
        return [w for w in words if len(w) > 4]

    def _expand_query(self, query: str, keywords: List[str]) -> str:
        """Expand query with synonyms"""
        # Simple expansion - enhance with WordNet or LLM
        return query + " " + " ".join(keywords)

    def _classify_intent(self, query: str) -> str:
        """Classify query intent"""
        intents = {
            'factual': ['what', 'when', 'where', 'who'],
            'procedural': ['how', 'steps', 'process'],
            'comparison': ['compare', 'difference', 'versus'],
            'explanation': ['why', 'explain', 'reason']
        }

        query_lower = query.lower()
        for intent, keywords in intents.items():
            if any(kw in query_lower for kw in keywords):
                return intent

        return 'general'
```

**Expected Outcome**: Query processed and expanded for better retrieval
**Validation**: Intent classified, entities extracted, keywords identified

### Step 2: Semantic Document Retrieval (Estimated Time: 5 minutes)
**Action**: Retrieve relevant documents using vector similarity search

**Retrieval Implementation**:
```python
import numpy as np
from typing import List, Tuple

@dataclass
class RetrievedDocument:
    doc_id: str
    content: str
    score: float
    metadata: Dict
    chunk_index: int

class SemanticRetriever:
    def __init__(self, vector_db, embedding_model):
        self.vector_db = vector_db
        self.embedding_model = embedding_model

    def retrieve(self, query: ProcessedQuery, top_k: int = 5) -> List[RetrievedDocument]:
        """Retrieve top-k relevant documents"""
        # Generate query embedding
        query_embedding = self.embedding_model.encode(query.expanded_query)

        # Vector similarity search
        results = self.vector_db.similarity_search(
            query_embedding,
            k=top_k,
            filters=query.filters
        )

        documents = []
        for i, result in enumerate(results):
            documents.append(RetrievedDocument(
                doc_id=result['id'],
                content=result['content'],
                score=result['score'],
                metadata=result['metadata'],
                chunk_index=i
            ))

        return documents

    def hybrid_search(self, query: ProcessedQuery, top_k: int = 5,
                     alpha: float = 0.7) -> List[RetrievedDocument]:
        """Hybrid search combining vector and keyword search"""
        # Vector search
        vector_results = self.retrieve(query, top_k=top_k*2)

        # Keyword search (BM25)
        keyword_results = self._keyword_search(query.keywords, top_k=top_k*2)

        # Combine and rerank (alpha for vector, 1-alpha for keyword)
        combined = self._rerank_hybrid(vector_results, keyword_results, alpha)

        return combined[:top_k]

    def _keyword_search(self, keywords: List[str], top_k: int) -> List[RetrievedDocument]:
        """Keyword-based search using BM25"""
        # Placeholder for BM25 implementation
        return []

    def _rerank_hybrid(self, vector_results: List, keyword_results: List,
                      alpha: float) -> List[RetrievedDocument]:
        """Rerank combining vector and keyword scores"""
        # Combine scores with weighted fusion
        doc_scores = {}

        for doc in vector_results:
            doc_scores[doc.doc_id] = alpha * doc.score

        for doc in keyword_results:
            doc_scores[doc.doc_id] = doc_scores.get(doc.doc_id, 0) + (1-alpha) * doc.score

        # Sort by combined score
        sorted_docs = sorted(doc_scores.items(), key=lambda x: x[1], reverse=True)

        # Return top documents
        doc_map = {doc.doc_id: doc for doc in vector_results + keyword_results}
        return [doc_map[doc_id] for doc_id, score in sorted_docs if doc_id in doc_map]
```

**Expected Outcome**: Top-k relevant documents retrieved with scores
**Validation**: Retrieved docs relevant, diversity maintained, scores normalized

### Step 3: Context Ranking and Selection (Estimated Time: 3 minutes)
**Action**: Rank and select best context chunks for prompt

**Context Ranking**:
```python
class ContextRanker:
    def rank_and_select(self, documents: List[RetrievedDocument],
                       query: ProcessedQuery, max_tokens: int = 2000) -> List[RetrievedDocument]:
        """Rank documents and select within token limit"""
        # Rerank by relevance, diversity, and recency
        ranked = self._rerank_documents(documents, query)

        # Select diverse chunks within token limit
        selected = self._select_diverse_chunks(ranked, max_tokens)

        return selected

    def _rerank_documents(self, documents: List[RetrievedDocument],
                         query: ProcessedQuery) -> List[RetrievedDocument]:
        """Rerank documents considering multiple factors"""
        for doc in documents:
            # Relevance score (base similarity)
            relevance = doc.score

            # Recency boost
            recency = self._calculate_recency_score(doc.metadata.get('timestamp'))

            # Quality score from metadata
            quality = doc.metadata.get('quality_score', 0.8)

            # Combined score
            doc.score = 0.6 * relevance + 0.2 * recency + 0.2 * quality

        return sorted(documents, key=lambda d: d.score, reverse=True)

    def _calculate_recency_score(self, timestamp) -> float:
        """Calculate recency score (1.0 = very recent, 0.5 = old)"""
        if not timestamp:
            return 0.8
        # Implement time decay function
        return 0.8

    def _select_diverse_chunks(self, documents: List[RetrievedDocument],
                              max_tokens: int) -> List[RetrievedDocument]:
        """Select diverse chunks within token budget"""
        selected = []
        total_tokens = 0
        seen_topics = set()

        for doc in documents:
            # Estimate tokens (rough: 4 chars per token)
            doc_tokens = len(doc.content) // 4

            # Check topic diversity (simplified)
            doc_topic = doc.metadata.get('topic', 'general')

            if total_tokens + doc_tokens <= max_tokens:
                if doc_topic not in seen_topics or len(selected) < 3:
                    selected.append(doc)
                    total_tokens += doc_tokens
                    seen_topics.add(doc_topic)

        return selected
```

**Expected Outcome**: Ranked and diverse context chunks selected
**Validation**: Context within token limit, diversity maintained, relevance high

### Step 4: Prompt Augmentation and Generation (Estimated Time: 5 minutes)
**Action**: Construct RAG prompt with retrieved context and generate response

**Prompt Construction**:
```python
class RAGPromptBuilder:
    def build_prompt(self, query: ProcessedQuery, context_docs: List[RetrievedDocument]) -> str:
        """Build RAG prompt with context"""
        # Format context
        context_text = self._format_context(context_docs)

        # Construct prompt with system instructions
        prompt = f"""You are a helpful AI assistant. Use the following context to answer the user's question accurately. If the answer is not in the context, say "I don't have enough information to answer that."

Context:
{context_text}

Question: {query.original_query}

Answer: """

        return prompt

    def _format_context(self, docs: List[RetrievedDocument]) -> str:
        """Format context documents"""
        formatted = []
        for i, doc in enumerate(docs, 1):
            source = doc.metadata.get('source', 'Unknown')
            formatted.append(f"[{i}] Source: {source}\n{doc.content}\n")

        return "\n".join(formatted)

class RAGGenerator:
    def __init__(self, llm_client):
        self.llm = llm_client
        self.prompt_builder = RAGPromptBuilder()

    def generate_response(self, query: ProcessedQuery,
                         context_docs: List[RetrievedDocument]) -> Dict:
        """Generate RAG response"""
        # Build prompt
        prompt = self.prompt_builder.build_prompt(query, context_docs)

        # Generate response
        response = self.llm.generate(
            prompt=prompt,
            max_tokens=500,
            temperature=0.3  # Lower temp for factual responses
        )

        # Extract citations
        citations = self._extract_citations(response, context_docs)

        return {
            'answer': response,
            'sources': [doc.metadata.get('source') for doc in context_docs],
            'citations': citations,
            'confidence': self._estimate_confidence(response, context_docs)
        }

    def _extract_citations(self, response: str, docs: List[RetrievedDocument]) -> List[int]:
        """Extract citation numbers from response"""
        import re
        citations = re.findall(r'\[(\d+)\]', response)
        return [int(c) for c in citations]

    def _estimate_confidence(self, response: str, docs: List[RetrievedDocument]) -> float:
        """Estimate response confidence"""
        # Check for uncertainty phrases
        uncertainty_phrases = ["i don't know", "not sure", "unclear", "may be"]
        if any(phrase in response.lower() for phrase in uncertainty_phrases):
            return 0.5

        # Check citation coverage
        has_citations = '[' in response and ']' in response
        return 0.9 if has_citations else 0.7
```

**Expected Outcome**: Response generated with source attribution
**Validation**: Answer grounded in context, citations present, confidence estimated

### Step 5: Answer Grounding Verification (Estimated Time: 2 minutes)
**Action**: Verify response is grounded in retrieved context

**Grounding Verification**:
```python
class GroundingVerifier:
    def verify_grounding(self, response: str, context_docs: List[RetrievedDocument]) -> Dict:
        """Verify response is grounded in context"""
        # Extract claims from response
        claims = self._extract_claims(response)

        # Check each claim against context
        grounded_claims = 0
        ungrounded_claims = []

        for claim in claims:
            if self._is_grounded(claim, context_docs):
                grounded_claims += 1
            else:
                ungrounded_claims.append(claim)

        grounding_score = grounded_claims / len(claims) if claims else 1.0

        return {
            'grounding_score': grounding_score,
            'total_claims': len(claims),
            'grounded_claims': grounded_claims,
            'ungrounded_claims': ungrounded_claims,
            'status': 'grounded' if grounding_score >= 0.8 else 'partially_grounded'
        }

    def _extract_claims(self, response: str) -> List[str]:
        """Extract factual claims"""
        # Simple sentence splitting
        sentences = response.split('.')
        return [s.strip() for s in sentences if s.strip() and len(s.strip()) > 10]

    def _is_grounded(self, claim: str, docs: List[RetrievedDocument]) -> bool:
        """Check if claim is supported by context"""
        claim_lower = claim.lower()
        for doc in docs:
            # Simple substring matching (enhance with entailment model)
            if any(word in doc.content.lower() for word in claim_lower.split() if len(word) > 4):
                return True
        return False
```

**Expected Outcome**: Grounding score calculated, ungrounded claims identified
**Validation**: Grounding score ≥0.8, critical claims verified

### Step 6: User Feedback Collection and Learning (Estimated Time: Ongoing)
**Action**: Collect user feedback to improve RAG system

**Feedback System**:
```python
@dataclass
class UserFeedback:
    query_id: str
    rating: int  # 1-5
    feedback_text: str
    helpful: bool
    timestamp: str

class RAGFeedbackCollector:
    def collect_feedback(self, query_id: str, response: Dict, rating: int,
                        feedback_text: str = "") -> UserFeedback:
        """Collect user feedback"""
        feedback = UserFeedback(
            query_id=query_id,
            rating=rating,
            feedback_text=feedback_text,
            helpful=rating >= 4,
            timestamp=datetime.now().isoformat()
        )

        # Store feedback for analysis
        self._store_feedback(feedback)

        # Trigger learning if needed
        if not feedback.helpful:
            self._trigger_improvement(query_id, response)

        return feedback

    def _store_feedback(self, feedback: UserFeedback):
        """Store feedback in database"""
        pass

    def _trigger_improvement(self, query_id: str, response: Dict):
        """Trigger system improvement based on negative feedback"""
        # Analyze failure mode
        # Adjust retrieval parameters
        # Retrain ranking model
        pass

    def analyze_feedback_trends(self) -> Dict:
        """Analyze feedback trends for improvement"""
        # Calculate metrics
        return {
            'avg_rating': 4.2,
            'helpful_rate': 0.85,
            'common_issues': ['incomplete_context', 'outdated_info'],
            'improvement_opportunities': []
        }
```

**Expected Outcome**: Feedback collected, system improved iteratively
**Validation**: Feedback stored, low-rated responses analyzed

### Step 7: Performance Monitoring and Optimization (Estimated Time: 10 minutes)
**Action**: Monitor RAG performance and optimize components

**Expected Outcome**: Performance metrics tracked, optimization applied
**Validation**: Latency within target, accuracy improving, user satisfaction high

## Expected Outputs

- **RAG Response**: Generated answer with source citations
- **Retrieved Context**: Top-k relevant documents with scores
- **Grounding Report**: Grounding score, ungrounded claims
- **Source Attribution**: List of sources used for answer
- **Confidence Score**: Estimated answer confidence
- **Performance Metrics**: Retrieval precision, response accuracy, latency
- **Success Indicators**: ≥0.8 grounding score, ≥0.85 user satisfaction, <3s latency

## Rollback/Recovery

**Trigger**: Low grounding score, poor retrieval quality, user dissatisfaction

**P-RECOVERY Integration**:
1. Fall back to direct LLM without RAG if retrieval fails
2. Use cached high-quality responses for common queries
3. Escalate to human support for complex queries
4. Regenerate with adjusted parameters

**Verification**: Alternative response provided, user needs met
**Data Integrity**: Medium - RAG augments but doesn't modify data

## Failure Handling

### Failure Scenario 1: Poor Retrieval Quality
- **Symptoms**: Irrelevant documents retrieved, low relevance scores
- **Root Cause**: Poor embeddings, outdated index, query mismatch
- **Impact**: High - Wrong context, inaccurate answers
- **Resolution**: Reindex documents, improve embeddings, query expansion
- **Prevention**: Regular reindexing, embedding model updates, retrieval evaluation

### Failure Scenario 2: Context Exceeding Token Limit
- **Symptoms**: Prompt truncated, incomplete context
- **Root Cause**: Too many documents retrieved, long documents
- **Impact**: Medium - Information loss, incomplete answers
- **Resolution**: Better chunking, selective summarization, prioritization
- **Prevention**: Token budget management, smart chunk selection

### Failure Scenario 3: Low Grounding Score
- **Symptoms**: LLM generating beyond provided context
- **Root Cause**: Weak prompt instructions, LLM hallucination
- **Impact**: High - Misinformation, hallucinated content
- **Resolution**: Stronger prompts, grounding enforcement, lower temperature
- **Prevention**: Prompt engineering, grounding verification, citation requirements

### Failure Scenario 4: Slow Retrieval Latency
- **Symptoms**: Response time >5 seconds, user frustration
- **Root Cause**: Large vector DB, inefficient indexing, no caching
- **Impact**: High - Poor user experience, abandonment
- **Resolution**: Add caching, optimize indexes, reduce search scope
- **Prevention**: Performance monitoring, caching strategy, index optimization

### Failure Scenario 5: Outdated Information Retrieval
- **Symptoms**: Answers based on stale documents
- **Root Cause**: No document freshness in ranking, old index
- **Impact**: High - Incorrect information, user trust loss
- **Resolution**: Add recency to ranking, refresh index, filter old docs
- **Prevention**: Timestamp-based ranking, regular index updates, freshness filters

### Failure Scenario 6: No Relevant Documents Found
- **Symptoms**: Empty retrieval results, generic LLM response
- **Root Cause**: Corpus gaps, query out of scope, poor embeddings
- **Impact**: Medium - Unable to answer, user disappointment
- **Resolution**: Expand corpus, improve query understanding, fallback messaging
- **Prevention**: Corpus coverage analysis, query analysis, scope definition

## Validation Criteria

### Quantitative Thresholds
- Retrieval precision@5: ≥0.8
- Grounding score: ≥0.8
- User satisfaction: ≥0.85 (helpful rate)
- Response latency: <3 seconds
- Answer accuracy: ≥0.9 (evaluated)
- Citation coverage: ≥80% responses with citations

### Boolean Checks
- Query processed: Pass/Fail
- Documents retrieved: Pass/Fail
- Context ranked: Pass/Fail
- Response generated: Pass/Fail
- Grounding verified: Pass/Fail
- Sources attributed: Pass/Fail

### Qualitative Assessments
- Answer quality: User ratings (≥4/5)
- Context relevance: QA evaluation (≥4/5)
- System usability: User feedback (≥4/5)

**Overall Success**: Thresholds met AND boolean checks pass AND assessments ≥4/5

## HITL Escalation

### Automatic Triggers
- Grounding score <0.5
- User rating ≤2
- No relevant documents found
- Response latency >5 seconds

### Manual Triggers
- RAG strategy optimization
- Corpus expansion decisions
- Embedding model selection

### Escalation Procedure
1. **Level 1**: AI-Engineer retrieval tuning
2. **Level 2**: BackendEngineer infrastructure optimization
3. **Level 3**: Technical-Lead strategy review

## Related Protocols

### Upstream
- **P-KNOW-KG-INTERACTION**: Provides graph context
- **P-CONTEXT-VALIDATION**: Validates retrieved context

### Downstream
- **LLM Response Monitoring**: Tracks response quality
- **User Feedback Analysis**: Analyzes satisfaction

### Alternatives
- **Direct LLM**: No retrieval vs. RAG
- **Traditional Search**: Keyword search vs. semantic

## Test Scenarios

### Happy Path
#### Scenario 1: Factual Question with Perfect Retrieval
- **Setup**: "What is the capital of France?" with relevant docs
- **Execution**: Retrieve Paris doc, generate grounded response
- **Expected Result**: "Paris [1]" with source citation, grounding 1.0
- **Validation**: Correct answer, cited, grounded

### Failure Scenarios
#### Scenario 2: Query with No Relevant Documents
- **Setup**: Query outside corpus scope
- **Execution**: Retrieval returns low-scored irrelevant docs
- **Expected Result**: "I don't have information on that" response
- **Validation**: Honest response, no hallucination

### Edge Cases
#### Scenario 3: Multi-Hop Reasoning Requiring Multiple Sources
- **Setup**: Complex query needing synthesis across 3+ docs
- **Execution**: Retrieve multiple docs, synthesize answer
- **Expected Result**: Comprehensive answer with multiple citations
- **Validation**: All sources cited, coherent synthesis

## Metadata

### Version History
| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0 | 2025-10-10 | Initial protocol for Epic 111. RAG with semantic retrieval, grounding verification, feedback learning, 6 failure scenarios. | AI-Engineer |

### Review Cycle
- **Frequency**: Quarterly
- **Next Review**: 2026-01-10
- **Reviewers**: AI-Engineer lead, BackendEngineer, QATester

### Compliance Status
- **Framework Standards**: ✅ Compliant
- **RAG Knowledge Management**: Required
- **Last Validation**: 2025-10-10

## Performance SLOs

- **Retrieval precision@5**: ≥0.8
- **Grounding score**: ≥0.8
- **User satisfaction**: ≥0.85
- **Response latency**: <3 seconds
- **Answer accuracy**: ≥0.9
- **Citation coverage**: ≥80%
