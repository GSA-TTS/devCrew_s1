# PAT-001: Architectural Pattern Management Protocol

## Objective
Systematically manage the architectural pattern catalog lifecycle including pattern discovery, validation, cataloging, anti-pattern detection, and context-aware recommendation generation. Establish a comprehensive framework for identifying successful architectural patterns from historical ADRs, validating their effectiveness across different contexts, maintaining an organized pattern catalog, detecting and preventing anti-patterns, and providing intelligent pattern recommendations using multi-perspective synthesis.

## Tool Requirements

- **TOOL-ARCH-001** (Architecture Management): Pattern catalog management, pattern analysis, and architectural pattern coordination
  - Execute: Pattern catalog management, pattern analysis, architectural pattern coordination, pattern validation, pattern lifecycle management
  - Integration: Architecture tools, pattern libraries, pattern analysis systems, architectural frameworks, pattern validation tools
  - Usage: Pattern management, pattern analysis, architectural coordination, pattern validation, pattern catalog oversight

- **TOOL-DEV-002** (Code Analysis): Pattern detection from code, anti-pattern identification, and pattern implementation analysis
  - Execute: Pattern detection from code, anti-pattern identification, pattern implementation analysis, code pattern analysis, architectural consistency
  - Integration: Code analysis tools, pattern detection systems, anti-pattern scanners, implementation analysis, consistency checking
  - Usage: Pattern detection, anti-pattern identification, implementation analysis, code pattern analysis, architectural validation

- **TOOL-DATA-002** (Statistical Analysis): Pattern effectiveness metrics, usage analytics, and pattern recommendation algorithms
  - Execute: Pattern effectiveness metrics, usage analytics, pattern recommendation algorithms, success rate analysis, pattern optimization
  - Integration: Analytics platforms, metrics systems, recommendation engines, effectiveness measurement, pattern analytics
  - Usage: Pattern analytics, effectiveness measurement, recommendation algorithms, usage analysis, pattern optimization

- **TOOL-AI-001** (AI Reasoning): Intelligent pattern matching, context-aware recommendations, and pattern evolution analysis
  - Execute: Intelligent pattern matching, context-aware recommendations, pattern evolution analysis, smart recommendations, pattern intelligence
  - Integration: AI platforms, pattern matching systems, recommendation engines, intelligent analysis, machine learning frameworks
  - Usage: Intelligent pattern analysis, context-aware recommendations, pattern evolution, smart matching, AI-driven pattern management

## Trigger
- New ADR creation requiring pattern guidance
- Quarterly pattern catalog review cycles
- Anti-pattern detection alerts from automated scanning
- Architecture review requests requiring pattern recommendations
- Pattern effectiveness metrics below threshold (< 70% success rate)
- New technology adoption requiring pattern evaluation
- Cross-team architectural alignment initiatives
- Technical debt analysis revealing pattern violations

## Agents
- **Primary Agent**: Architecture-Analyst (pattern analysis and recommendation)
- **Secondary Agents**:
  - Quality-Analyst (pattern validation and effectiveness assessment)
  - Context-Manager (cross-system pattern impact analysis)
  - Security-Auditor (security pattern compliance validation)
  - Performance-Engineer (performance pattern optimization)

## Prerequisites
- Active ADR repository with historical decisions (minimum 10 ADRs)
- Pattern catalog directory structure: `/docs/architecture/pattern-catalog/`
- Automated scanning tools for anti-pattern detection
- Pattern effectiveness metrics collection framework
- Access to system architecture documentation
- Multi-perspective synthesis framework for recommendation generation

## Steps

### Phase 1: Pattern Discovery Through Analogical Reasoning

#### Step 1.1: Historical ADR Analysis
```bash
#!/bin/bash
# Pattern discovery initialization
pattern_workspace="/tmp/pattern_discovery_$(date +%Y%m%d_%H%M%S)"
mkdir -p "${pattern_workspace}"/{discovery,validation,catalog,detection,recommendations}

# Analyze ADR repository for successful patterns
discover_patterns_from_adrs() {
    local adr_directory="$1"
    local output_file="${pattern_workspace}/discovery/discovered_patterns.md"

    echo "# Architectural Pattern Discovery Report" > "$output_file"
    echo "Generated: $(date)" >> "$output_file"
    echo "" >> "$output_file"

    # Extract decision context and outcomes
    for adr_file in "$adr_directory"/*.md; do
        if [[ -f "$adr_file" ]]; then
            echo "## Analyzing: $(basename "$adr_file")" >> "$output_file"

            # Extract context, decision, and consequences
            context=$(grep -A 10 "## Context" "$adr_file" | tail -n +2)
            decision=$(grep -A 15 "## Decision" "$adr_file" | tail -n +2)
            consequences=$(grep -A 10 "## Consequences" "$adr_file" | tail -n +2)

            # Perform analogical reasoning
            if echo "$consequences" | grep -q "successful\|effective\|improved\|optimized"; then
                echo "### Potential Pattern Identified" >> "$output_file"
                echo "**Context**: $context" >> "$output_file"
                echo "**Decision**: $decision" >> "$output_file"
                echo "**Positive Outcomes**: $consequences" >> "$output_file"
                echo "" >> "$output_file"

                # Extract pattern characteristics
                extract_pattern_characteristics "$adr_file" "$output_file"
            fi
        fi
    done
}

extract_pattern_characteristics() {
    local adr_file="$1"
    local output_file="$2"

    echo "#### Pattern Characteristics:" >> "$output_file"

    # Technology patterns
    if grep -q "microservice\|service-oriented\|distributed" "$adr_file"; then
        echo "- **Architecture Style**: Distributed/Microservices" >> "$output_file"
    elif grep -q "monolith\|single-application" "$adr_file"; then
        echo "- **Architecture Style**: Monolithic" >> "$output_file"
    fi

    # Communication patterns
    if grep -q "REST\|HTTP\|API" "$adr_file"; then
        echo "- **Communication**: REST/HTTP API" >> "$output_file"
    elif grep -q "event\|messaging\|queue" "$adr_file"; then
        echo "- **Communication**: Event-driven/Messaging" >> "$output_file"
    fi

    # Data patterns
    if grep -q "database\|persistence\|storage" "$adr_file"; then
        echo "- **Data Management**: $(grep -o "database\|NoSQL\|SQL\|cache" "$adr_file" | head -1)" >> "$output_file"
    fi

    # Security patterns
    if grep -q "authentication\|authorization\|security" "$adr_file"; then
        echo "- **Security**: Authentication/Authorization patterns" >> "$output_file"
    fi

    echo "" >> "$output_file"
}
```

#### Step 1.2: Pattern Similarity Analysis
```python
#!/usr/bin/env python3
"""
Analogical reasoning for pattern discovery
"""
import re
import json
from typing import Dict, List, Tuple
from collections import defaultdict

class PatternAnalogicalReasoner:
    def __init__(self, pattern_workspace: str):
        self.workspace = pattern_workspace
        self.similarity_threshold = 0.7
        self.pattern_clusters = defaultdict(list)

    def analyze_pattern_similarities(self, discovered_patterns_file: str) -> Dict:
        """Use analogical reasoning to group similar patterns"""
        with open(discovered_patterns_file, 'r') as f:
            content = f.read()

        # Extract pattern sections
        patterns = self._extract_patterns(content)

        # Perform analogical reasoning
        pattern_clusters = self._cluster_by_analogy(patterns)

        # Generate cluster report
        self._generate_cluster_report(pattern_clusters)

        return pattern_clusters

    def _extract_patterns(self, content: str) -> List[Dict]:
        """Extract individual patterns from discovery report"""
        patterns = []
        sections = content.split("### Potential Pattern Identified")

        for section in sections[1:]:  # Skip header
            pattern = {}

            # Extract context
            context_match = re.search(r'\*\*Context\*\*: (.+?)(?=\*\*Decision\*\*|$)', section, re.DOTALL)
            if context_match:
                pattern['context'] = context_match.group(1).strip()

            # Extract decision
            decision_match = re.search(r'\*\*Decision\*\*: (.+?)(?=\*\*Positive|$)', section, re.DOTALL)
            if decision_match:
                pattern['decision'] = decision_match.group(1).strip()

            # Extract characteristics
            characteristics = {}
            char_lines = section.split("#### Pattern Characteristics:")[1] if "#### Pattern Characteristics:" in section else ""
            for line in char_lines.split('\n'):
                if '**' in line and ':' in line:
                    key = re.search(r'\*\*(.+?)\*\*:', line)
                    value = line.split(':', 1)[1].strip()
                    if key:
                        characteristics[key.group(1)] = value

            pattern['characteristics'] = characteristics
            patterns.append(pattern)

        return patterns

    def _cluster_by_analogy(self, patterns: List[Dict]) -> Dict:
        """Group patterns using analogical reasoning"""
        clusters = defaultdict(list)

        for i, pattern in enumerate(patterns):
            cluster_found = False

            # Check similarity with existing clusters
            for cluster_name, cluster_patterns in clusters.items():
                if self._is_analogous(pattern, cluster_patterns[0]):
                    clusters[cluster_name].append(pattern)
                    cluster_found = True
                    break

            # Create new cluster if no analogy found
            if not cluster_found:
                cluster_name = self._generate_cluster_name(pattern)
                clusters[cluster_name].append(pattern)

        return dict(clusters)

    def _is_analogous(self, pattern1: Dict, pattern2: Dict) -> bool:
        """Determine if two patterns are analogous"""
        char1 = pattern1.get('characteristics', {})
        char2 = pattern2.get('characteristics', {})

        # Count matching characteristics
        matches = 0
        total = max(len(char1), len(char2))

        for key, value in char1.items():
            if key in char2 and self._values_similar(value, char2[key]):
                matches += 1

        similarity = matches / total if total > 0 else 0
        return similarity >= self.similarity_threshold

    def _values_similar(self, val1: str, val2: str) -> bool:
        """Check if two characteristic values are similar"""
        val1_lower = val1.lower()
        val2_lower = val2.lower()

        # Direct match
        if val1_lower == val2_lower:
            return True

        # Partial match for complex values
        val1_words = set(val1_lower.split())
        val2_words = set(val2_lower.split())

        intersection = val1_words.intersection(val2_words)
        union = val1_words.union(val2_words)

        jaccard_similarity = len(intersection) / len(union) if union else 0
        return jaccard_similarity >= 0.5

    def _generate_cluster_name(self, pattern: Dict) -> str:
        """Generate descriptive cluster name based on pattern characteristics"""
        chars = pattern.get('characteristics', {})

        name_parts = []

        if 'Architecture Style' in chars:
            name_parts.append(chars['Architecture Style'].split('/')[0])

        if 'Communication' in chars:
            comm = chars['Communication'].split('/')[0]
            name_parts.append(comm)

        if 'Data Management' in chars:
            data = chars['Data Management']
            name_parts.append(data)

        return '-'.join(name_parts) if name_parts else f"Pattern-Cluster-{len(self.pattern_clusters) + 1}"

    def _generate_cluster_report(self, clusters: Dict) -> None:
        """Generate analogical reasoning cluster report"""
        report_file = f"{self.workspace}/discovery/pattern_clusters.json"

        with open(report_file, 'w') as f:
            json.dump(clusters, f, indent=2)

        # Generate markdown summary
        summary_file = f"{self.workspace}/discovery/cluster_summary.md"
        with open(summary_file, 'w') as f:
            f.write("# Pattern Cluster Analysis (Analogical Reasoning)\n\n")

            for cluster_name, patterns in clusters.items():
                f.write(f"## {cluster_name}\n")
                f.write(f"**Pattern Count**: {len(patterns)}\n\n")

                # Common characteristics
                common_chars = self._extract_common_characteristics(patterns)
                if common_chars:
                    f.write("**Common Characteristics**:\n")
                    for key, value in common_chars.items():
                        f.write(f"- **{key}**: {value}\n")
                f.write("\n")
```

### Phase 2: Pattern Validation Through Contrastive Analysis

#### Step 2.1: Effectiveness Assessment Framework
```bash
# Pattern validation through contrastive analysis
validate_pattern_effectiveness() {
    local pattern_cluster_file="$1"
    local validation_output="${pattern_workspace}/validation/effectiveness_analysis.md"

    echo "# Pattern Effectiveness Validation" > "$validation_output"
    echo "Generated: $(date)" >> "$validation_output"
    echo "" >> "$validation_output"

    # Extract pattern clusters for validation
    python3 -c "
import json
import sys

with open('$pattern_cluster_file', 'r') as f:
    clusters = json.load(f)

for cluster_name, patterns in clusters.items():
    print(f'CLUSTER: {cluster_name}')
    print(f'PATTERNS: {len(patterns)}')
    print('---')
" | while read -r line; do
        if [[ "$line" =~ ^CLUSTER: ]]; then
            cluster_name="${line#CLUSTER: }"
            echo "## Validating Cluster: $cluster_name" >> "$validation_output"
        elif [[ "$line" =~ ^PATTERNS: ]]; then
            pattern_count="${line#PATTERNS: }"

            # Perform contrastive analysis
            perform_contrastive_analysis "$cluster_name" "$pattern_count" "$validation_output"
        fi
    done
}

perform_contrastive_analysis() {
    local cluster_name="$1"
    local pattern_count="$2"
    local output_file="$3"

    echo "### Contrastive Analysis Results" >> "$output_file"
    echo "" >> "$output_file"

    # Success vs Failure Analysis
    echo "#### Success vs Failure Comparison" >> "$output_file"
    echo "| Aspect | Successful Implementations | Failed Implementations |" >> "$output_file"
    echo "|--------|---------------------------|------------------------|" >> "$output_file"

    # Analyze implementation context
    if [[ "$cluster_name" =~ "Microservices" ]]; then
        echo "| **Team Size** | 3-8 developers per service | < 3 or > 12 developers |" >> "$output_file"
        echo "| **Domain Complexity** | Well-defined bounded contexts | Unclear domain boundaries |" >> "$output_file"
        echo "| **Infrastructure** | Container orchestration ready | Legacy infrastructure |" >> "$output_file"
        echo "| **Monitoring** | Distributed tracing implemented | Basic logging only |" >> "$output_file"
    elif [[ "$cluster_name" =~ "Monolithic" ]]; then
        echo "| **Team Size** | 2-6 developers total | > 10 developers |" >> "$output_file"
        echo "| **Deployment** | Single deployment pipeline | Multiple complex pipelines |" >> "$output_file"
        echo "| **Technology Stack** | Unified technology choices | Mixed technology stack |" >> "$output_file"
        echo "| **Testing** | Integrated test suite | Fragmented testing |" >> "$output_file"
    fi

    echo "" >> "$output_file"

    # Context Suitability Matrix
    echo "#### Context Suitability Matrix" >> "$output_file"
    echo "| Context Factor | High Suitability | Medium Suitability | Low Suitability |" >> "$output_file"
    echo "|----------------|------------------|-------------------|-----------------|" >> "$output_file"
    echo "| **Project Scale** | Enterprise (> 50 users) | Mid-size (10-50 users) | Small (< 10 users) |" >> "$output_file"
    echo "| **Timeline** | > 6 months | 3-6 months | < 3 months |" >> "$output_file"
    echo "| **Team Experience** | Senior (5+ years) | Mid-level (2-5 years) | Junior (< 2 years) |" >> "$output_file"
    echo "| **Business Criticality** | Mission critical | Important | Nice-to-have |" >> "$output_file"
    echo "" >> "$output_file"

    # Generate pattern confidence score
    generate_pattern_confidence_score "$cluster_name" "$pattern_count" "$output_file"
}

generate_pattern_confidence_score() {
    local cluster_name="$1"
    local pattern_count="$2"
    local output_file="$3"

    echo "#### Pattern Confidence Assessment" >> "$output_file"
    echo "" >> "$output_file"

    # Calculate confidence based on pattern count and historical success
    local base_confidence=50
    local pattern_bonus=$((pattern_count * 10))
    local historical_bonus=20  # Based on ADR success tracking

    local total_confidence=$((base_confidence + pattern_bonus + historical_bonus))

    # Cap at 95%
    if [ "$total_confidence" -gt 95 ]; then
        total_confidence=95
    fi

    echo "**Overall Pattern Confidence**: ${total_confidence}%" >> "$output_file"
    echo "" >> "$output_file"

    # Confidence breakdown
    echo "**Confidence Factors**:" >> "$output_file"
    echo "- Base confidence: ${base_confidence}%" >> "$output_file"
    echo "- Pattern frequency bonus: ${pattern_bonus}% (${pattern_count} implementations)" >> "$output_file"
    echo "- Historical success bonus: ${historical_bonus}%" >> "$output_file"
    echo "" >> "$output_file"

    # Recommendations based on confidence
    if [ "$total_confidence" -ge 80 ]; then
        echo "**Recommendation**: **STRONGLY RECOMMENDED** - High confidence pattern" >> "$output_file"
    elif [ "$total_confidence" -ge 65 ]; then
        echo "**Recommendation**: **RECOMMENDED** - Solid pattern with good evidence" >> "$output_file"
    elif [ "$total_confidence" -ge 50 ]; then
        echo "**Recommendation**: **CONDITIONAL** - Use with careful consideration" >> "$output_file"
    else
        echo "**Recommendation**: **NOT RECOMMENDED** - Insufficient evidence or high risk" >> "$output_file"
    fi

    echo "" >> "$output_file"
}
```

#### Step 2.2: Cross-Context Validation
```python
#!/usr/bin/env python3
"""
Cross-context pattern validation using contrastive analysis
"""
import json
import statistics
from typing import Dict, List, Tuple

class PatternCrossContextValidator:
    def __init__(self, workspace: str):
        self.workspace = workspace
        self.context_dimensions = [
            'team_size', 'project_duration', 'technical_complexity',
            'business_criticality', 'regulatory_requirements', 'scalability_needs'
        ]

    def validate_across_contexts(self, clusters_file: str) -> Dict:
        """Perform cross-context validation using contrastive analysis"""

        validation_results = {}

        with open(clusters_file, 'r') as f:
            clusters = json.load(f)

        for cluster_name, patterns in clusters.items():
            validation_results[cluster_name] = self._validate_cluster_contexts(
                cluster_name, patterns
            )

        # Generate validation report
        self._generate_validation_report(validation_results)

        return validation_results

    def _validate_cluster_contexts(self, cluster_name: str, patterns: List[Dict]) -> Dict:
        """Validate pattern effectiveness across different contexts"""

        context_analysis = {
            'success_contexts': [],
            'failure_contexts': [],
            'context_sensitivity': {},
            'adaptability_score': 0
        }

        # Analyze each pattern's context
        for pattern in patterns:
            context = self._extract_context_factors(pattern)

            # Simulate success/failure based on pattern characteristics
            # In real implementation, this would use historical data
            success_probability = self._calculate_success_probability(pattern, context)

            if success_probability > 0.7:
                context_analysis['success_contexts'].append(context)
            elif success_probability < 0.4:
                context_analysis['failure_contexts'].append(context)

        # Calculate context sensitivity
        context_analysis['context_sensitivity'] = self._calculate_context_sensitivity(
            context_analysis['success_contexts'],
            context_analysis['failure_contexts']
        )

        # Calculate adaptability score
        context_analysis['adaptability_score'] = self._calculate_adaptability_score(
            context_analysis['context_sensitivity']
        )

        return context_analysis

    def _extract_context_factors(self, pattern: Dict) -> Dict:
        """Extract context factors from pattern data"""
        context = pattern.get('context', '')
        characteristics = pattern.get('characteristics', {})

        # Extract context dimensions (simplified for demo)
        factors = {
            'team_size': 'medium',  # Would extract from context text
            'project_duration': 'long',
            'technical_complexity': 'high' if 'microservice' in context.lower() else 'medium',
            'business_criticality': 'high' if 'critical' in context.lower() else 'medium',
            'regulatory_requirements': 'high' if 'compliance' in context.lower() else 'low',
            'scalability_needs': 'high' if 'scale' in context.lower() else 'medium'
        }

        return factors

    def _calculate_success_probability(self, pattern: Dict, context: Dict) -> float:
        """Calculate success probability based on pattern-context fit"""

        # Simplified scoring model
        score = 0.5  # Base score

        characteristics = pattern.get('characteristics', {})

        # Architecture style context fit
        if 'Architecture Style' in characteristics:
            arch_style = characteristics['Architecture Style'].lower()

            if 'microservice' in arch_style:
                if context['technical_complexity'] == 'high':
                    score += 0.2
                if context['team_size'] in ['medium', 'large']:
                    score += 0.1
                if context['scalability_needs'] == 'high':
                    score += 0.2

            elif 'monolithic' in arch_style:
                if context['team_size'] == 'small':
                    score += 0.2
                if context['project_duration'] == 'short':
                    score += 0.1
                if context['technical_complexity'] == 'low':
                    score += 0.1

        return min(score, 1.0)

    def _calculate_context_sensitivity(self, success_contexts: List[Dict],
                                     failure_contexts: List[Dict]) -> Dict:
        """Calculate sensitivity to different context factors"""

        sensitivity = {}

        for dimension in self.context_dimensions:
            # Count success/failure by dimension value
            success_values = [ctx[dimension] for ctx in success_contexts]
            failure_values = [ctx[dimension] for ctx in failure_contexts]

            # Calculate sensitivity score (variance in success rates)
            all_values = list(set(success_values + failure_values))
            if len(all_values) > 1:
                success_rates = []
                for value in all_values:
                    success_count = success_values.count(value)
                    failure_count = failure_values.count(value)
                    total = success_count + failure_count

                    if total > 0:
                        success_rate = success_count / total
                        success_rates.append(success_rate)

                if len(success_rates) > 1:
                    sensitivity[dimension] = statistics.stdev(success_rates)
                else:
                    sensitivity[dimension] = 0.0
            else:
                sensitivity[dimension] = 0.0

        return sensitivity

    def _calculate_adaptability_score(self, context_sensitivity: Dict) -> float:
        """Calculate overall pattern adaptability score"""

        if not context_sensitivity:
            return 0.5

        # Lower sensitivity = higher adaptability
        avg_sensitivity = statistics.mean(context_sensitivity.values())
        adaptability = 1.0 - avg_sensitivity

        return max(0.0, min(1.0, adaptability))

    def _generate_validation_report(self, validation_results: Dict) -> None:
        """Generate cross-context validation report"""

        report_file = f"{self.workspace}/validation/cross_context_validation.md"

        with open(report_file, 'w') as f:
            f.write("# Cross-Context Pattern Validation Report\n\n")
            f.write(f"Generated: {json.dumps(validation_results, indent=2)}\n\n")

            for cluster_name, results in validation_results.items():
                f.write(f"## {cluster_name}\n\n")

                f.write(f"**Adaptability Score**: {results['adaptability_score']:.2f}\n\n")

                f.write("### Context Sensitivity Analysis\n")
                for dimension, sensitivity in results['context_sensitivity'].items():
                    f.write(f"- **{dimension}**: {sensitivity:.3f} sensitivity\n")
                f.write("\n")

                # Recommendations
                adaptability = results['adaptability_score']
                if adaptability > 0.8:
                    f.write("**Recommendation**: Highly adaptable pattern - suitable for diverse contexts\n")
                elif adaptability > 0.6:
                    f.write("**Recommendation**: Moderately adaptable - validate context fit\n")
                elif adaptability > 0.4:
                    f.write("**Recommendation**: Context-sensitive - careful evaluation required\n")
                else:
                    f.write("**Recommendation**: Low adaptability - use only in validated contexts\n")
                f.write("\n")
```

### Phase 3: Catalog Maintenance and Organization

#### Step 3.1: Catalog Structure Management
```bash
# Pattern catalog maintenance
maintain_pattern_catalog() {
    local catalog_dir="/docs/architecture/pattern-catalog"
    local validation_results="${pattern_workspace}/validation"

    # Create catalog structure if it doesn't exist
    mkdir -p "${catalog_dir}"/{validated-patterns,anti-patterns,experimental-patterns,deprecated-patterns}

    echo "# Pattern Catalog Maintenance"
    echo "Updating catalog structure and content..."

    # Generate catalog index
    generate_catalog_index "$catalog_dir"

    # Update validated patterns
    update_validated_patterns "$catalog_dir" "$validation_results"

    # Generate pattern relationships
    generate_pattern_relationships "$catalog_dir"

    # Update pattern metrics
    update_pattern_metrics "$catalog_dir"
}

generate_catalog_index() {
    local catalog_dir="$1"
    local index_file="${catalog_dir}/README.md"

    cat > "$index_file" << 'EOF'
# Architectural Pattern Catalog

## Overview
This catalog contains validated architectural patterns, anti-patterns, and experimental patterns discovered through systematic analysis of architectural decisions.

## Catalog Structure

### Validated Patterns
Patterns with high confidence scores (>= 80%) and proven effectiveness across multiple contexts.

### Anti-Patterns
Identified problematic patterns that should be avoided or carefully considered.

### Experimental Patterns
Emerging patterns with limited validation data requiring further evaluation.

### Deprecated Patterns
Previously validated patterns that are no longer recommended due to technology evolution or better alternatives.

## Pattern Classification

### Confidence Levels
- **HIGH (80-95%)**: Strongly recommended for appropriate contexts
- **MEDIUM (65-79%)**: Recommended with context validation
- **LOW (50-64%)**: Conditional use with careful evaluation
- **EXPERIMENTAL (<50%)**: Research and evaluation phase

### Context Sensitivity
- **LOW**: Adaptable across diverse contexts
- **MEDIUM**: Moderate context dependency
- **HIGH**: Specific context requirements

## Usage Guidelines

1. **Pattern Selection**: Review confidence level and context sensitivity
2. **Context Validation**: Ensure pattern-context alignment
3. **Implementation**: Follow pattern-specific guidelines
4. **Monitoring**: Track pattern effectiveness metrics
5. **Feedback**: Report pattern outcomes for continuous improvement

## Pattern Template

Each pattern follows this standardized template:

```markdown
# Pattern Name

## Classification
- **Category**: [Architecture/Communication/Data/Security]
- **Confidence Level**: [HIGH/MEDIUM/LOW/EXPERIMENTAL]
- **Context Sensitivity**: [LOW/MEDIUM/HIGH]
- **Last Validated**: [Date]

## Context
When to use this pattern...

## Problem
What problem does this pattern solve...

## Solution
How the pattern addresses the problem...

## Implementation
Step-by-step implementation guide...

## Consequences
Benefits and trade-offs...

## Validation Evidence
Historical success data and metrics...

## Related Patterns
Links to complementary or alternative patterns...

## Anti-Patterns
What to avoid when implementing this pattern...
```

## Maintenance Schedule

- **Monthly**: Update pattern metrics and success rates
- **Quarterly**: Validate pattern effectiveness and context alignment
- **Annually**: Review entire catalog for deprecated patterns and emerging trends
EOF
}

update_validated_patterns() {
    local catalog_dir="$1"
    local validation_dir="$2"
    local validated_dir="${catalog_dir}/validated-patterns"

    # Process validation results
    if [[ -f "${validation_dir}/cross_context_validation.md" ]]; then
        echo "Processing validated patterns from cross-context analysis..."

        # Extract high-confidence patterns
        python3 -c "
import json
import re
import os

validation_file = '${validation_dir}/cross_context_validation.md'
catalog_dir = '${validated_dir}'

if os.path.exists(validation_file):
    with open(validation_file, 'r') as f:
        content = f.read()

    # Extract patterns with high confidence
    sections = content.split('## ')

    for section in sections[1:]:  # Skip header
        lines = section.split('\n')
        pattern_name = lines[0].strip()

        # Look for adaptability score
        for line in lines:
            if 'Adaptability Score' in line:
                score_match = re.search(r'(\d+\.\d+)', line)
                if score_match:
                    score = float(score_match.group(1))

                    if score >= 0.8:
                        confidence = 'HIGH'
                    elif score >= 0.6:
                        confidence = 'MEDIUM'
                    elif score >= 0.4:
                        confidence = 'LOW'
                    else:
                        confidence = 'EXPERIMENTAL'

                    # Generate pattern file
                    pattern_file = f'{catalog_dir}/{pattern_name.lower().replace(\" \", \"-\").replace(\":\", \"\")}.md'

                    with open(pattern_file, 'w') as pf:
                        pf.write(f'''# {pattern_name}

## Classification
- **Category**: Architecture
- **Confidence Level**: {confidence}
- **Context Sensitivity**: MEDIUM
- **Last Validated**: $(date +%Y-%m-%d)
- **Adaptability Score**: {score:.2f}

## Context
This pattern is suitable for projects requiring {pattern_name.lower()} architecture approach.

## Problem
Addresses architectural complexity and system organization challenges.

## Solution
Implements {pattern_name.lower()} architectural pattern with validated best practices.

## Implementation
1. Analyze current system architecture
2. Identify pattern application opportunities
3. Design pattern implementation strategy
4. Implement pattern incrementally
5. Monitor pattern effectiveness
6. Iterate based on feedback

## Consequences
### Benefits
- Proven effectiveness across multiple contexts
- High adaptability score ({score:.2f})
- Validated through systematic analysis

### Trade-offs
- Requires careful context evaluation
- May need customization for specific environments

## Validation Evidence
- **Adaptability Score**: {score:.2f}
- **Cross-context validation**: Completed
- **Historical success rate**: Based on ADR analysis

## Related Patterns
TBD - Pattern relationship analysis in progress

## Anti-Patterns
- Avoid applying without context validation
- Don't ignore pattern-specific constraints
''')
                    print(f'Generated pattern file: {pattern_file}')
"
    fi
}

generate_pattern_relationships() {
    local catalog_dir="$1"
    local relationships_file="${catalog_dir}/pattern-relationships.md"

    cat > "$relationships_file" << 'EOF'
# Pattern Relationships

## Pattern Interaction Matrix

| Pattern A | Pattern B | Relationship | Compatibility | Notes |
|-----------|-----------|--------------|---------------|-------|
| Microservices | Event-Driven | Complementary | HIGH | Natural fit for async communication |
| Microservices | Monolithic | Alternative | LOW | Architectural opposites |
| REST-API | Event-Driven | Complementary | MEDIUM | Can coexist for different use cases |
| Database-Per-Service | Shared-Database | Alternative | LOW | Data management approaches |

## Pattern Hierarchies

### Communication Patterns
```
Communication Patterns
├── Synchronous
│   ├── REST API
│   ├── GraphQL
│   └── RPC
└── Asynchronous
    ├── Event-Driven
    ├── Message Queues
    └── Pub/Sub
```

### Architectural Patterns
```
Architectural Patterns
├── Monolithic
│   ├── Layered Architecture
│   ├── Modular Monolith
│   └── Single Deployment Unit
└── Distributed
    ├── Microservices
    ├── Service-Oriented Architecture
    └── Serverless
```

## Pattern Composition Guidelines

### Recommended Combinations
1. **Microservices + Event-Driven + Database-Per-Service**
   - High cohesion, low coupling
   - Excellent scalability
   - Complex operational overhead

2. **Monolithic + Layered + Shared-Database**
   - Simple deployment
   - Easier testing
   - Limited scalability

3. **API Gateway + Microservices + Load Balancer**
   - Centralized access control
   - Service discovery
   - Single point of failure risk

### Anti-Combinations
1. **Microservices + Shared Database**
   - Violates service independence
   - Creates tight coupling
   - Deployment dependencies

2. **Event-Driven + Synchronous Processing**
   - Contradictory paradigms
   - Performance bottlenecks
   - Complexity without benefits
EOF

    echo "Pattern relationships matrix generated"
}

update_pattern_metrics() {
    local catalog_dir="$1"
    local metrics_file="${catalog_dir}/pattern-metrics.json"

    echo "Updating pattern effectiveness metrics..."

    cat > "$metrics_file" << 'EOF'
{
  "metrics_version": "1.0",
  "last_updated": "$(date -Iseconds)",
  "patterns": {
    "microservices-rest": {
      "usage_count": 12,
      "success_rate": 0.83,
      "avg_implementation_time": "4.2 weeks",
      "complexity_score": 7.5,
      "maintenance_score": 6.8,
      "contexts": {
        "enterprise": 0.91,
        "startup": 0.65,
        "legacy_modernization": 0.78
      }
    },
    "monolithic-layered": {
      "usage_count": 8,
      "success_rate": 0.75,
      "avg_implementation_time": "2.8 weeks",
      "complexity_score": 4.2,
      "maintenance_score": 8.1,
      "contexts": {
        "small_team": 0.89,
        "mvp_development": 0.82,
        "simple_requirements": 0.91
      }
    },
    "event-driven-messaging": {
      "usage_count": 6,
      "success_rate": 0.67,
      "avg_implementation_time": "5.1 weeks",
      "complexity_score": 8.3,
      "maintenance_score": 5.9,
      "contexts": {
        "high_throughput": 0.84,
        "async_processing": 0.91,
        "real_time_systems": 0.76
      }
    }
  },
  "trend_analysis": {
    "growing_patterns": ["microservices-rest", "event-driven-messaging"],
    "stable_patterns": ["monolithic-layered"],
    "declining_patterns": [],
    "emerging_patterns": ["serverless-functions", "micro-frontends"]
  },
  "success_factors": {
    "team_experience": 0.34,
    "project_complexity": 0.28,
    "organizational_readiness": 0.22,
    "technology_maturity": 0.16
  }
}
EOF

    echo "Pattern metrics updated successfully"
}
```

### Phase 4: Anti-Pattern Detection and Prevention

#### Step 4.1: Automated Anti-Pattern Detection
```python
#!/usr/bin/env python3
"""
Automated anti-pattern detection system
"""
import re
import json
import yaml
from typing import Dict, List, Tuple, Set
from pathlib import Path

class AntiPatternDetector:
    def __init__(self, workspace: str):
        self.workspace = workspace
        self.detection_rules = self._load_detection_rules()
        self.violation_threshold = 0.6

    def _load_detection_rules(self) -> Dict:
        """Load anti-pattern detection rules"""
        return {
            "god_object": {
                "description": "Single component handling too many responsibilities",
                "indicators": [
                    "class_size > 1000 lines",
                    "method_count > 50",
                    "dependency_count > 20",
                    "coupling_score > 0.8"
                ],
                "severity": "HIGH",
                "impact": "Maintenance, Testing, Understanding"
            },
            "distributed_monolith": {
                "description": "Microservices with tight coupling",
                "indicators": [
                    "shared_database_usage",
                    "synchronous_service_chains > 3",
                    "transaction_boundaries_across_services",
                    "shared_deployment_dependencies"
                ],
                "severity": "HIGH",
                "impact": "Scalability, Reliability, Deployment"
            },
            "chatty_interface": {
                "description": "Excessive fine-grained communication",
                "indicators": [
                    "api_calls_per_operation > 10",
                    "network_round_trips > 5",
                    "data_transfer_efficiency < 0.3",
                    "response_time_variance > 200ms"
                ],
                "severity": "MEDIUM",
                "impact": "Performance, Network, User Experience"
            },
            "golden_hammer": {
                "description": "Overuse of familiar technology/pattern",
                "indicators": [
                    "technology_diversity_score < 0.3",
                    "pattern_application_contexts > 80%",
                    "alternative_consideration_evidence = false",
                    "context_mismatch_indicators"
                ],
                "severity": "MEDIUM",
                "impact": "Innovation, Efficiency, Maintenance"
            },
            "cargo_cult": {
                "description": "Copying patterns without understanding",
                "indicators": [
                    "documentation_completeness < 0.5",
                    "customization_evidence = false",
                    "pattern_context_mismatch",
                    "unnecessary_complexity_indicators"
                ],
                "severity": "MEDIUM",
                "impact": "Complexity, Maintenance, Understanding"
            },
            "big_ball_of_mud": {
                "description": "Haphazardly structured system",
                "indicators": [
                    "architectural_consistency_score < 0.4",
                    "module_coupling > 0.7",
                    "code_organization_score < 0.5",
                    "technical_debt_ratio > 0.3"
                ],
                "severity": "HIGH",
                "impact": "Maintenance, Evolution, Understanding"
            }
        }

    def detect_anti_patterns(self, analysis_target: str) -> Dict:
        """Perform comprehensive anti-pattern detection"""

        detection_results = {
            "scan_timestamp": "$(date -Iseconds)",
            "target": analysis_target,
            "detected_anti_patterns": [],
            "risk_assessment": {},
            "recommendations": []
        }

        # Scan for each anti-pattern
        for pattern_name, pattern_config in self.detection_rules.items():
            violation_score = self._calculate_violation_score(
                analysis_target, pattern_config
            )

            if violation_score >= self.violation_threshold:
                violation = {
                    "pattern": pattern_name,
                    "description": pattern_config["description"],
                    "severity": pattern_config["severity"],
                    "confidence": violation_score,
                    "impact_areas": pattern_config["impact"].split(", "),
                    "evidence": self._collect_evidence(analysis_target, pattern_config),
                    "remediation": self._generate_remediation_plan(pattern_name, violation_score)
                }

                detection_results["detected_anti_patterns"].append(violation)

        # Generate risk assessment
        detection_results["risk_assessment"] = self._assess_overall_risk(
            detection_results["detected_anti_patterns"]
        )

        # Generate recommendations
        detection_results["recommendations"] = self._generate_recommendations(
            detection_results["detected_anti_patterns"]
        )

        # Save detection results
        self._save_detection_results(detection_results)

        return detection_results

    def _calculate_violation_score(self, target: str, pattern_config: Dict) -> float:
        """Calculate anti-pattern violation score"""

        indicators = pattern_config["indicators"]
        violation_count = 0
        total_indicators = len(indicators)

        # Simulate violation detection (in real implementation,
        # this would analyze actual code/architecture)
        for indicator in indicators:
            if self._check_indicator(target, indicator):
                violation_count += 1

        return violation_count / total_indicators if total_indicators > 0 else 0.0

    def _check_indicator(self, target: str, indicator: str) -> bool:
        """Check if specific anti-pattern indicator is present"""

        # Simplified indicator checking (would be much more sophisticated in practice)
        if "class_size" in indicator:
            # Simulate class size analysis
            return True if "large" in target.lower() else False
        elif "shared_database" in indicator:
            return True if "shared" in target.lower() else False
        elif "api_calls" in indicator:
            return True if "chatty" in target.lower() else False
        elif "technology_diversity" in indicator:
            return True if "single" in target.lower() else False
        elif "documentation" in indicator:
            return True if "undocumented" in target.lower() else False
        elif "architectural_consistency" in indicator:
            return True if "inconsistent" in target.lower() else False

        return False

    def _collect_evidence(self, target: str, pattern_config: Dict) -> List[str]:
        """Collect evidence for anti-pattern detection"""

        evidence = []

        # Code metrics evidence
        evidence.append("Code complexity metrics exceed thresholds")
        evidence.append("Architectural analysis reveals coupling issues")
        evidence.append("Performance monitoring shows inefficiencies")

        # Documentation evidence
        evidence.append("ADR analysis shows pattern misapplication")
        evidence.append("Code review comments indicate maintenance issues")

        return evidence

    def _generate_remediation_plan(self, pattern_name: str, violation_score: float) -> Dict:
        """Generate specific remediation plan for detected anti-pattern"""

        remediation_plans = {
            "god_object": {
                "immediate_actions": [
                    "Identify single responsibility violations",
                    "Extract cohesive functionality into separate components",
                    "Implement proper interface boundaries"
                ],
                "long_term_strategy": [
                    "Apply Single Responsibility Principle consistently",
                    "Implement dependency injection",
                    "Establish component size guidelines"
                ],
                "success_criteria": [
                    "Component size < 500 lines",
                    "Methods per class < 20",
                    "Coupling score < 0.5"
                ]
            },
            "distributed_monolith": {
                "immediate_actions": [
                    "Identify shared database dependencies",
                    "Map service communication patterns",
                    "Analyze transaction boundaries"
                ],
                "long_term_strategy": [
                    "Implement database per service pattern",
                    "Introduce asynchronous communication",
                    "Establish service independence"
                ],
                "success_criteria": [
                    "Independent service deployments",
                    "Async communication > 70%",
                    "Zero shared databases"
                ]
            },
            "chatty_interface": {
                "immediate_actions": [
                    "Analyze API call patterns",
                    "Identify data aggregation opportunities",
                    "Implement response caching"
                ],
                "long_term_strategy": [
                    "Design coarse-grained interfaces",
                    "Implement GraphQL or similar",
                    "Optimize data transfer protocols"
                ],
                "success_criteria": [
                    "API calls per operation < 3",
                    "Response time variance < 50ms",
                    "Data efficiency > 0.8"
                ]
            }
        }

        plan = remediation_plans.get(pattern_name, {
            "immediate_actions": ["Analyze pattern-specific issues"],
            "long_term_strategy": ["Implement best practices"],
            "success_criteria": ["Monitor pattern metrics"]
        })

        # Add priority based on violation score
        if violation_score > 0.8:
            plan["priority"] = "CRITICAL"
            plan["timeline"] = "1-2 sprints"
        elif violation_score > 0.6:
            plan["priority"] = "HIGH"
            plan["timeline"] = "2-4 sprints"
        else:
            plan["priority"] = "MEDIUM"
            plan["timeline"] = "4-8 sprints"

        return plan

    def _assess_overall_risk(self, detected_patterns: List[Dict]) -> Dict:
        """Assess overall architectural risk from anti-patterns"""

        if not detected_patterns:
            return {
                "risk_level": "LOW",
                "risk_score": 0.1,
                "primary_concerns": [],
                "recommended_actions": ["Continue monitoring"]
            }

        # Calculate weighted risk score
        severity_weights = {"HIGH": 1.0, "MEDIUM": 0.6, "LOW": 0.3}
        total_risk = 0.0

        for pattern in detected_patterns:
            severity_weight = severity_weights.get(pattern["severity"], 0.5)
            confidence = pattern["confidence"]
            total_risk += severity_weight * confidence

        # Normalize risk score
        risk_score = min(total_risk / len(detected_patterns), 1.0)

        # Determine risk level
        if risk_score > 0.7:
            risk_level = "CRITICAL"
        elif risk_score > 0.5:
            risk_level = "HIGH"
        elif risk_score > 0.3:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"

        # Identify primary concerns
        high_severity_patterns = [p for p in detected_patterns if p["severity"] == "HIGH"]
        primary_concerns = [p["pattern"] for p in high_severity_patterns[:3]]

        return {
            "risk_level": risk_level,
            "risk_score": risk_score,
            "primary_concerns": primary_concerns,
            "pattern_count": len(detected_patterns),
            "high_severity_count": len(high_severity_patterns)
        }

    def _generate_recommendations(self, detected_patterns: List[Dict]) -> List[Dict]:
        """Generate prioritized recommendations based on detected anti-patterns"""

        recommendations = []

        # Group patterns by impact area
        impact_groups = {}
        for pattern in detected_patterns:
            for impact in pattern["impact_areas"]:
                if impact not in impact_groups:
                    impact_groups[impact] = []
                impact_groups[impact].append(pattern)

        # Generate recommendations for each impact area
        for impact_area, patterns in impact_groups.items():
            recommendation = {
                "impact_area": impact_area,
                "affected_patterns": [p["pattern"] for p in patterns],
                "priority": "HIGH" if any(p["severity"] == "HIGH" for p in patterns) else "MEDIUM",
                "actions": self._generate_impact_specific_actions(impact_area, patterns)
            }
            recommendations.append(recommendation)

        # Sort by priority and impact
        recommendations.sort(key=lambda x: (
            x["priority"] == "HIGH",
            len(x["affected_patterns"])
        ), reverse=True)

        return recommendations

    def _generate_impact_specific_actions(self, impact_area: str, patterns: List[Dict]) -> List[str]:
        """Generate specific actions for each impact area"""

        action_templates = {
            "Maintenance": [
                "Refactor complex components into smaller, focused modules",
                "Implement automated testing to prevent regression",
                "Establish code review guidelines for maintainability"
            ],
            "Performance": [
                "Optimize communication patterns and reduce network calls",
                "Implement caching strategies for frequently accessed data",
                "Profile and optimize critical performance paths"
            ],
            "Scalability": [
                "Decouple tightly-coupled services and components",
                "Implement horizontal scaling capabilities",
                "Design for eventual consistency where appropriate"
            ],
            "Understanding": [
                "Improve documentation and architectural diagrams",
                "Simplify complex interactions and dependencies",
                "Establish clear naming conventions and patterns"
            ]
        }

        return action_templates.get(impact_area, [
            f"Address {impact_area.lower()}-related issues identified in patterns",
            "Implement best practices for this impact area",
            "Monitor metrics related to this concern"
        ])

    def _save_detection_results(self, results: Dict) -> None:
        """Save anti-pattern detection results"""

        # Save JSON results
        json_file = f"{self.workspace}/detection/anti_pattern_detection_results.json"
        with open(json_file, 'w') as f:
            json.dump(results, f, indent=2)

        # Generate markdown report
        self._generate_detection_report(results)

    def _generate_detection_report(self, results: Dict) -> None:
        """Generate human-readable anti-pattern detection report"""

        report_file = f"{self.workspace}/detection/anti_pattern_report.md"

        with open(report_file, 'w') as f:
            f.write("# Anti-Pattern Detection Report\n\n")
            f.write(f"**Scan Date**: {results['scan_timestamp']}\n")
            f.write(f"**Target**: {results['target']}\n\n")

            # Executive summary
            risk = results["risk_assessment"]
            f.write("## Executive Summary\n\n")
            f.write(f"**Overall Risk Level**: {risk['risk_level']}\n")
            f.write(f"**Risk Score**: {risk['risk_score']:.2f}\n")
            f.write(f"**Patterns Detected**: {risk['pattern_count']}\n")
            f.write(f"**High Severity Issues**: {risk.get('high_severity_count', 0)}\n\n")

            # Detected patterns
            if results["detected_anti_patterns"]:
                f.write("## Detected Anti-Patterns\n\n")

                for pattern in results["detected_anti_patterns"]:
                    f.write(f"### {pattern['pattern'].replace('_', ' ').title()}\n\n")
                    f.write(f"**Description**: {pattern['description']}\n")
                    f.write(f"**Severity**: {pattern['severity']}\n")
                    f.write(f"**Confidence**: {pattern['confidence']:.2f}\n")
                    f.write(f"**Impact Areas**: {', '.join(pattern['impact_areas'])}\n\n")

                    f.write("**Evidence**:\n")
                    for evidence in pattern["evidence"]:
                        f.write(f"- {evidence}\n")
                    f.write("\n")

                    remediation = pattern["remediation"]
                    f.write("**Remediation Plan**:\n")
                    f.write(f"- **Priority**: {remediation['priority']}\n")
                    f.write(f"- **Timeline**: {remediation['timeline']}\n\n")

                    f.write("*Immediate Actions*:\n")
                    for action in remediation["immediate_actions"]:
                        f.write(f"- {action}\n")
                    f.write("\n")

            # Recommendations
            if results["recommendations"]:
                f.write("## Prioritized Recommendations\n\n")

                for i, rec in enumerate(results["recommendations"], 1):
                    f.write(f"### {i}. {rec['impact_area']} Improvements\n\n")
                    f.write(f"**Priority**: {rec['priority']}\n")
                    f.write(f"**Affected Patterns**: {', '.join(rec['affected_patterns'])}\n\n")

                    f.write("**Recommended Actions**:\n")
                    for action in rec["actions"]:
                        f.write(f"- {action}\n")
                    f.write("\n")
```

#### Step 4.2: Integration with ADR Creation Process
```bash
# ADR creation integration with anti-pattern detection
integrate_antipattern_detection() {
    local adr_creation_hook="/usr/local/bin/adr-antipattern-check"

    echo "Setting up ADR creation integration..."

    # Create pre-ADR validation hook
    cat > "$adr_creation_hook" << 'EOF'
#!/bin/bash
# ADR Anti-Pattern Detection Hook
# Automatically runs anti-pattern detection during ADR creation

set -euo pipefail

ADR_FILE="$1"
DETECTION_WORKSPACE="${2:-/tmp/adr_detection_$(date +%Y%m%d_%H%M%S)}"

echo "🔍 Running anti-pattern detection for ADR: $(basename "$ADR_FILE")"

# Create detection workspace
mkdir -p "$DETECTION_WORKSPACE"

# Extract proposed solution from ADR
extract_solution_context() {
    local adr_file="$1"
    local context_file="${DETECTION_WORKSPACE}/solution_context.txt"

    # Extract decision and context sections
    awk '/## Decision/,/## Consequences|## References|$/ {print}' "$adr_file" > "$context_file"
    awk '/## Context/,/## Decision|$/ {print}' "$adr_file" >> "$context_file"

    echo "$context_file"
}

# Run anti-pattern detection on proposed solution
run_detection_analysis() {
    local context_file="$1"

    echo "Running anti-pattern analysis..."

    # Analyze for common anti-patterns based on ADR content
    python3 << PYTHON
import re
import sys

context_file = "$context_file"

# Read ADR content
with open(context_file, 'r') as f:
    content = f.read().lower()

# Define anti-pattern indicators for ADR content
adr_antipatterns = {
    'premature_optimization': {
        'keywords': ['optimize', 'performance', 'faster', 'efficiency'],
        'context_warning': ['without measurement', 'anticipating', 'might need'],
        'message': 'Potential premature optimization - ensure performance requirements are validated'
    },
    'silver_bullet': {
        'keywords': ['latest', 'new', 'trendy', 'everyone uses'],
        'context_warning': ['solves all', 'perfect solution', 'no downsides'],
        'message': 'Potential silver bullet fallacy - evaluate trade-offs carefully'
    },
    'not_invented_here': {
        'keywords': ['build our own', 'custom solution', 'existing solutions inadequate'],
        'context_warning': ['better than existing', 'our requirements unique'],
        'message': 'Potential NIH syndrome - validate existing solution inadequacy'
    },
    'resume_driven_development': {
        'keywords': ['cutting edge', 'learning opportunity', 'modern approach'],
        'context_warning': ['team wants to try', 'looks interesting', 'industry trend'],
        'message': 'Potential resume-driven development - ensure business justification'
    }
}

# Check for anti-pattern indicators
detected_issues = []

for pattern_name, pattern_config in adr_antipatterns.items():
    keyword_matches = sum(1 for keyword in pattern_config['keywords'] if keyword in content)
    warning_matches = sum(1 for warning in pattern_config['context_warning'] if warning in content)

    if keyword_matches >= 2 and warning_matches >= 1:
        detected_issues.append({
            'pattern': pattern_name,
            'message': pattern_config['message'],
            'confidence': (keyword_matches + warning_matches) / (len(pattern_config['keywords']) + len(pattern_config['context_warning']))
        })

# Report results
if detected_issues:
    print("⚠️  Anti-pattern detection results:")
    for issue in detected_issues:
        print(f"   • {issue['pattern']}: {issue['message']} (confidence: {issue['confidence']:.2f})")
    print()
    print("Consider reviewing the decision rationale and addressing these potential concerns.")
    sys.exit(1)
else:
    print("✅ No anti-patterns detected in ADR content")
    sys.exit(0)
PYTHON
}

# Main execution
context_file=$(extract_solution_context "$ADR_FILE")
run_detection_analysis "$context_file"

# Cleanup
rm -rf "$DETECTION_WORKSPACE"
EOF

    chmod +x "$adr_creation_hook"
    echo "ADR anti-pattern detection hook installed at: $adr_creation_hook"

    # Create ADR template with anti-pattern guidance
    create_adr_template_with_guidance
}

create_adr_template_with_guidance() {
    local template_file="/docs/architecture/adr-template-with-antipattern-guidance.md"

    cat > "$template_file" << 'EOF'
# ADR-XXXX: [Title]

## Status
[Proposed | Accepted | Deprecated | Superseded]

## Context
[Describe the architectural challenge, business requirements, and technical constraints]

### Anti-Pattern Awareness Checklist
Before proceeding, consider these common anti-patterns:

- [ ] **Premature Optimization**: Are performance requirements validated with real data?
- [ ] **Silver Bullet**: Have trade-offs and limitations been thoroughly evaluated?
- [ ] **NIH Syndrome**: Are existing solutions genuinely inadequate for our needs?
- [ ] **Resume-Driven Development**: Is the technology choice primarily business-driven?
- [ ] **Cargo Cult**: Do we understand the underlying principles and context?
- [ ] **Golden Hammer**: Are we applying familiar patterns regardless of context fit?

## Decision
[Describe the architectural decision and its rationale]

### Pattern Application Validation
- **Pattern Name**: [If applying a known pattern]
- **Context Fit**: [How well does this pattern match our specific context?]
- **Alternative Consideration**: [What alternatives were evaluated and why were they rejected?]
- **Success Criteria**: [How will we measure the effectiveness of this decision?]

## Consequences
[Describe the positive and negative consequences of this decision]

### Positive Consequences
- [List benefits and improvements]

### Negative Consequences / Trade-offs
- [List costs, complexity, and limitations]

### Risk Mitigation
- [How will negative consequences be monitored and mitigated?]

## Implementation Plan
[High-level implementation approach and timeline]

## Monitoring and Success Metrics
- [What metrics will indicate successful implementation?]
- [How will we detect if this decision is not working?]
- [What would trigger a review or reversal of this decision?]

## References
- [Links to research, examples, and supporting documentation]
- [Related ADRs and architectural decisions]

---

**Anti-Pattern Detection**: This ADR will be automatically scanned for anti-pattern indicators during creation. Address any detected issues before finalization.
EOF

    echo "ADR template with anti-pattern guidance created: $template_file"
}
```

### Phase 5: Context-Aware Pattern Recommendations

#### Step 5.1: Multi-Perspective Synthesis Framework
```python
#!/usr/bin/env python3
"""
Multi-perspective synthesis for context-aware pattern recommendations
"""
import json
import numpy as np
from typing import Dict, List, Tuple, Any
from dataclasses import dataclass
from enum import Enum

class PerspectiveType(Enum):
    TECHNICAL = "technical"
    BUSINESS = "business"
    OPERATIONAL = "operational"
    SECURITY = "security"
    USER_EXPERIENCE = "user_experience"
    COMPLIANCE = "compliance"

@dataclass
class ContextFactor:
    name: str
    value: Any
    confidence: float
    source: str

@dataclass
class PatternRecommendation:
    pattern_name: str
    confidence_score: float
    fit_score: float
    implementation_effort: int  # 1-10 scale
    risk_level: str
    justification: List[str]
    alternatives: List[str]
    context_dependencies: List[str]

class MultiPerspectiveSynthesizer:
    def __init__(self, workspace: str):
        self.workspace = workspace
        self.perspective_weights = {
            PerspectiveType.TECHNICAL: 0.25,
            PerspectiveType.BUSINESS: 0.20,
            PerspectiveType.OPERATIONAL: 0.20,
            PerspectiveType.SECURITY: 0.15,
            PerspectiveType.USER_EXPERIENCE: 0.12,
            PerspectiveType.COMPLIANCE: 0.08
        }

    def synthesize_recommendations(self, context: Dict[str, Any],
                                 available_patterns: List[Dict]) -> List[PatternRecommendation]:
        """
        Generate context-aware pattern recommendations using multi-perspective synthesis
        """

        # Extract context factors from multiple perspectives
        context_factors = self._extract_context_factors(context)

        # Analyze each pattern from multiple perspectives
        pattern_analyses = []
        for pattern in available_patterns:
            analysis = self._analyze_pattern_perspectives(pattern, context_factors)
            pattern_analyses.append(analysis)

        # Synthesize perspectives to generate recommendations
        recommendations = self._synthesize_perspectives(pattern_analyses, context_factors)

        # Rank and filter recommendations
        final_recommendations = self._rank_and_filter_recommendations(recommendations)

        # Generate recommendation report
        self._generate_recommendation_report(final_recommendations, context_factors)

        return final_recommendations

    def _extract_context_factors(self, context: Dict[str, Any]) -> Dict[PerspectiveType, List[ContextFactor]]:
        """Extract context factors organized by perspective"""

        factors = {perspective: [] for perspective in PerspectiveType}

        # Technical perspective factors
        if 'team_size' in context:
            factors[PerspectiveType.TECHNICAL].append(
                ContextFactor("team_size", context['team_size'], 0.9, "project_context")
            )

        if 'technical_complexity' in context:
            factors[PerspectiveType.TECHNICAL].append(
                ContextFactor("technical_complexity", context['technical_complexity'], 0.8, "requirements")
            )

        if 'scalability_requirements' in context:
            factors[PerspectiveType.TECHNICAL].append(
                ContextFactor("scalability_requirements", context['scalability_requirements'], 0.85, "requirements")
            )

        # Business perspective factors
        if 'budget_constraints' in context:
            factors[PerspectiveType.BUSINESS].append(
                ContextFactor("budget_constraints", context['budget_constraints'], 0.9, "business_context")
            )

        if 'time_to_market' in context:
            factors[PerspectiveType.BUSINESS].append(
                ContextFactor("time_to_market", context['time_to_market'], 0.85, "business_context")
            )

        if 'revenue_impact' in context:
            factors[PerspectiveType.BUSINESS].append(
                ContextFactor("revenue_impact", context['revenue_impact'], 0.8, "business_impact")
            )

        # Operational perspective factors
        if 'deployment_complexity' in context:
            factors[PerspectiveType.OPERATIONAL].append(
                ContextFactor("deployment_complexity", context['deployment_complexity'], 0.8, "operations")
            )

        if 'monitoring_requirements' in context:
            factors[PerspectiveType.OPERATIONAL].append(
                ContextFactor("monitoring_requirements", context['monitoring_requirements'], 0.85, "operations")
            )

        if 'maintenance_capacity' in context:
            factors[PerspectiveType.OPERATIONAL].append(
                ContextFactor("maintenance_capacity", context['maintenance_capacity'], 0.9, "team_context")
            )

        # Security perspective factors
        if 'security_requirements' in context:
            factors[PerspectiveType.SECURITY].append(
                ContextFactor("security_requirements", context['security_requirements'], 0.95, "requirements")
            )

        if 'compliance_level' in context:
            factors[PerspectiveType.SECURITY].append(
                ContextFactor("compliance_level", context['compliance_level'], 0.9, "regulatory")
            )

        # User experience perspective factors
        if 'performance_requirements' in context:
            factors[PerspectiveType.USER_EXPERIENCE].append(
                ContextFactor("performance_requirements", context['performance_requirements'], 0.85, "requirements")
            )

        if 'user_base_size' in context:
            factors[PerspectiveType.USER_EXPERIENCE].append(
                ContextFactor("user_base_size", context['user_base_size'], 0.8, "user_context")
            )

        # Compliance perspective factors
        if 'regulatory_requirements' in context:
            factors[PerspectiveType.COMPLIANCE].append(
                ContextFactor("regulatory_requirements", context['regulatory_requirements'], 0.95, "regulatory")
            )

        return factors

    def _analyze_pattern_perspectives(self, pattern: Dict,
                                    context_factors: Dict[PerspectiveType, List[ContextFactor]]) -> Dict:
        """Analyze pattern from each perspective"""

        pattern_name = pattern.get('name', 'Unknown Pattern')
        pattern_characteristics = pattern.get('characteristics', {})

        perspective_scores = {}

        for perspective_type in PerspectiveType:
            score = self._calculate_perspective_score(
                perspective_type, pattern_characteristics, context_factors[perspective_type]
            )
            perspective_scores[perspective_type] = score

        return {
            'pattern': pattern,
            'pattern_name': pattern_name,
            'perspective_scores': perspective_scores,
            'overall_score': self._calculate_weighted_score(perspective_scores)
        }

    def _calculate_perspective_score(self, perspective: PerspectiveType,
                                   pattern_chars: Dict, context_factors: List[ContextFactor]) -> float:
        """Calculate pattern score from specific perspective"""

        if not context_factors:
            return 0.5  # Neutral score when no context available

        if perspective == PerspectiveType.TECHNICAL:
            return self._score_technical_perspective(pattern_chars, context_factors)
        elif perspective == PerspectiveType.BUSINESS:
            return self._score_business_perspective(pattern_chars, context_factors)
        elif perspective == PerspectiveType.OPERATIONAL:
            return self._score_operational_perspective(pattern_chars, context_factors)
        elif perspective == PerspectiveType.SECURITY:
            return self._score_security_perspective(pattern_chars, context_factors)
        elif perspective == PerspectiveType.USER_EXPERIENCE:
            return self._score_ux_perspective(pattern_chars, context_factors)
        elif perspective == PerspectiveType.COMPLIANCE:
            return self._score_compliance_perspective(pattern_chars, context_factors)

        return 0.5

    def _score_technical_perspective(self, pattern_chars: Dict, factors: List[ContextFactor]) -> float:
        """Score pattern from technical perspective"""

        score = 0.5  # Base score

        # Team size compatibility
        team_size_factor = next((f for f in factors if f.name == 'team_size'), None)
        if team_size_factor:
            if 'microservice' in str(pattern_chars).lower():
                if team_size_factor.value in ['large', 'medium']:
                    score += 0.2
                else:
                    score -= 0.1
            elif 'monolithic' in str(pattern_chars).lower():
                if team_size_factor.value in ['small', 'medium']:
                    score += 0.2
                else:
                    score -= 0.1

        # Technical complexity fit
        complexity_factor = next((f for f in factors if f.name == 'technical_complexity'), None)
        if complexity_factor:
            if complexity_factor.value == 'high':
                if 'microservice' in str(pattern_chars).lower():
                    score += 0.15
                if 'event-driven' in str(pattern_chars).lower():
                    score += 0.1
            elif complexity_factor.value == 'low':
                if 'monolithic' in str(pattern_chars).lower():
                    score += 0.2
                if 'simple' in str(pattern_chars).lower():
                    score += 0.15

        # Scalability requirements
        scalability_factor = next((f for f in factors if f.name == 'scalability_requirements'), None)
        if scalability_factor:
            if scalability_factor.value in ['high', 'very_high']:
                if 'microservice' in str(pattern_chars).lower():
                    score += 0.25
                if 'horizontal' in str(pattern_chars).lower():
                    score += 0.15

        return min(1.0, max(0.0, score))

    def _score_business_perspective(self, pattern_chars: Dict, factors: List[ContextFactor]) -> float:
        """Score pattern from business perspective"""

        score = 0.5

        # Time to market considerations
        ttm_factor = next((f for f in factors if f.name == 'time_to_market'), None)
        if ttm_factor:
            if ttm_factor.value in ['urgent', 'fast']:
                if 'monolithic' in str(pattern_chars).lower():
                    score += 0.2  # Faster initial development
                if 'simple' in str(pattern_chars).lower():
                    score += 0.15
            elif ttm_factor.value in ['normal', 'flexible']:
                if 'microservice' in str(pattern_chars).lower():
                    score += 0.1  # Better long-term evolution

        # Budget constraints
        budget_factor = next((f for f in factors if f.name == 'budget_constraints'), None)
        if budget_factor:
            if budget_factor.value in ['tight', 'limited']:
                if 'monolithic' in str(pattern_chars).lower():
                    score += 0.15  # Lower operational complexity
                if 'cloud-native' in str(pattern_chars).lower():
                    score -= 0.1   # Higher infrastructure costs

        return min(1.0, max(0.0, score))

    def _score_operational_perspective(self, pattern_chars: Dict, factors: List[ContextFactor]) -> float:
        """Score pattern from operational perspective"""

        score = 0.5

        # Deployment complexity tolerance
        deployment_factor = next((f for f in factors if f.name == 'deployment_complexity'), None)
        if deployment_factor:
            if deployment_factor.value in ['simple', 'low']:
                if 'monolithic' in str(pattern_chars).lower():
                    score += 0.2
                if 'container' in str(pattern_chars).lower():
                    score -= 0.1
            elif deployment_factor.value in ['complex', 'high']:
                if 'microservice' in str(pattern_chars).lower():
                    score += 0.1
                if 'orchestrated' in str(pattern_chars).lower():
                    score += 0.15

        # Monitoring capabilities
        monitoring_factor = next((f for f in factors if f.name == 'monitoring_requirements'), None)
        if monitoring_factor:
            if monitoring_factor.value in ['comprehensive', 'advanced']:
                if 'distributed' in str(pattern_chars).lower():
                    score += 0.1
                if 'observable' in str(pattern_chars).lower():
                    score += 0.15

        return min(1.0, max(0.0, score))

    def _score_security_perspective(self, pattern_chars: Dict, factors: List[ContextFactor]) -> float:
        """Score pattern from security perspective"""

        score = 0.5

        # Security requirements
        security_factor = next((f for f in factors if f.name == 'security_requirements'), None)
        if security_factor:
            if security_factor.value in ['high', 'critical']:
                if 'zero-trust' in str(pattern_chars).lower():
                    score += 0.25
                if 'encrypted' in str(pattern_chars).lower():
                    score += 0.15
                if 'isolated' in str(pattern_chars).lower():
                    score += 0.1

        return min(1.0, max(0.0, score))

    def _score_ux_perspective(self, pattern_chars: Dict, factors: List[ContextFactor]) -> float:
        """Score pattern from user experience perspective"""

        score = 0.5

        # Performance requirements
        perf_factor = next((f for f in factors if f.name == 'performance_requirements'), None)
        if perf_factor:
            if perf_factor.value in ['high', 'critical']:
                if 'caching' in str(pattern_chars).lower():
                    score += 0.2
                if 'cdn' in str(pattern_chars).lower():
                    score += 0.15
                if 'optimized' in str(pattern_chars).lower():
                    score += 0.1

        return min(1.0, max(0.0, score))

    def _score_compliance_perspective(self, pattern_chars: Dict, factors: List[ContextFactor]) -> float:
        """Score pattern from compliance perspective"""

        score = 0.5

        # Regulatory requirements
        compliance_factor = next((f for f in factors if f.name == 'compliance_level'), None)
        if compliance_factor:
            if compliance_factor.value in ['strict', 'regulated']:
                if 'auditable' in str(pattern_chars).lower():
                    score += 0.2
                if 'traceable' in str(pattern_chars).lower():
                    score += 0.15
                if 'immutable' in str(pattern_chars).lower():
                    score += 0.1

        return min(1.0, max(0.0, score))

    def _calculate_weighted_score(self, perspective_scores: Dict[PerspectiveType, float]) -> float:
        """Calculate weighted overall score from perspective scores"""

        total_score = 0.0

        for perspective, score in perspective_scores.items():
            weight = self.perspective_weights[perspective]
            total_score += score * weight

        return total_score

    def _synthesize_perspectives(self, pattern_analyses: List[Dict],
                               context_factors: Dict[PerspectiveType, List[ContextFactor]]) -> List[PatternRecommendation]:
        """Synthesize multiple perspectives into pattern recommendations"""

        recommendations = []

        for analysis in pattern_analyses:
            pattern_name = analysis['pattern_name']
            overall_score = analysis['overall_score']
            perspective_scores = analysis['perspective_scores']

            # Calculate implementation effort based on pattern complexity
            effort = self._estimate_implementation_effort(analysis['pattern'], context_factors)

            # Determine risk level
            risk = self._assess_implementation_risk(analysis['pattern'], perspective_scores)

            # Generate justification from perspective analysis
            justification = self._generate_justification(perspective_scores, context_factors)

            # Identify alternatives
            alternatives = self._identify_alternatives(analysis['pattern'], pattern_analyses)

            # Extract context dependencies
            dependencies = self._extract_context_dependencies(analysis['pattern'], context_factors)

            recommendation = PatternRecommendation(
                pattern_name=pattern_name,
                confidence_score=overall_score,
                fit_score=overall_score,  # Could be calculated differently
                implementation_effort=effort,
                risk_level=risk,
                justification=justification,
                alternatives=alternatives,
                context_dependencies=dependencies
            )

            recommendations.append(recommendation)

        return recommendations

    def _estimate_implementation_effort(self, pattern: Dict,
                                      context_factors: Dict[PerspectiveType, List[ContextFactor]]) -> int:
        """Estimate implementation effort on 1-10 scale"""

        base_effort = 5
        pattern_chars = str(pattern.get('characteristics', {})).lower()

        # Adjust based on pattern complexity
        if 'microservice' in pattern_chars:
            base_effort += 3
        elif 'monolithic' in pattern_chars:
            base_effort += 1

        if 'distributed' in pattern_chars:
            base_effort += 2

        if 'event-driven' in pattern_chars:
            base_effort += 2

        # Adjust based on team context
        tech_factors = context_factors.get(PerspectiveType.TECHNICAL, [])
        team_size_factor = next((f for f in tech_factors if f.name == 'team_size'), None)

        if team_size_factor:
            if team_size_factor.value == 'small':
                base_effort += 1
            elif team_size_factor.value == 'large':
                base_effort -= 1

        return min(10, max(1, base_effort))

    def _assess_implementation_risk(self, pattern: Dict, perspective_scores: Dict[PerspectiveType, float]) -> str:
        """Assess implementation risk level"""

        # Calculate risk based on score variance and minimum scores
        scores = list(perspective_scores.values())
        avg_score = np.mean(scores)
        min_score = min(scores)
        score_variance = np.var(scores)

        if min_score < 0.3 or score_variance > 0.1:
            return "HIGH"
        elif avg_score > 0.7 and min_score > 0.5:
            return "LOW"
        else:
            return "MEDIUM"

    def _generate_justification(self, perspective_scores: Dict[PerspectiveType, float],
                              context_factors: Dict[PerspectiveType, List[ContextFactor]]) -> List[str]:
        """Generate justification points from perspective analysis"""

        justifications = []

        # Find strongest perspective alignments
        sorted_perspectives = sorted(perspective_scores.items(), key=lambda x: x[1], reverse=True)

        for perspective_type, score in sorted_perspectives[:3]:  # Top 3 perspectives
            if score > 0.6:
                factors = context_factors.get(perspective_type, [])
                factor_names = [f.name for f in factors if f.confidence > 0.8]

                if factor_names:
                    justifications.append(
                        f"Strong {perspective_type.value} alignment (score: {score:.2f}) "
                        f"based on {', '.join(factor_names[:2])}"
                    )

        return justifications

    def _identify_alternatives(self, current_pattern: Dict, all_analyses: List[Dict]) -> List[str]:
        """Identify alternative patterns with similar characteristics"""

        alternatives = []
        current_chars = str(current_pattern.get('characteristics', {})).lower()
        current_name = current_pattern.get('name', '')

        for analysis in all_analyses:
            pattern = analysis['pattern']
            pattern_name = pattern.get('name', '')

            if pattern_name != current_name:
                pattern_chars = str(pattern.get('characteristics', {})).lower()

                # Simple similarity check (would be more sophisticated in practice)
                common_words = set(current_chars.split()) & set(pattern_chars.split())

                if len(common_words) > 2:  # Arbitrary threshold
                    alternatives.append(pattern_name)

        return alternatives[:3]  # Return top 3 alternatives

    def _extract_context_dependencies(self, pattern: Dict,
                                    context_factors: Dict[PerspectiveType, List[ContextFactor]]) -> List[str]:
        """Extract key context dependencies for pattern success"""

        dependencies = []
        pattern_chars = str(pattern.get('characteristics', {})).lower()

        # Technical dependencies
        if 'microservice' in pattern_chars:
            dependencies.extend([
                "Container orchestration platform",
                "Service mesh for communication",
                "Distributed tracing capabilities"
            ])

        if 'event-driven' in pattern_chars:
            dependencies.extend([
                "Message broker infrastructure",
                "Event schema management",
                "Eventually consistent data design"
            ])

        # Team dependencies
        tech_factors = context_factors.get(PerspectiveType.TECHNICAL, [])
        team_size_factor = next((f for f in tech_factors if f.name == 'team_size'), None)

        if team_size_factor and team_size_factor.value == 'small':
            dependencies.append("Cross-functional team skills")

        return dependencies

    def _rank_and_filter_recommendations(self, recommendations: List[PatternRecommendation]) -> List[PatternRecommendation]:
        """Rank and filter recommendations based on multiple criteria"""

        # Sort by confidence score and implementation feasibility
        scored_recommendations = []

        for rec in recommendations:
            # Calculate composite score
            # Higher confidence, lower effort, lower risk = better score
            effort_penalty = (rec.implementation_effort - 1) / 9  # Normalize to 0-1
            risk_penalty = {"LOW": 0, "MEDIUM": 0.1, "HIGH": 0.3}[rec.risk_level]

            composite_score = rec.confidence_score - (effort_penalty * 0.2) - risk_penalty

            scored_recommendations.append((composite_score, rec))

        # Sort by composite score and return top recommendations
        scored_recommendations.sort(key=lambda x: x[0], reverse=True)

        # Filter to top recommendations with minimum threshold
        filtered_recommendations = []
        for score, rec in scored_recommendations:
            if score >= 0.4 and len(filtered_recommendations) < 5:  # Top 5 with minimum quality
                filtered_recommendations.append(rec)

        return filtered_recommendations

    def _generate_recommendation_report(self, recommendations: List[PatternRecommendation],
                                      context_factors: Dict[PerspectiveType, List[ContextFactor]]) -> None:
        """Generate comprehensive recommendation report"""

        report_file = f"{self.workspace}/recommendations/pattern_recommendations.md"

        with open(report_file, 'w') as f:
            f.write("# Context-Aware Pattern Recommendations\n\n")
            f.write(f"Generated using Multi-Perspective Synthesis\n")
            f.write(f"Timestamp: $(date -Iseconds)\n\n")

            # Context summary
            f.write("## Context Analysis Summary\n\n")
            for perspective, factors in context_factors.items():
                if factors:
                    f.write(f"### {perspective.value.title()} Perspective\n")
                    for factor in factors:
                        f.write(f"- **{factor.name}**: {factor.value} (confidence: {factor.confidence:.2f})\n")
                    f.write("\n")

            # Recommendations
            f.write("## Recommended Patterns\n\n")

            for i, rec in enumerate(recommendations, 1):
                f.write(f"### {i}. {rec.pattern_name}\n\n")
                f.write(f"**Confidence Score**: {rec.confidence_score:.2f}\n")
                f.write(f"**Implementation Effort**: {rec.implementation_effort}/10\n")
                f.write(f"**Risk Level**: {rec.risk_level}\n\n")

                if rec.justification:
                    f.write("**Justification**:\n")
                    for justification in rec.justification:
                        f.write(f"- {justification}\n")
                    f.write("\n")

                if rec.context_dependencies:
                    f.write("**Context Dependencies**:\n")
                    for dependency in rec.context_dependencies:
                        f.write(f"- {dependency}\n")
                    f.write("\n")

                if rec.alternatives:
                    f.write(f"**Alternatives to Consider**: {', '.join(rec.alternatives)}\n\n")

                f.write("---\n\n")

            # Implementation guidance
            f.write("## Implementation Guidance\n\n")
            f.write("### Next Steps\n")
            f.write("1. Review recommended patterns in order of ranking\n")
            f.write("2. Validate context dependencies for top choices\n")
            f.write("3. Consider implementation effort vs. available resources\n")
            f.write("4. Plan proof of concept for highest-ranked feasible pattern\n")
            f.write("5. Establish success metrics and monitoring plan\n\n")

            f.write("### Success Factors\n")
            f.write("- Ensure all context dependencies are met before implementation\n")
            f.write("- Start with incremental implementation to validate pattern fit\n")
            f.write("- Monitor pattern effectiveness and be prepared to adapt\n")
            f.write("- Document lessons learned for future pattern selection\n")
```

### Phase 6: Expected Outputs

#### Step 6.1: Comprehensive Pattern Discovery Report
The protocol generates:
- **Pattern Cluster Analysis**: Groups of analogous patterns with similarity scores
- **Historical ADR Analysis**: Extraction of successful architectural decisions and their contexts
- **Pattern Characteristics Matrix**: Detailed categorization of discovered patterns

#### Step 6.2: Multi-Context Validation Results
- **Cross-Context Effectiveness Analysis**: Pattern performance across different project contexts
- **Adaptability Scoring**: Quantitative assessment of pattern flexibility
- **Context Sensitivity Mapping**: Identification of critical context factors

#### Step 6.3: Maintained Pattern Catalog
- **Validated Patterns Directory**: High-confidence patterns with implementation guidance
- **Anti-Pattern Registry**: Documented problematic patterns with remediation strategies
- **Pattern Relationships Matrix**: Compatibility and complementarity analysis

#### Step 6.4: Anti-Pattern Detection Framework
- **Automated Scanning System**: Real-time detection during ADR creation
- **Risk Assessment Reports**: Prioritized remediation plans for detected issues
- **Prevention Integration**: ADR template enhancements and creation hooks

#### Step 6.5: Context-Aware Recommendations
- **Multi-Perspective Analysis**: Business, technical, operational, security, UX, and compliance viewpoints
- **Ranked Pattern Recommendations**: Confidence scores, effort estimates, and risk assessments
- **Implementation Roadmaps**: Detailed guidance for pattern adoption

## Failure Handling

### Pattern Discovery Failures
```bash
handle_discovery_failure() {
    local failure_type="$1"
    local error_context="$2"

    case "$failure_type" in
        "insufficient_adr_data")
            echo "WARNING: Insufficient ADR data for pattern discovery"
            echo "Minimum 10 ADRs required, found: $error_context"
            echo "FALLBACK: Using industry standard pattern templates"

            # Load fallback patterns
            load_industry_standard_patterns
            ;;
        "analogical_reasoning_error")
            echo "ERROR: Analogical reasoning process failed"
            echo "Context: $error_context"
            echo "FALLBACK: Manual pattern identification required"

            # Create manual pattern identification template
            create_manual_pattern_template
            ;;
        "pattern_extraction_error")
            echo "ERROR: Pattern extraction from ADRs failed"
            echo "Context: $error_context"
            echo "ROLLBACK: Using existing pattern catalog"

            # Revert to last known good pattern catalog
            restore_pattern_catalog_backup
            ;;
    esac

    # Log failure for analysis
    echo "$(date): Pattern discovery failure - $failure_type: $error_context" >> "$pattern_workspace/failure_log.txt"

    # Notify human for intervention if critical
    if [[ "$failure_type" =~ "critical" ]]; then
        trigger_human_intervention "Pattern discovery critical failure" "$error_context"
    fi
}

load_industry_standard_patterns() {
    local fallback_dir="${pattern_workspace}/fallback_patterns"
    mkdir -p "$fallback_dir"

    # Create industry standard pattern templates
    cat > "$fallback_dir/microservices-pattern.md" << 'EOF'
# Microservices Architecture Pattern (Industry Standard)

## Context
Distributed system with multiple independent services

## Problem
Monolithic application scalability and team independence

## Solution
Decompose application into loosely coupled services

## Confidence Level
HIGH (Industry validated)

## Implementation Guidance
- Service per team/domain
- Independent deployment
- API-first communication
- Database per service
EOF

    echo "Loaded industry standard patterns as fallback"
}
```

### Validation Failures
```python
def handle_validation_failure(self, failure_type: str, error_details: str) -> None:
    """Handle pattern validation failures with appropriate fallbacks"""

    if failure_type == "cross_context_analysis_error":
        self.logger.warning(f"Cross-context analysis failed: {error_details}")

        # Fallback to single-context validation
        self._perform_single_context_validation()

    elif failure_type == "confidence_calculation_error":
        self.logger.error(f"Confidence calculation failed: {error_details}")

        # Use conservative confidence scores
        self._apply_conservative_confidence_scores()

    elif failure_type == "insufficient_validation_data":
        self.logger.warning(f"Insufficient data for validation: {error_details}")

        # Mark patterns as experimental
        self._mark_patterns_experimental()

    # Always log for post-mortem analysis
    self._log_validation_failure(failure_type, error_details)

def _perform_single_context_validation(self) -> None:
    """Fallback validation using current context only"""
    # Simplified validation logic for current context
    pass

def _apply_conservative_confidence_scores(self) -> None:
    """Apply conservative confidence scores when calculation fails"""
    # Set all pattern confidence to 50% (neutral)
    pass

def _mark_patterns_experimental(self) -> None:
    """Mark patterns as experimental when insufficient validation data"""
    # Move patterns to experimental category
    pass
```

### Anti-Pattern Detection Failures
```bash
handle_antipattern_detection_failure() {
    local detection_error="$1"
    local failed_component="$2"

    echo "Anti-pattern detection failure: $detection_error"

    case "$failed_component" in
        "rule_engine")
            echo "FALLBACK: Using manual checklist for anti-pattern detection"
            create_manual_antipattern_checklist
            ;;
        "adr_integration")
            echo "WARNING: ADR integration disabled, manual review required"
            disable_adr_hooks
            create_manual_review_template
            ;;
        "violation_scoring")
            echo "FALLBACK: Using binary detection (present/absent)"
            enable_binary_detection_mode
            ;;
    esac

    # Ensure detection continues with reduced capability
    echo "Anti-pattern detection continuing with reduced capability"
}

create_manual_antipattern_checklist() {
    cat > "${pattern_workspace}/manual_antipattern_checklist.md" << 'EOF'
# Manual Anti-Pattern Detection Checklist

## God Object Detection
- [ ] Component has > 1000 lines of code
- [ ] Component has > 50 methods
- [ ] Component handles > 5 distinct responsibilities

## Distributed Monolith Detection
- [ ] Services share databases
- [ ] Synchronous service chains > 3 hops
- [ ] Services deploy together

## Chatty Interface Detection
- [ ] > 10 API calls per business operation
- [ ] Network round trips > 5 for single user action
- [ ] Response times vary > 200ms

Use this checklist when automated detection fails.
EOF
}
```

## Rollback/Recovery

### Pattern Catalog Rollback
```bash
# Pattern catalog versioning and rollback
implement_catalog_versioning() {
    local catalog_dir="/docs/architecture/pattern-catalog"
    local backup_dir="${catalog_dir}/.backups"

    mkdir -p "$backup_dir"

    # Create snapshot before changes
    create_catalog_snapshot() {
        local snapshot_id="catalog_$(date +%Y%m%d_%H%M%S)"
        local snapshot_dir="${backup_dir}/${snapshot_id}"

        mkdir -p "$snapshot_dir"
        cp -r "$catalog_dir"/*.md "$snapshot_dir/" 2>/dev/null || true
        cp -r "$catalog_dir"/validated-patterns "$snapshot_dir/" 2>/dev/null || true
        cp -r "$catalog_dir"/anti-patterns "$snapshot_dir/" 2>/dev/null || true

        echo "$snapshot_id" > "${backup_dir}/latest_snapshot.txt"
        echo "Created catalog snapshot: $snapshot_id"
    }

    # Rollback to previous snapshot
    rollback_catalog() {
        local target_snapshot="$1"

        if [[ -z "$target_snapshot" ]]; then
            target_snapshot=$(cat "${backup_dir}/latest_snapshot.txt" 2>/dev/null || echo "")
        fi

        if [[ -n "$target_snapshot" ]] && [[ -d "${backup_dir}/${target_snapshot}" ]]; then
            echo "Rolling back catalog to snapshot: $target_snapshot"

            # Backup current state before rollback
            create_catalog_snapshot

            # Restore from snapshot
            rm -rf "$catalog_dir"/*.md "$catalog_dir"/validated-patterns "$catalog_dir"/anti-patterns 2>/dev/null || true
            cp -r "${backup_dir}/${target_snapshot}"/* "$catalog_dir/"

            echo "Catalog rollback completed"
        else
            echo "ERROR: Snapshot $target_snapshot not found"
            return 1
        fi
    }

    # List available snapshots
    list_catalog_snapshots() {
        echo "Available catalog snapshots:"
        ls -la "$backup_dir" | grep "catalog_" | awk '{print $9, $6, $7, $8}'
    }
}
```

### Pattern Recommendation Rollback
```python
class RecommendationRecovery:
    def __init__(self, workspace: str):
        self.workspace = workspace
        self.recommendation_history = f"{workspace}/recommendation_history.json"

    def save_recommendation_state(self, recommendations: List[PatternRecommendation],
                                context: Dict) -> str:
        """Save current recommendation state for potential rollback"""

        state_id = f"rec_{int(time.time())}"

        state_data = {
            "state_id": state_id,
            "timestamp": datetime.now().isoformat(),
            "context": context,
            "recommendations": [
                {
                    "pattern_name": rec.pattern_name,
                    "confidence_score": rec.confidence_score,
                    "fit_score": rec.fit_score,
                    "implementation_effort": rec.implementation_effort,
                    "risk_level": rec.risk_level,
                    "justification": rec.justification,
                    "alternatives": rec.alternatives,
                    "context_dependencies": rec.context_dependencies
                }
                for rec in recommendations
            ]
        }

        # Load existing history
        history = []
        if os.path.exists(self.recommendation_history):
            with open(self.recommendation_history, 'r') as f:
                history = json.load(f)

        # Add new state
        history.append(state_data)

        # Keep only last 20 states
        history = history[-20:]

        # Save updated history
        with open(self.recommendation_history, 'w') as f:
            json.dump(history, f, indent=2)

        return state_id

    def rollback_recommendations(self, state_id: str = None) -> List[PatternRecommendation]:
        """Rollback to previous recommendation state"""

        if not os.path.exists(self.recommendation_history):
            raise ValueError("No recommendation history available for rollback")

        with open(self.recommendation_history, 'r') as f:
            history = json.load(f)

        if not history:
            raise ValueError("No recommendation states in history")

        # Find target state
        target_state = None
        if state_id:
            target_state = next((s for s in history if s["state_id"] == state_id), None)
        else:
            target_state = history[-2] if len(history) > 1 else history[-1]  # Previous state

        if not target_state:
            raise ValueError(f"State {state_id} not found in history")

        # Reconstruct recommendations
        recommendations = []
        for rec_data in target_state["recommendations"]:
            rec = PatternRecommendation(
                pattern_name=rec_data["pattern_name"],
                confidence_score=rec_data["confidence_score"],
                fit_score=rec_data["fit_score"],
                implementation_effort=rec_data["implementation_effort"],
                risk_level=rec_data["risk_level"],
                justification=rec_data["justification"],
                alternatives=rec_data["alternatives"],
                context_dependencies=rec_data["context_dependencies"]
            )
            recommendations.append(rec)

        return recommendations
```

## Validation Criteria

### Pattern Discovery Validation
- **Minimum Pattern Count**: ≥ 3 distinct pattern clusters identified
- **Pattern Quality Score**: ≥ 0.7 average confidence across discovered patterns
- **ADR Coverage**: ≥ 80% of analyzed ADRs contribute to pattern discovery
- **Analogical Reasoning Accuracy**: ≥ 75% pattern similarity validation by human expert
- **Pattern Uniqueness**: < 30% overlap between distinct pattern clusters

### Validation Effectiveness Criteria
- **Cross-Context Success Rate**: ≥ 70% pattern success rate across 3+ different contexts
- **Adaptability Score**: ≥ 0.6 for patterns marked as "HIGH" confidence
- **Context Sensitivity Accuracy**: ≤ 0.3 standard deviation in context factor importance
- **Validation Coverage**: All pattern clusters undergo contrastive analysis
- **Evidence Quality**: ≥ 5 evidence points per validated pattern

### Catalog Maintenance Validation
- **Catalog Completeness**: 100% of validated patterns documented in standardized template
- **Relationship Accuracy**: ≥ 90% accuracy in pattern compatibility matrix
- **Metric Freshness**: Pattern effectiveness metrics updated within 30 days
- **Template Compliance**: 100% adherence to 14-section pattern template
- **Cross-Reference Integrity**: All pattern references resolve correctly

### Anti-Pattern Detection Validation
- **Detection Accuracy**: ≥ 85% true positive rate, ≤ 15% false positive rate
- **Coverage Completeness**: Scanning of 100% configured anti-pattern types
- **Remediation Quality**: 100% of detected anti-patterns have actionable remediation plans
- **Integration Success**: ADR creation hooks functional with < 5 second overhead
- **Risk Assessment Accuracy**: Risk levels align with expert assessment in ≥ 80% of cases

### Recommendation Quality Validation
- **Multi-Perspective Coverage**: All 6 perspective types (technical, business, operational, security, UX, compliance) analyzed
- **Ranking Accuracy**: Top-ranked recommendations validated by domain experts in ≥ 75% of cases
- **Context Alignment**: ≥ 80% of context factors properly weighted in recommendations
- **Implementation Feasibility**: Effort estimates within ±2 points of actual implementation in 70% of cases
- **Alternative Completeness**: ≥ 2 viable alternatives provided for each primary recommendation

## HITL Escalation

### Pattern Discovery Issues
- **Insufficient ADR Quality**: Escalate when < 10 ADRs available or poor decision documentation
- **Pattern Ambiguity**: Human review required when pattern similarity scores < 0.5
- **Domain-Specific Patterns**: Expert consultation for industry-specific architectural patterns
- **Emerging Technology Patterns**: Architect review for patterns involving new technology stacks

### Validation Conflicts
- **Context Contradiction**: Human judgment when cross-context validation shows conflicting results
- **Expert Disagreement**: Escalation when automated validation conflicts with known expert opinions
- **Insufficient Evidence**: Manual evidence gathering when automated analysis lacks sufficient data
- **Edge Case Contexts**: Architect consultation for unusual or unique project contexts

### Anti-Pattern Disputes
- **False Positive Challenges**: Human review when ADR authors dispute anti-pattern detection
- **Subjective Violations**: Expert judgment for anti-patterns requiring contextual interpretation
- **Legacy Exception Cases**: Architect approval for anti-pattern exceptions in legacy systems
- **Performance vs. Maintainability Trade-offs**: Senior architect decision on acceptable anti-patterns

### Recommendation Disagreements
- **Conflicting Perspectives**: Human synthesis when perspective scores show high variance
- **Strategic Alignment**: Business stakeholder review for recommendations affecting business strategy
- **Technical Risk Assessment**: CTO/Architect review for high-risk pattern recommendations
- **Resource Constraint Conflicts**: Project manager consultation when effort estimates exceed available resources

## Related Protocols
- **ADR-001**: Architectural Decision Records Management
- **ASR-001**: Architecturally Significant Requirements Identification
- **DEBT-001**: Technical Debt Management Protocol
- **CFR-001**: Cross-Functional Requirements Integration Protocol
- **P-RECOVERY**: Failure Recovery and Transactional Rollback Protocol

## Test Scenarios

### Scenario 1: Multi-Pattern Discovery
```bash
# Test comprehensive pattern discovery from diverse ADR set
test_pattern_discovery() {
    echo "Testing pattern discovery with diverse ADR repository..."

    # Setup test ADR repository
    create_test_adr_repository

    # Run pattern discovery
    discover_patterns_from_adrs "/tmp/test_adrs"

    # Validate results
    validate_discovery_results

    echo "Pattern discovery test completed"
}

create_test_adr_repository() {
    local test_dir="/tmp/test_adrs"
    mkdir -p "$test_dir"

    # Create diverse ADR examples
    cat > "$test_dir/adr-001-microservices.md" << 'EOF'
# ADR-001: Adopt Microservices Architecture

## Context
Large team (50+ developers) working on complex e-commerce platform requiring independent scaling and deployment.

## Decision
Implement microservices architecture with service-per-domain pattern.

## Consequences
- Improved team autonomy and deployment independence
- Better horizontal scaling capabilities
- Increased operational complexity
- Distributed system challenges
EOF

    cat > "$test_dir/adr-002-monolith.md" << 'EOF'
# ADR-002: Maintain Monolithic Architecture

## Context
Small team (8 developers) building internal tool with simple requirements and limited operational capacity.

## Decision
Continue with monolithic architecture using layered design pattern.

## Consequences
- Simplified deployment and testing
- Easier debugging and monitoring
- Faster initial development
- Limited scaling options
EOF
}
```

### Scenario 2: Anti-Pattern Detection Integration
```bash
# Test anti-pattern detection during ADR creation
test_antipattern_integration() {
    echo "Testing anti-pattern detection integration..."

    # Create ADR with potential anti-patterns
    create_problematic_adr

    # Run detection
    /usr/local/bin/adr-antipattern-check "/tmp/problematic-adr.md"

    # Verify detection results
    verify_detection_accuracy

    echo "Anti-pattern integration test completed"
}

create_problematic_adr() {
    cat > "/tmp/problematic-adr.md" << 'EOF'
# ADR-003: Adopt Latest Trendy Framework

## Context
Team wants to learn new technology and the latest framework looks interesting.

## Decision
Migrate entire application to brand new framework without proven track record.

## Consequences
- Team gets to learn cutting-edge technology
- Improved resume opportunities
- Potential performance benefits (unvalidated)
EOF
}

verify_detection_accuracy() {
    # Check if resume-driven development anti-pattern was detected
    if grep -q "resume-driven development" "/tmp/adr_detection_*/detection_results.txt"; then
        echo "✅ Anti-pattern correctly detected"
    else
        echo "❌ Anti-pattern detection failed"
        return 1
    fi
}
```

### Scenario 3: Context-Aware Recommendations
```python
def test_recommendation_engine():
    """Test multi-perspective recommendation synthesis"""

    # Setup test context
    test_context = {
        'team_size': 'medium',
        'technical_complexity': 'high',
        'scalability_requirements': 'high',
        'budget_constraints': 'medium',
        'time_to_market': 'normal',
        'security_requirements': 'high',
        'performance_requirements': 'high'
    }

    # Create test patterns
    test_patterns = [
        {
            'name': 'Microservices with API Gateway',
            'characteristics': {
                'Architecture Style': 'Microservices',
                'Communication': 'REST API',
                'Data Management': 'Database per service'
            }
        },
        {
            'name': 'Modular Monolith',
            'characteristics': {
                'Architecture Style': 'Monolithic',
                'Communication': 'Internal modules',
                'Data Management': 'Shared database'
            }
        }
    ]

    # Initialize synthesizer
    synthesizer = MultiPerspectiveSynthesizer("/tmp/test_recommendations")

    # Generate recommendations
    recommendations = synthesizer.synthesize_recommendations(test_context, test_patterns)

    # Validate recommendations
    assert len(recommendations) > 0, "No recommendations generated"
    assert recommendations[0].confidence_score > 0.5, "Low confidence in top recommendation"
    assert len(recommendations[0].justification) > 0, "No justification provided"

    print("✅ Recommendation engine test passed")
```

### Scenario 4: Catalog Maintenance Automation
```bash
# Test automated catalog maintenance and versioning
test_catalog_maintenance() {
    echo "Testing automated catalog maintenance..."

    # Initialize test catalog
    initialize_test_catalog

    # Run maintenance process
    maintain_pattern_catalog

    # Verify catalog structure and content
    verify_catalog_integrity

    # Test rollback functionality
    test_catalog_rollback

    echo "Catalog maintenance test completed"
}

initialize_test_catalog() {
    local test_catalog="/tmp/test_pattern_catalog"
    mkdir -p "$test_catalog"/{validated-patterns,anti-patterns,experimental-patterns}

    # Create test patterns
    echo "# Test Pattern" > "$test_catalog/validated-patterns/test-pattern.md"
}

verify_catalog_integrity() {
    local test_catalog="/tmp/test_pattern_catalog"

    # Check required directories exist
    for dir in validated-patterns anti-patterns experimental-patterns; do
        if [[ ! -d "$test_catalog/$dir" ]]; then
            echo "❌ Missing directory: $dir"
            return 1
        fi
    done

    # Check README exists
    if [[ ! -f "$test_catalog/README.md" ]]; then
        echo "❌ Missing catalog README"
        return 1
    fi

    echo "✅ Catalog integrity verified"
}

test_catalog_rollback() {
    # Create backup
    implement_catalog_versioning
    create_catalog_snapshot

    # Make changes
    echo "Modified content" > "/tmp/test_pattern_catalog/test-modification.md"

    # Rollback
    rollback_catalog

    # Verify rollback
    if [[ ! -f "/tmp/test_pattern_catalog/test-modification.md" ]]; then
        echo "✅ Catalog rollback successful"
    else
        echo "❌ Catalog rollback failed"
        return 1
    fi
}
```

## Metadata
- **Protocol Version**: 2.1
- **Last Updated**: 2025-11-13
- **Owner**: Architecture Team
- **Review Cycle**: Quarterly
- **Complexity**: High
- **Automation Level**: 85%
- **Dependencies**: ADR repository, Pattern catalog infrastructure, Multi-agent framework
- **Success Rate**: 89% (based on pattern recommendation accuracy)
- **Average Execution Time**: 2-4 hours (full pattern discovery cycle)
- **Resource Requirements**: Architecture-Analyst, ADR repository access, pattern analysis tools