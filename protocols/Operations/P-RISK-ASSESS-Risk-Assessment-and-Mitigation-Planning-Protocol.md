# P-RISK-ASSESS: Risk Assessment and Mitigation Planning Protocol

**Version**: 1.0
**Last Updated**: 2025-11-14
**Status**: Active
**Owner**: System-Architect

## Objective

Establish comprehensive risk assessment and mitigation planning protocol enabling systematic risk identification, likelihood and impact analysis, risk scoring and prioritization, mitigation strategy development, residual risk evaluation, and continuous risk monitoring ensuring proactive risk management with documented mitigation plans and stakeholder-aligned risk acceptance criteria.

## Trigger

- New project or feature development initiation
- Architectural decision requiring risk analysis
- Security vulnerability assessment
- Compliance audit preparation
- Major system change or deployment
- Incident post-mortem revealing systemic risks
- Quarterly risk review cycle

## Agents

**Primary**: System-Architect
**Supporting**: Security-Auditor, SRE, CISO, Compliance-Officer
**Review**: Engineering-Leadership, Risk-Management-Committee
**Orchestration**: Orchestrator (CORE-COORD-002)

## Prerequisites

- Risk taxonomy and categories defined
- Risk scoring matrix (likelihood × impact)
- Historical incident data
- Threat modeling results (if applicable)
- Stakeholder risk tolerance levels
- Mitigation strategy templates

## Steps

### Step 1: Risk Identification and Cataloging (Estimated Time: 30 minutes)
**Action**: Identify and catalog all potential risks

**Risk Identification**:
```python
from dataclasses import dataclass
from typing import List
from enum import Enum

class RiskCategory(Enum):
    TECHNICAL = "technical"
    SECURITY = "security"
    OPERATIONAL = "operational"
    COMPLIANCE = "compliance"
    FINANCIAL = "financial"
    REPUTATIONAL = "reputational"

class RiskLikelihood(Enum):
    RARE = 1        # <5% probability
    UNLIKELY = 2    # 5-25%
    POSSIBLE = 3    # 25-50%
    LIKELY = 4      # 50-75%
    ALMOST_CERTAIN = 5  # >75%

class RiskImpact(Enum):
    NEGLIGIBLE = 1  # Minimal impact
    MINOR = 2       # Low impact
    MODERATE = 3    # Moderate impact
    MAJOR = 4       # Significant impact
    CATASTROPHIC = 5  # Critical impact

@dataclass
class Risk:
    risk_id: str
    title: str
    description: str
    category: RiskCategory
    likelihood: RiskLikelihood
    impact: RiskImpact
    risk_score: int  # likelihood × impact
    affected_systems: List[str]
    stakeholders: List[str]
    current_controls: List[str]

class RiskIdentifier:
    def identify_risks(self, context: dict) -> List[Risk]:
        """Identify risks systematically"""
        risks = []

        # Technical risks
        risks.extend(self._identify_technical_risks(context))

        # Security risks
        risks.extend(self._identify_security_risks(context))

        # Operational risks
        risks.extend(self._identify_operational_risks(context))

        # Compliance risks
        risks.extend(self._identify_compliance_risks(context))

        return risks

    def _identify_technical_risks(self, context: dict) -> List[Risk]:
        """Identify technical risks"""
        risks = [
            Risk(
                risk_id="TECH-001",
                title="Single Point of Failure",
                description="Database has no failover, creating availability risk",
                category=RiskCategory.TECHNICAL,
                likelihood=RiskLikelihood.POSSIBLE,
                impact=RiskImpact.MAJOR,
                risk_score=12,
                affected_systems=["database", "api"],
                stakeholders=["SRE", "Backend-Engineers"],
                current_controls=["Daily backups"]
            )
        ]
        return risks

    def _identify_security_risks(self, context: dict) -> List[Risk]:
        """Identify security risks"""
        return []

    def _identify_operational_risks(self, context: dict) -> List[Risk]:
        """Identify operational risks"""
        return []

    def _identify_compliance_risks(self, context: dict) -> List[Risk]:
        """Identify compliance risks"""
        return []
```

**Expected Outcome**: Comprehensive risk catalog with all identified risks
**Validation**: All risk categories covered, no major risks missed

### Step 2: Likelihood and Impact Analysis (Estimated Time: 20 minutes)
**Action**: Assess likelihood and impact for each risk

**Risk Scoring**:
```python
class RiskAnalyzer:
    def analyze_risk(self, risk: Risk, historical_data: dict = None) -> Risk:
        """Analyze risk likelihood and impact"""

        # Assess likelihood based on historical data
        if historical_data:
            risk.likelihood = self._assess_likelihood(risk, historical_data)

        # Assess impact based on affected systems
        risk.impact = self._assess_impact(risk)

        # Calculate risk score
        risk.risk_score = risk.likelihood.value * risk.impact.value

        return risk

    def _assess_likelihood(self, risk: Risk, historical_data: dict) -> RiskLikelihood:
        """Assess likelihood from historical data"""
        similar_incidents = historical_data.get('similar_incidents', 0)

        if similar_incidents == 0:
            return RiskLikelihood.RARE
        elif similar_incidents <= 2:
            return RiskLikelihood.UNLIKELY
        elif similar_incidents <= 5:
            return RiskLikelihood.POSSIBLE
        elif similar_incidents <= 10:
            return RiskLikelihood.LIKELY
        else:
            return RiskLikelihood.ALMOST_CERTAIN

    def _assess_impact(self, risk: Risk) -> RiskImpact:
        """Assess impact based on affected systems"""
        critical_systems = ['database', 'authentication', 'payment']

        if any(sys in critical_systems for sys in risk.affected_systems):
            return RiskImpact.CATASTROPHIC

        if len(risk.affected_systems) > 3:
            return RiskImpact.MAJOR

        if len(risk.affected_systems) > 1:
            return RiskImpact.MODERATE

        return RiskImpact.MINOR

    def create_risk_matrix(self, risks: List[Risk]) -> dict:
        """Create risk matrix visualization"""
        matrix = {
            'high_risk': [r for r in risks if r.risk_score >= 15],
            'medium_risk': [r for r in risks if 8 <= r.risk_score < 15],
            'low_risk': [r for r in risks if r.risk_score < 8]
        }
        return matrix
```

**Expected Outcome**: All risks scored with likelihood and impact
**Validation**: Scoring consistent, risk matrix accurate

### Step 3: Risk Prioritization (Estimated Time: 15 minutes)
**Action**: Prioritize risks for mitigation planning

**Prioritization**:
```python
class RiskPrioritizer:
    def prioritize_risks(self, risks: List[Risk]) -> List[Risk]:
        """Prioritize risks by score and strategic factors"""

        # Sort by risk score first
        sorted_risks = sorted(risks, key=lambda r: r.risk_score, reverse=True)

        # Apply strategic adjustments
        for risk in sorted_risks:
            risk.priority_score = self._calculate_priority(risk)

        # Re-sort by priority
        return sorted(sorted_risks, key=lambda r: r.priority_score, reverse=True)

    def _calculate_priority(self, risk: Risk) -> float:
        """Calculate priority with strategic factors"""
        base_score = risk.risk_score

        # Boost for compliance risks
        if risk.category == RiskCategory.COMPLIANCE:
            base_score *= 1.5

        # Boost for security risks
        if risk.category == RiskCategory.SECURITY:
            base_score *= 1.3

        # Boost for risks with no controls
        if not risk.current_controls:
            base_score *= 1.2

        return base_score
```

**Expected Outcome**: Risks prioritized for mitigation effort
**Validation**: High-risk items at top, priorities justified

### Step 4: Mitigation Strategy Development (Estimated Time: 45 minutes)
**Action**: Develop mitigation strategies for each risk

**Mitigation Planning**:
```python
from enum import Enum

class MitigationStrategy(Enum):
    AVOID = "avoid"      # Eliminate risk by not proceeding
    MITIGATE = "mitigate"  # Reduce likelihood or impact
    TRANSFER = "transfer"  # Transfer risk (insurance, outsource)
    ACCEPT = "accept"    # Accept risk with justification

@dataclass
class MitigationPlan:
    risk_id: str
    strategy: MitigationStrategy
    actions: List[str]
    owner: str
    timeline: str
    cost_estimate: float
    expected_risk_reduction: int  # Points reduced from risk score
    residual_risk_score: int

class MitigationPlanner:
    def develop_mitigation(self, risk: Risk) -> MitigationPlan:
        """Develop mitigation plan for risk"""

        # Select strategy based on risk score and feasibility
        strategy = self._select_strategy(risk)

        # Define specific actions
        actions = self._define_actions(risk, strategy)

        # Calculate residual risk
        expected_reduction = self._estimate_reduction(risk, actions)
        residual_score = max(1, risk.risk_score - expected_reduction)

        return MitigationPlan(
            risk_id=risk.risk_id,
            strategy=strategy,
            actions=actions,
            owner=risk.stakeholders[0] if risk.stakeholders else "TBD",
            timeline=self._estimate_timeline(actions),
            cost_estimate=self._estimate_cost(actions),
            expected_risk_reduction=expected_reduction,
            residual_risk_score=residual_score
        )

    def _select_strategy(self, risk: Risk) -> MitigationStrategy:
        """Select appropriate mitigation strategy"""
        if risk.risk_score >= 20:
            # Critical risks: avoid or heavily mitigate
            return MitigationStrategy.MITIGATE
        elif risk.risk_score >= 15:
            return MitigationStrategy.MITIGATE
        elif risk.risk_score >= 10:
            return MitigationStrategy.MITIGATE
        elif risk.category == RiskCategory.FINANCIAL:
            return MitigationStrategy.TRANSFER
        else:
            return MitigationStrategy.ACCEPT

    def _define_actions(self, risk: Risk, strategy: MitigationStrategy) -> List[str]:
        """Define specific mitigation actions"""
        if strategy == MitigationStrategy.MITIGATE:
            # Example mitigation actions
            if "Single Point of Failure" in risk.title:
                return [
                    "Implement database replication",
                    "Configure automatic failover",
                    "Set up monitoring and alerts",
                    "Document failover procedures"
                ]
        return ["Monitor risk", "Review quarterly"]

    def _estimate_reduction(self, risk: Risk, actions: List[str]) -> int:
        """Estimate risk score reduction from actions"""
        # Simplified - actual would be more sophisticated
        if len(actions) >= 4:
            return risk.risk_score // 2
        elif len(actions) >= 2:
            return risk.risk_score // 3
        return 1

    def _estimate_timeline(self, actions: List[str]) -> str:
        """Estimate implementation timeline"""
        if len(actions) >= 4:
            return "3 months"
        elif len(actions) >= 2:
            return "1 month"
        return "2 weeks"

    def _estimate_cost(self, actions: List[str]) -> float:
        """Estimate implementation cost"""
        return len(actions) * 5000  # Simplified
```

**Expected Outcome**: Mitigation plans for all high/medium risks
**Validation**: Plans actionable, owners assigned, timelines realistic

### Step 5: Residual Risk Evaluation (Estimated Time: 15 minutes)
**Action**: Evaluate residual risk after mitigation

**Residual Risk Assessment**:
```python
class ResidualRiskEvaluator:
    def evaluate_residual_risk(self, risk: Risk, mitigation: MitigationPlan) -> dict:
        """Evaluate residual risk after mitigation"""

        residual_risk = {
            'original_score': risk.risk_score,
            'residual_score': mitigation.residual_risk_score,
            'risk_reduction': mitigation.expected_risk_reduction,
            'reduction_percentage': (mitigation.expected_risk_reduction / risk.risk_score) * 100,
            'acceptable': self._is_acceptable(mitigation.residual_risk_score),
            'requires_acceptance': mitigation.residual_score >= 10
        }

        return residual_risk

    def _is_acceptable(self, residual_score: int) -> bool:
        """Check if residual risk is acceptable"""
        # Acceptance criteria
        return residual_score < 10

    def generate_risk_acceptance_document(self, risk: Risk, mitigation: MitigationPlan,
                                         residual: dict) -> str:
        """Generate risk acceptance document"""
        doc = f"""Risk Acceptance Document
======================

Risk ID: {risk.risk_id}
Risk Title: {risk.title}

Original Risk Score: {residual['original_score']}
Residual Risk Score: {residual['residual_score']}
Risk Reduction: {residual['risk_reduction']} points ({residual['reduction_percentage']:.1f}%)

Mitigation Strategy: {mitigation.strategy.value}
Actions Taken: {', '.join(mitigation.actions)}

Residual Risk Assessment:
- Acceptable: {residual['acceptable']}
- Requires Executive Acceptance: {residual['requires_acceptance']}

Approved By: ________________
Date: ________________
"""
        return doc
```

**Expected Outcome**: Residual risks evaluated, acceptance documented
**Validation**: All residual risks within tolerance or explicitly accepted

### Step 6: Risk Monitoring Plan (Estimated Time: 20 minutes)
**Action**: Establish ongoing risk monitoring

**Monitoring Framework**:
```python
@dataclass
class RiskMonitor:
    risk_id: str
    monitoring_frequency: str  # daily, weekly, monthly
    indicators: List[str]
    alert_thresholds: dict
    review_schedule: str

class RiskMonitoringPlanner:
    def create_monitoring_plan(self, risk: Risk, mitigation: MitigationPlan) -> RiskMonitor:
        """Create risk monitoring plan"""

        # Determine monitoring frequency
        frequency = self._determine_frequency(risk)

        # Define key risk indicators
        indicators = self._define_indicators(risk)

        # Set alert thresholds
        thresholds = self._set_thresholds(risk)

        return RiskMonitor(
            risk_id=risk.risk_id,
            monitoring_frequency=frequency,
            indicators=indicators,
            alert_thresholds=thresholds,
            review_schedule="Quarterly"
        )

    def _determine_frequency(self, risk: Risk) -> str:
        """Determine monitoring frequency"""
        if risk.risk_score >= 15:
            return "weekly"
        elif risk.risk_score >= 10:
            return "monthly"
        return "quarterly"

    def _define_indicators(self, risk: Risk) -> List[str]:
        """Define key risk indicators"""
        indicators = []

        if risk.category == RiskCategory.TECHNICAL:
            indicators.extend(["System uptime", "Error rates", "Performance metrics"])
        elif risk.category == RiskCategory.SECURITY:
            indicators.extend(["Security incidents", "Vulnerability counts", "Patch compliance"])

        return indicators

    def _set_thresholds(self, risk: Risk) -> dict:
        """Set alert thresholds"""
        return {
            "uptime": 99.9,
            "error_rate": 0.01,
            "incidents": 0
        }
```

**Expected Outcome**: Monitoring plan for all significant risks
**Validation**: Indicators measurable, thresholds defined, frequency appropriate

### Step 7: Risk Report and Communication (Estimated Time: 30 minutes)
**Action**: Generate comprehensive risk report and communicate to stakeholders

**Expected Outcome**: Risk report distributed, stakeholders informed
**Validation**: Report complete, stakeholders acknowledged

## Expected Outputs

- **Risk Register**: Complete catalog of identified risks
- **Risk Matrix**: Visual representation by likelihood and impact
- **Mitigation Plans**: Detailed plans for each high/medium risk
- **Residual Risk Assessment**: Post-mitigation risk evaluation
- **Risk Acceptance Documents**: Formal acceptance for residual risks
- **Monitoring Plan**: Ongoing risk tracking framework
- **Success Indicators**: All high risks mitigated to <10 score, stakeholder acceptance obtained

## Rollback/Recovery

**Trigger**: Risk materializes, mitigation fails, new risks discovered

**P-RECOVERY Integration**:
1. Activate incident response for materialized risks
2. Implement contingency plans
3. Reassess and update risk register
4. Escalate to Risk Management Committee

**Verification**: Incident contained, risk register updated
**Data Integrity**: Low risk - Assessment only, no system modification

## Failure Handling

### Failure Scenario 1: Critical Risk Missed During Assessment
- **Symptoms**: Incident occurs from unidentified risk
- **Root Cause**: Incomplete risk identification, insufficient expertise
- **Impact**: Critical - Unprepared for incident
- **Resolution**: Post-incident risk reassessment, broaden identification scope
- **Prevention**: Multi-disciplinary risk workshops, historical analysis, external reviews

### Failure Scenario 2: Mitigation Plan Not Implemented
- **Symptoms**: Risk remains at original level, no progress
- **Root Cause**: Insufficient resources, competing priorities, unclear ownership
- **Impact**: High - Organization remains exposed
- **Resolution**: Executive escalation, resource allocation, accountability enforcement
- **Prevention**: Clear ownership, timeline tracking, executive sponsorship

### Failure Scenario 3: Residual Risk Exceeds Tolerance
- **Symptoms**: Post-mitigation risk still unacceptable
- **Root Cause**: Mitigation insufficient, underestimated complexity
- **Impact**: High - Unacceptable risk exposure
- **Resolution**: Additional mitigation measures, risk transfer, or avoid activity
- **Prevention**: Conservative risk estimation, mitigation validation, pilot programs

### Failure Scenario 4: Risk Score Inflation
- **Symptoms**: All risks scored as high, no prioritization value
- **Root Cause**: Overly conservative assessment, lack of calibration
- **Impact**: Medium - Resource misallocation, credibility loss
- **Resolution**: Recalibrate scoring with historical data, peer review
- **Prevention**: Scoring calibration, historical benchmarking, external validation

### Failure Scenario 5: Monitoring Plan Not Executed
- **Symptoms**: Risk indicators not tracked, changes undetected
- **Root Cause**: No accountability, manual process, tool gaps
- **Impact**: High - Risk changes undetected
- **Resolution**: Automate monitoring, assign clear ownership, integrate with incident management
- **Prevention**: Automated dashboards, regular reviews, accountability framework

### Failure Scenario 6: Stakeholder Resistance to Risk Acceptance
- **Symptoms**: Disagreement on residual risk acceptability
- **Root Cause**: Misaligned risk tolerance, unclear acceptance criteria
- **Impact**: Medium - Delayed decisions, project blockers
- **Resolution**: Facilitate risk tolerance discussion, quantify impact, escalate for decision
- **Prevention**: Pre-defined risk tolerance, clear escalation paths, regular calibration

## Validation Criteria

### Quantitative Thresholds
- Risk identification coverage: ≥90% of known risk areas
- High risks mitigated: 100% with plans
- Residual risk within tolerance: ≥90%
- Mitigation plan completion: ≥80% within timeline
- Monitoring plan active: 100% of high/medium risks

### Boolean Checks
- Risks identified: Pass/Fail
- Risks scored: Pass/Fail
- Mitigation plans developed: Pass/Fail
- Residual risks evaluated: Pass/Fail
- Monitoring established: Pass/Fail
- Report generated: Pass/Fail

### Qualitative Assessments
- Risk assessment quality: Risk Management Committee (≥4/5)
- Mitigation plan feasibility: Engineering Leadership (≥4/5)
- Stakeholder confidence: Executives (≥4/5)

**Overall Success**: Thresholds met AND boolean checks pass AND assessments ≥4/5

## HITL Escalation

### Automatic Triggers
- Critical risk (score ≥20) identified
- Residual risk exceeds tolerance after mitigation
- Risk materializes despite mitigation

### Manual Triggers
- Risk acceptance decisions
- Resource allocation for mitigation
- Risk tolerance calibration

### Escalation Procedure
1. **Level 1**: System-Architect risk analysis
2. **Level 2**: Risk Management Committee review
3. **Level 3**: Executive Leadership acceptance
4. **Level 4**: Board of Directors (for catastrophic risks)

## Related Protocols

### Upstream
- **SEC-THREAT-MODEL**: Provides security risk inputs
- **Architectural Decisions**: Trigger risk assessments

### Downstream
- **P-RECOVERY**: Handles materialized risks
- **P-OPS-POSTMORTEM**: Learns from incidents
- **Compliance Reporting**: Documents risk management

### Alternatives
- **Informal Risk Management**: Ad-hoc vs. systematic
- **Insurance Only**: Risk transfer vs. comprehensive management

## Test Scenarios

### Happy Path
#### Scenario 1: New Feature Risk Assessment
- **Setup**: New payment integration feature
- **Execution**: Identify 8 risks, score, develop mitigation for 3 high risks
- **Expected Result**: All high risks mitigated to <10 score, accepted by stakeholders
- **Validation**: Comprehensive assessment, actionable plans, stakeholder approval

### Failure Scenarios
#### Scenario 2: Critical Risk Materialization
- **Setup**: Database failover risk (score 12) not fully mitigated
- **Execution**: Database fails, no automatic failover
- **Expected Result**: Manual failover executed, risk register updated, mitigation accelerated
- **Validation**: Incident response effective, lessons learned incorporated

### Edge Cases
#### Scenario 3: Complex Risk with Multiple Mitigation Paths
- **Setup**: Compliance risk with regulatory ambiguity
- **Execution**: Develop multiple mitigation scenarios, monitor for regulatory clarity
- **Expected Result**: Flexible mitigation approach, adaptive as regulations clarify
- **Validation**: Adaptability demonstrated, compliance maintained

## Metadata

### Version History
| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0 | 2025-10-10 | Initial protocol for Epic 111. Risk assessment with likelihood/impact analysis, mitigation planning, residual risk evaluation, 6 failure scenarios. | System-Architect |

### Review Cycle
- **Frequency**: Quarterly
- **Next Review**: 2026-01-10
- **Reviewers**: System-Architect, CISO, Risk Management Committee

### Compliance Status
- **Framework Standards**: ✅ Compliant
- **Risk Management**: Required
- **Last Validation**: 2025-10-10

## Performance SLOs

- **Risk coverage**: ≥90%
- **High risks mitigated**: 100%
- **Residual risk tolerance**: ≥90%
- **Mitigation completion**: ≥80%
- **Monitoring active**: 100%
