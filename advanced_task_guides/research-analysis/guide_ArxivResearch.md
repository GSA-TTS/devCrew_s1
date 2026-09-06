# Research Workflow for Survey Deep-Dives Using ArXiv

## Executive Overview

This guide provides a structured, expansive methodology for converting topic surveys (like the "Enforcing Appropriately Secure Authentication Methods For Non-User Accounts And Services" example) into targeted ArXiv research queries and distilling findings into actionable insights. The workflow comprises three integrated phases: **(1) Extracting Important Details from Surveys, (2) Formulating Effective ArXiv Search Strings, and (3) Distilling Paper Contents into Usable Results**.

---

## Phase 1: Identifying Important Details from a Survey

### 1.1 Survey Structure Analysis

Begin by understanding how your survey is organized. Most policy/security/technology surveys follow this pattern:

**Key Structural Elements:**
- **Scope section**: Defines core concepts and terminology
- **Impact assessment**: How external forces (AI, regulations, technology adoption) reshape the domain
- **Threat/risk landscape**: Emerging vulnerabilities and attack vectors
- **Provider/stakeholder implications**: Architectural, operational, and market-level impacts
- **Practical recommendations**: Patterns, best practices, and implementation guidance

For your example survey, the structure maps to:
1. Non-human identities (NHI) definitions and types
2. AI agents reshaping NHI authentication
3. Emerging threats at AI-NHI intersection
4. CSP impacts and architectural evolution
5. Practical implementation patterns

### 1.2 Hierarchical Topic Extraction

Extract topics at multiple levels of abstraction:

**Level 1 - Primary Topics** (directly stated, survey title-level)
- Non-human identities (service accounts, API keys, machine identities, workload identities, AI agents)
- Secure authentication methods (OIDC, mTLS, certificate-based auth, JIT provisioning)
- Credential lifecycle management (rotation, provisioning, deprovisioning)

**Level 2 - Secondary Topics** (explicit sections, subtopic areas)
- Workload identity federation
- Static credential exposure and lateral movement
- Behavioral verification for AI agents
- Delegation chains and scope boundaries
- Anomaly detection for non-human identities
- Service-to-service authentication

**Level 3 - Tertiary/Granular Topics** (implications, emerging areas, gaps)
- Behavioral baseline poisoning attacks
- Delegation scope expansion
- Cross-environment contamination
- Zombie account lifecycle
- Model drift in anomaly detection
- Zero-standing-privilege architectures
- Dynamic authorization with ABAC

**Extraction Method:**
1. Read the survey abstract and key takeaway for top-level problem statement
2. Scan each section heading for Level 1 topics
3. Read subsection headings and opening paragraphs for Level 2 topics
4. Note specific threats, challenges, and technical details for Level 3 topics
5. Identify cross-cutting themes (e.g., "automation," "visibility," "governance")

### 1.3 Identifying Critical Details and Research Dimensions

For each topic extracted, identify what aspects need research validation:

**Dimension Framework:**

| Topic | Why It Matters | Research Angles | Key Uncertainties |
|-------|----------------|-----------------|-------------------|
| Workload Identity Federation (WIF) | Replaces long-lived API keys with short-lived tokens; reduces lateral movement window from months to minutes | Technical implementation, adoption barriers, provider support, cost-benefit analysis | How many organizations use WIF? What are measured security improvements? Barriers to adoption? |
| AI Agent Authentication | AI agents have non-human behavior, dynamic permissions needs, delegation chains; existing models don't fit | Agent threat modeling, behavioral baselines, dynamic authorization frameworks | What anomaly detection models work for AI agent behavior? How do we prevent baseline poisoning? |
| Lateral Movement via Compromised Service Accounts | Service account compromise enables cross-project, cross-environment privilege escalation; hard to detect with long-lived credentials | Attack paths, detection methods, dwell time analysis, containment strategies | Measured impact of WIF on dwell time? Real-world lateral movement chains? |
| Behavioral Anomaly Detection | Static ML baselines learn expected behavior; deviations trigger escalation; but model drift and attacker adaptation are risks | Baseline construction, drift mitigation, false positive reduction, real-time detection | Which baseline models work best for different identity types? How do we handle legitimate behavior change? |

**Extraction Action Items:**
- For each Level 2 topic, note: (a) current state, (b) emerging challenges, (c) future direction, (d) measurable impact
- Flag quantitative claims (e.g., "94% of organizations manage credentials manually," "45:1 machine-to-human ratio") for validation via research
- Identify recommendations that lack empirical support (e.g., "rotate credentials every 14-90 days") as research targets
- Note contradictions or tensions (e.g., "automated deprovisioning breaks production" vs. "manual deprovisioning never happens")

### 1.4 Identifying Context and Relationships

Map how topics relate to each other:

**Dependency Chains:**
- AI agent explosion → credential proliferation → lifecycle automation need → behavioral monitoring → anomaly detection
- Long-lived API keys → static credentials scattered across repos → secrets exposure on GitHub → lateral movement risk → workload identity federation solution

**Risk-Control Pairs:**
- Risk: Lateral movement via service account compromise → Control: Short-lived tokens + zero standing privilege
- Risk: Behavioral baseline poisoning → Control: Drift detection + human-in-the-loop review
- Risk: Over-permissioned service accounts → Control: Least-privilege by design + continuous re-validation

**Use these relationships to cluster your ArXiv searches**: don't search for isolated topics; search for topic clusters that show causal or dependency relationships.

---

## Phase 2: Mutating and Effectively Forming Search Strings for ArXiv

### 2.1 Understanding ArXiv Search Capabilities and Syntax

**ArXiv Categories Relevant to Your Domain:**
- `cs.CR` (Cryptography and Security) — primary category for authentication, identity, threat research
- `cs.SY` (Systems and Control) — workload orchestration, distributed systems, automated control
- `cs.AI` (Artificial Intelligence) — AI agent behavior, anomaly detection, behavioral modeling
- `cs.CL` (Computation and Language) — NLP-based detection/analysis (less directly relevant)

**Search Fields:**
- `ti:` = Title only
- `abs:` = Abstract only
- `ti: AND abs:` = Title and abstract combined
- `au:` = Author
- `cat:` = Category (e.g., `cat:cs.CR`)
- `submittedDate:` = Date range (format: `[YYYYMMDDHHMM TO YYYYMMDDHHMM]`)
- `all:` or default = All fields (title, abstract, categories, author)

**Boolean Operators:**
- `AND` — both terms required (default connector)
- `OR` — either term acceptable
- `ANDNOT` — exclude term
- Parentheses `()` — enforce precedence (mandatory for complex queries with multiple Boolean operators)

**Wildcards and Operators:**
- `*` — zero or more characters at end of term (e.g., `authentica*` matches authentication, authenticator, etc.)
- Phrase search with quotes: `"zero trust"` matches exact phrase
- Note: ArXiv does NOT support wildcards at the beginning of terms or in the middle

**Important Limitations:**
- Punctuation generally not indexed (cannot search for "OAuth2.0"; search for "OAuth" and "2" separately)
- Special characters like parentheses, equals signs not searchable
- Stemming is automatic in most fields (searching "superconductor" also matches "superconducting")

### 2.2 Query Formulation Strategy: From Topics to Search Strings

**Step 1: Start with Core Topic Terms**

For your survey's Level 1 topics, identify synonyms and variant terminology:

| Survey Term | Synonyms & Variants | ArXiv-Friendly Forms |
|-------------|-------------------|---------------------|
| Non-human identities (NHI) | Machine identities, service accounts, workload identities, bot identities, automation identities | `(service account* OR machine identit* OR workload identit* OR non-human identit*)` |
| Workload identity federation | Workload identity, WIF, identity federation, OIDC federation, SAML federation | `(workload identit* OR identity federation OR OIDC OR SAML)` |
| AI agents | Autonomous agents, agentic AI, intelligent agents, software agents | `(AI agent* OR autonomous agent* OR agentic AI OR intelligent agent*)` |
| Static credentials | Long-lived credentials, hardcoded secrets, API keys, hardcoded keys | `(static credential* OR long-lived credential* OR hardcoded secret* OR hardcoded API key*)` |
| Short-lived tokens | Ephemeral tokens, temporary credentials, JWT, OIDC token | `(short-lived token* OR ephemeral token* OR JWT OR temporary credential*)` |

**Step 2: Create Query Clusters by Research Question**

Organize searches around specific research questions derived from your survey:

**Cluster A: Workload Identity Federation Technical Implementation & Adoption**

Searches:
1. `ti:(workload identity OR identity federation) AND (implementation OR architecture OR framework)`
2. `abs:(OIDC OR OpenID Connect) AND (authentication OR credential* OR token*) AND (workload* OR service*)`
3. `abs:(zero trust) AND (authentication OR identit*) AND (credential*)`
4. `ti:(OIDC OR SAML) AND (microservice* OR containeriz* OR Kubernetes)`
5. `abs:(lateral movement) AND (credential* OR identit*) AND (mitigation OR prevent*)`

**Cluster B: AI Agent Authentication & Authorization**

Searches:
1. `abs:(AI agent* OR autonomous agent*) AND (authentication OR authorization OR permission*)`
2. `abs:(agentic AI OR autonomous agent*) AND (security OR risk* OR threat*)`
3. `abs:(behavioral anomaly OR anomaly detection) AND (agent* OR identity OR identit*)`
4. `abs:(delegation OR privilege*) AND (agent* OR automation OR orchestration)`
5. `ti:(AI security) AND (agent* OR automation) AND (cloud OR infrastructure)`

**Cluster C: Service Account Lifecycle & Secrets Management**

Searches:
1. `abs:(service account* OR API key*) AND (lifecycle OR rotation OR management)`
2. `abs:(credential* OR secret*) AND (rotation OR deprovisioning OR lifecycle)`
3. `ti:(secret* OR credential*) AND (rotation OR automation OR management)`
4. `abs:(secret exposure OR credential exposure) AND (GitHub OR repository OR repository*)`
5. `abs:(secrets vault* OR credential manager*) AND (rotation OR automation)`

**Cluster D: Threat Modeling & Attack Surface**

Searches:
1. `abs:(lateral movement) AND (service account* OR machine identit* OR credential*)`
2. `abs:(privilege escalation) AND (container* OR microservice* OR cloud)`
3. `abs:(threat model* OR attack surface) AND (identity OR identit* OR credential*)`
4. `abs:(compromised credential* OR credential compromise) AND (detection OR mitigation)`
5. `ti:(insider threat) AND (automation OR agent* OR bot*)`

**Cluster E: Behavioral Monitoring & Anomaly Detection for Non-Human Identities**

Searches:
1. `abs:(anomaly detection OR behavioral baseline*) AND (machine identit* OR service account*)`
2. `abs:(behavioral monitoring OR behavior-based) AND (authentication OR identit*)`
3. `abs:(machine learning) AND (anomaly detection) AND (cloud security OR access control)`
4. `abs:(model drift) AND (anomaly detection OR machine learning)`
5. `abs:(zero-day OR adversarial) AND (anomaly detection OR behavioral baseline*)`

### 2.3 Query Mutation Strategies for Comprehensive Coverage

Once you have a baseline query, apply these mutation strategies to capture variations:

**Mutation 1: Synonymy Expansion**
- Original: `workload identity`
- Mutations:
  - `service identit*` (more general)
  - `application identit*` (broader context)
  - `workload authentication* OR workload credential*` (related concepts)

**Mutation 2: Abstraction Level Variation**
- Original: `OIDC federation`
- Higher abstraction: `(authentication OR credential*) AND (federation OR standard*)`
- Lower abstraction: `(OpenID Connect OR OAuth) AND (JWT OR token*)`

**Mutation 3: Boolean Restructuring**
- Original: `(workload identit* OR service identit*) AND authentication`
- Variant 1: `workload identit* AND (authentication OR credential*)`
- Variant 2: `(workload OR application) AND (authentication OR identit*)`

**Mutation 4: Negative Queries (Exclusion)**
- Use `ANDNOT` to exclude specific subtopics
- Example: `anomaly detection AND (identit* OR credential*) ANDNOT human` (exclude papers focused on human user detection)

**Mutation 5: Author/Venue Targeting**
- Add author constraints: `au:"specific author" AND (workload identit*)`
- Add date constraints: `submittedDate:[202301010000 TO 202412312359] AND (credential* OR identit*)`

**Mutation 6: Title-Only vs. Full-Text Balance**
- Title-focused (higher precision, lower recall): `ti:(workload identity OR OIDC) AND ti:authentication`
- Full-text (lower precision, higher recall): `abs:(workload identit* OR identity federation) AND (authentication OR authorization)`

### 2.4 Query Formulation Workflow

**Process for Each Research Question:**

1. **Identify core concepts** → List 3-5 key terms from your survey topic
2. **Expand with synonyms** → For each term, generate 2-3 variants
3. **Create base query** → Combine synonyms with OR; separate concept clusters with AND
4. **Add specificity filters** → Narrow with category (`cat:cs.CR`), date range, or keywords
5. **Generate mutations** → Create 3-5 variations (exclusions, different Boolean arrangements, abstraction levels)
6. **Test and refine** → Run queries, assess relevance; if too many results (>200), add specificity; if too few (<10), broaden
7. **Document** → Keep a spreadsheet of each query, result count, and relevance assessment

**Example Workflow for "Behavioral Anomaly Detection for Service Accounts":**

| Step | Action | Query |
|------|--------|-------|
| 1 | Core concepts | service account, anomaly detection, behavioral, baseline |
| 2 | Synonyms | service account*, machine identit*; anomaly detection, outlier detection; behavioral baseline*, behavior profile* |
| 3 | Base query | `(service account* OR machine identit*) AND (anomaly detection OR outlier detection) AND (behavioral baseline* OR behavior profile*)` |
| 4 | Add specificity | Add `cat:cs.CR` for security focus; date: last 3 years |
| 5 | Mutations | Remove "OR outlier" (narrower); Add `ANDNOT (user OR human)` (exclude non-target papers); Use title-only: `ti:(anomaly detection) AND ti:(service account*)` |
| 6 | Test | Base query yields 45 results; mutation with ANDNOT yields 28; title-only yields 8; select mutation with ~30-40 results as sweet spot |
| 7 | Document | Log final query, result count, top 3 papers found |

---

## Phase 3: Distilling Paper Contents Into Usable Results

### 3.1 Paper Screening and Pre-Assessment

**Quick Relevance Filtering (2-3 minutes per paper):**

Before deep-diving into a paper, quickly assess relevance:

1. **Title scan**: Does the title directly address your research question?
   - Highly relevant: explicit match (e.g., "Workload Identity Federation in Multi-Cloud Environments")
   - Moderately relevant: related but not direct (e.g., "Zero-Trust Architecture for Cloud Services")
   - Marginally relevant: tangential (e.g., "OAuth2.0 Standards and Best Practices")

2. **Abstract skim**: Read abstract in 1-2 minutes
   - Extract: research problem, proposed solution, key findings
   - Flag: methodology (empirical vs. theoretical), dataset/context, applicability to your survey
   - Decision: Include (proceed to full read), Conditional (may be useful, keep in backlog), Exclude (not relevant)

3. **Structure preview**: Scan section headings (Introduction, Methodology, Results, Discussion, Conclusion)
   - Identify: experimental setup, datasets, empirical claims
   - Note: theoretical contributions vs. applied implementation

**Screening Result Categories:**

- **Red (Skip)**: Out-of-scope topic, outdated (>5 years old unless seminal), non-peer-reviewed
- **Yellow (Review Later)**: Related but not directly relevant; may provide context
- **Green (Read Full)**: Directly addresses research question; likely to extract novel findings

Aim to quickly categorize 50-100 papers down to ~15-25 "Green" papers for full analysis.

### 3.2 Structured Paper Content Analysis

For each "Green" paper, use this framework to extract usable content:

**Part A: Paper Metadata & Context**
- Title, authors, publication date, venue/journal
- Funding/affiliation (may indicate bias or credibility factors)
- Citation count (indicates impact; search Google Scholar)
- Category/tags assigned by authors

**Part B: Problem Statement & Research Question**
- *What problem does this paper solve?*
  - Extract: Explicit statement from Abstract/Introduction
  - Note: Relationship to your survey's problem space
- *What research question does it address?*
  - Often stated explicitly (e.g., "Research Question 1: How can organizations...")
  - If implicit, infer from literature gaps identified
- *Why does it matter?* (Motivation)
  - Quantitative evidence of the problem's scale (e.g., "94% of organizations lack X")
  - Qualitative motivation (risk, market opportunity, technical challenge)

**Part C: Methodology & Approach**
- **Type**: Empirical (measurement, user study, experiment), Theoretical (formal analysis, proof), Implementation (architecture, tool, framework), Literature survey
- **Scope**: Where/what was studied?
  - Example: "We surveyed 200 enterprises," "We analyzed 10,000 GitHub repositories," "We conducted case study with X company"
  - Note: How generalizable are findings? (Sample bias, context-specific, etc.)
- **Key technical approach**: What method/algorithm/tool was used?
  - For anomaly detection papers: What baseline model? What features? What labeled data?
  - For architecture papers: What technologies/standards? What trade-offs? What assumptions?

**Part D: Key Findings & Results**
- **Primary findings**: 2-3 main quantitative or qualitative results
  - Extract exact numbers/percentages if claimed
  - Note statistical significance (confidence intervals, p-values) if provided
  - Examples:
    - "Organizations using WIF reduced lateral movement dwell time from 6 months to 15 minutes"
    - "Behavioral baseline model achieved 94% anomaly detection accuracy with 2% false positive rate"
    - "78% of surveyed enterprises lack credential rotation automation"
- **Implications**: What does the finding mean?
  - For your survey context: Does it validate/contradict claims? Does it quantify an assertion?
  - For practitioners: What action should be taken?
  - For researchers: What questions remain?

**Part E: Critical Assessment**
- **Strengths**: 
  - Rigor (well-designed experiment, large sample, peer review)
  - Novelty (new technique, new insight, new application)
  - Applicability (findings generalize; practical relevance)
- **Limitations & Caveats**:
  - Acknowledged by authors (see Limitations section)
  - Gaps you identify (e.g., "Study only covered AWS; Azure/GCP may differ")
  - Confounds or unmeasured variables
  - Small sample size, artificial setting, outdated assumptions
- **Relevance to your survey**:
  - Direct application (validates/refutes survey claim)
  - Tangential (provides background, context, or related insight)
  - Gap-closing (addresses uncertainty in survey)

**Part F: Extractable Insights (Actionable Takeaways)**
- **For practitioners**: What should a CSP or enterprise do based on this paper?
- **For researchers**: What questions remain? What's the next step?
- **For your survey**: How does this paper deepen/sharpen/validate/challenge your survey's recommendations?
- **Quantitative evidence**: What specific metrics, numbers, or thresholds does this paper provide?

### 3.3 Note-Taking Structure for Efficient Extraction

Use this template for each paper (adapt to your tool—text file, spreadsheet, Notion, etc.):

```
PAPER ENTRY TEMPLATE
====================

[METADATA]
Title: 
Authors: 
Date: / Venue: 
URL/DOI: 
Citation Count (Google Scholar): 
Relevance Tag (Red/Yellow/Green): 

[PROBLEM & CONTEXT]
Problem Statement (1-2 sentences): 
Research Question: 
Motivation/Why It Matters: 
How it relates to [Your Survey Topic]: 

[METHODOLOGY]
Type (Empirical/Theoretical/Implementation/Survey): 
Study Setting/Sample (where, who, what scale): 
Key Technical Approach: 
Limitations/Scope Constraints: 

[KEY FINDINGS]
Finding 1: [Specific quantitative/qualitative result]
Finding 2: 
Finding 3: 
Critical Caveats: 

[ASSESSMENT]
Strengths (rigor, novelty, applicability): 
Weaknesses/Limitations: 
Confidence in Findings (High/Medium/Low): 

[EXTRACTABLE INSIGHTS]
Practitioner Action: 
Quantitative Evidence (metrics, thresholds, benchmarks): 
Validation/Contradiction of Survey Claims: 
Research Gaps Identified: 
```

### 3.4 Synthesizing Across Multiple Papers

Once you've analyzed ~15-25 papers from a given cluster, synthesize findings:

**Synthesis Activities:**

1. **Compare findings across papers**:
   - Do measurements align? (e.g., lateral movement dwell time: 6 months vs. 2 months)
   - Identify consensus vs. conflicting claims
   - Note variations due to methodology, context, or genuinely different results

2. **Identify trends over time**:
   - Plot key findings on a timeline (2020-2025)
   - Note technology adoption curves (e.g., OIDC adoption rates)
   - Identify emerging vs. established practices

3. **Cluster by theme**:
   - Group papers addressing the same topic (e.g., all papers on "behavioral anomaly detection")
   - For each cluster, identify: (a) consensus findings, (b) open debates, (c) methodological gaps

4. **Build an evidence matrix** (spreadsheet):
   - Rows: Papers
   - Columns: Key dimensions (e.g., for anomaly detection: "Model Type," "False Positive Rate," "Features Used," "Dataset Size," "Anomaly Types Detected")
   - Cells: Data extracted from each paper
   - Use this to identify patterns, outliers, and gaps in the research

5. **Identify research gaps**:
   - What questions do the papers collectively NOT answer?
   - What methodological limitations are consistent across papers?
   - What contexts are under-represented?

6. **Generate summary report per cluster** (1 page per cluster):
   - State-of-the-art: What is the current best practice/understanding?
   - Consensus findings: Where do multiple papers agree?
   - Open questions: What remains uncertain?
   - Recommended next steps: What research or implementation would be most valuable?

### 3.5 Integration Into Survey

Once Phase 3 synthesis is complete, map findings back to survey:

**For each survey claim or recommendation:**
1. Search your paper database for supporting evidence
2. Categorize evidence:
   - **Strong empirical support**: Multiple peer-reviewed papers with consistent findings
   - **Theoretical support**: Well-argued but not empirically validated
   - **Emerging evidence**: Few papers, preliminary findings
   - **No direct evidence**: Gap in literature; survey makes assertion unsupported by published research
3. Update survey sections with evidence citations and quantitative data
4. Flag assertions without evidence for future research or expert validation
5. Create "Research Priorities" appendix: List questions/gaps identified during ArXiv research

---

## Phase 3 Bonus: Advanced Extraction Techniques

### 3.5.1 Using Large Language Models for Paper Content Extraction

If analyzing >100 papers, consider semi-automating extraction with LLMs (ChatGPT, Claude, etc.):

**ChatExtract Method:**
1. Provide paper abstract or PDF to LLM
2. Use engineered prompts to extract structured data:
   ```
   Extract the following from this paper in JSON format:
   {
     "research_question": "[State the main research question]",
     "methodology": "[Type: Empirical/Theoretical/Other]",
     "key_findings": "[List 3-5 key quantitative findings]",
     "limitations": "[Explicitly stated limitations]",
     "applicability_to_security": "[Rate 1-5 and explain]"
   }
   ```
3. Review extracted data for accuracy; use follow-up questions to refine
4. Export to spreadsheet for synthesis

**Advantages**: Speed (analyze paper in 2-3 minutes); consistency in output format  
**Disadvantages**: Risk of hallucination; requires human review; may misinterpret nuanced claims

### 3.5.2 Citation Chasing

After identifying key papers, use citation chains to find related work:

1. **Forward citations**: Use Google Scholar to find papers that cite your key paper (more recent work building on it)
2. **Backward citations**: Check references in your key papers (earlier work it builds on)
3. **Author following**: Identify prolific authors in your domain; search for all their papers
4. **Venue following**: Identify conferences/journals publishing relevant work; search their proceedings

This can expand your corpus by 20-30% with high-relevance papers.

---

## Practical Workflow Summary

### Quick Reference: 3-Phase Process

**PHASE 1: Extract Topics from Survey**
- [ ] Identify Level 1 (primary), Level 2 (secondary), Level 3 (granular) topics
- [ ] Map dependency chains and risk-control pairs
- [ ] Create research question(s) for each topic cluster
- [ ] Identify quantitative claims needing validation
- [ ] Flag gaps/uncertainties in survey

**PHASE 2: Form Search Strings**
- [ ] For each topic cluster, create 5-10 search query variants
- [ ] Use Boolean operators, wildcards, phrase search appropriately
- [ ] Test queries: target 20-50 results per query (sweet spot)
- [ ] Combine mutations to increase coverage
- [ ] Document all queries with result counts

**PHASE 3: Distill Paper Contents**
- [ ] Screen papers: Red/Yellow/Green categorization
- [ ] For Green papers, extract: metadata, problem, methodology, findings, assessment, insights
- [ ] Synthesize across papers: compare, trend, cluster, build evidence matrix
- [ ] Integrate into survey: validate claims, quantify recommendations, identify gaps

**Total Effort Estimate:**
- Phase 1: 2-3 hours per survey topic
- Phase 2: 4-6 hours (formulating, testing, refining queries)
- Phase 3: 5-8 hours per 100 papers screened (includes reading ~20-25 full papers)
- **Total: 12-20 hours per survey deep-dive**

---

## Tools & Resources

**ArXiv Access:**
- ArXiv.org advanced search interface
- ArXiv API (Python: `arxiv` library; supports programmatic queries)
- Semantic search tools: searchthearxiv.com (OpenAI embeddings; find similar papers)

**Note-Taking & Organization:**
- Spreadsheet (Google Sheets, Excel): Evidence matrix, query log
- Notion, Obsidian: Structured templates for paper notes
- Zotero, Mendeley: Citation management and annotation
- ChatGPT/Claude: LLM-assisted extraction

**Citation & Discovery:**
- Google Scholar (citation counts, related papers)
- Semantic Scholar (AI-powered discovery)
- ResearchGate, Papers With Code (author profiles, linked resources)

---

## Key Takeaways

1. **Hierarchical extraction is essential**: Drill from top-level concepts (NHI) through dependencies (AI agents → credential proliferation → lifecycle automation) to granular risks (behavioral baseline poisoning). This hierarchy drives search strategy.

2. **Query mutation multiplies coverage**: A single well-formed query finds ~30 papers; 5-10 mutations of that query find ~150-300 papers with much higher relevance-to-noise ratio than a single broad query.

3. **Screening is faster than reading**: Spend 2-3 min per abstract deciding Red/Yellow/Green; only read full papers marked Green. This 10:1 time ratio (100 papers screened, 10-20 read) is optimal.

4. **Synthesis reveals patterns**: Comparing findings across papers surfaces consensus, conflict, and gaps that a single paper cannot. Build evidence matrices to make patterns visible.

5. **Evidence mapping bridges survey to research**: Creating explicit links between survey claims and supporting papers strengthens credibility and identifies gaps for future research.

---

## Appendix: Example Search Queries for Your "NHI Authentication & AI Agents" Survey

These queries target the core topics in your example survey. Adapt these templates for other domains:

```
QUERY SET A: Workload Identity & Short-Lived Tokens
============================================
1. abs:(workload identit* OR identity federation) AND (authentication OR credential*) AND (token* OR JWT)
2. ti:(OIDC OR OpenID) AND (workload* OR service* OR microservice*)
3. abs:(short-lived token* OR ephemeral credential*) AND (lateral movement OR privilege escalation) AND mitigation
4. abs:(zero standing privilege) AND (authentication OR credential*)
5. abs:(credential rotation OR credential lifecycle) AND automation

QUERY SET B: Service Account & Machine Identity Security
=====================================================
1. abs:(service account* OR API key*) AND (compromise OR attack* OR lateral movement)
2. abs:(machine identit* OR non-human identit*) AND (lifecycle OR inventory OR discovery)
3. ti:(secret exposure) AND (GitHub OR repository OR repository*)
4. abs:(service account lifecycle) AND (automation OR management OR governance)
5. abs:(privilege escalation) AND (service account* OR container* OR microservice*)

QUERY SET C: AI Agent Authentication & Authorization
================================================
1. abs:(AI agent* OR autonomous agent* OR agentic AI) AND (authentication OR authorization OR permission*)
2. abs:(agent* OR autonomous system*) AND (behavioral anomaly OR anomaly detection OR baseline*)
3. abs:(delegation) AND (agent* OR automation) AND (privilege* OR scope OR permission*)
4. abs:(AI security) AND (agent* OR automation) AND (cloud OR infrastructure)
5. abs:(AI threat* OR AI risk*) AND (agent* OR identity OR authentication)

QUERY SET D: Behavioral Monitoring & Anomaly Detection
=================================================
1. abs:(anomaly detection OR behavioral baseline*) AND (machine identit* OR service account* OR API)
2. abs:(behavioral monitoring) AND (authentication OR access control OR identit*)
3. abs:(model drift) AND (machine learning OR deep learning) AND (security OR detection)
4. abs:(insider threat OR unauthorized access) AND (behavioral* OR anomaly OR baseline*)
5. ti:(zero trust) AND (behavior* OR anomaly OR continuous verification)

QUERY SET E: Cloud Identity & Access Management Evolution
====================================================
1. abs:(IAM OR identity access management) AND (cloud OR AWS OR Azure OR Google Cloud) AND (evolution OR future OR trend*)
2. abs:(credential* OR identit*) AND (cloud computing OR cloud infrastructure) AND (threat* OR attack*)
3. ti:(cloud security) AND (identit* OR credential* OR authentication) AND (2024 OR 2025)
4. abs:(CSP OR cloud service provider) AND (identit* OR credential*) AND (security OR challenge*)
5. abs:(zero trust architecture) AND (implementation OR deployment OR enterprise)
```

Run each query set against ArXiv; expect 30-80 results per query. Filter by category (`cat:cs.CR`), date range (last 3-5 years), and relevance to your specific focus.

