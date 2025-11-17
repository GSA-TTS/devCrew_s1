# P-AGILE-PRIVACY: Privacy Integration in Agile Development Protocol

**Version**: 1.0
**Last Updated**: 2025-11-17
**Status**: Active
**Owner**: Privacy-Engineer

## Objective

Establish privacy-by-design integration in Agile development protocol enabling privacy requirements in user stories, sprint-level privacy assessments, data flow mapping, consent mechanism validation, privacy testing automation, and GDPR/CCPA compliance ensuring privacy embedded throughout SDLC with minimal friction to development velocity.

## Tool Requirements

- **TOOL-DATA-003** (Privacy Management): Privacy requirement tracking, compliance validation, and data protection enforcement
  - Execute: Privacy requirement management, compliance tracking, data protection validation, consent management, audit trail maintenance
  - Integration: Privacy management platforms, compliance tracking systems, data protection tools, consent management systems
  - Usage: Privacy requirement integration, compliance validation, data protection enforcement, consent tracking

- **TOOL-COLLAB-001** (GitHub Integration): Agile privacy documentation, sprint coordination, and user story management
  - Execute: Privacy user story management, sprint coordination, documentation management, team collaboration, review workflows
  - Integration: CLI commands (gh, git), API calls, repository operations, documentation management, collaboration workflows, Agile tools
  - Usage: Agile privacy coordination, user story management, sprint documentation, team collaboration

- **TOOL-TEST-001** (Load Testing): Privacy testing automation, compliance validation, and consent mechanism testing
  - Execute: Privacy testing automation, consent mechanism validation, compliance testing, data flow testing, privacy regression testing
  - Integration: Testing frameworks, privacy testing tools, compliance validation systems, automated testing platforms
  - Usage: Privacy testing automation, compliance validation, consent testing, privacy quality assurance

- **TOOL-SEC-011** (Compliance): Privacy compliance validation, regulatory alignment, and audit trail management
  - Execute: Privacy compliance validation, regulatory requirement checking, audit trail maintenance, governance enforcement
  - Integration: Privacy frameworks (GDPR, CCPA, PIPEDA), compliance systems, audit platforms, regulatory tools
  - Usage: Privacy compliance validation, regulatory compliance, audit preparation, governance enforcement

## Trigger

- Sprint planning with features handling personal data
- User story creation involving data collection/processing
- Privacy Impact Assessment (PIA) requirement
- New data flow or integration
- Compliance requirement (GDPR, CCPA, HIPAA)
- Privacy incident requiring process improvement

## Agents

**Primary**: Privacy-Engineer
**Supporting**: Backend-Engineer, Product-Owner, QA-Tester, Security-Auditor
**Review**: CISO, Legal, Compliance-Officer
**Orchestration**: Orchestrator (CORE-COORD-002)

## Prerequisites

- Privacy requirements framework
- Data classification taxonomy
- Consent management system
- Privacy testing tools
- GDPR/CCPA compliance checklist
- Data flow mapping tools

## Steps

### Step 1: Privacy Requirements in User Stories (Estimated Time: 15 minutes per story)
**Action**: Embed privacy requirements in user story acceptance criteria

**Privacy Story Template**:
```markdown
## User Story with Privacy Requirements

**As a** [user role]
**I want** [functionality]
**So that** [business value]

### Privacy Considerations
- **Data Collected**: [List personal data fields]
- **Data Classification**: [Public/Internal/Confidential/Restricted]
- **Legal Basis**: [Consent/Contract/Legitimate Interest/Legal Obligation]
- **Retention Period**: [Duration and deletion criteria]
- **Data Sharing**: [Third parties, purpose, safeguards]
- **User Rights**: [Access/Rectification/Erasure/Portability]

### Privacy Acceptance Criteria
- [ ] Explicit consent obtained before data collection
- [ ] Privacy notice displayed and acknowledged
- [ ] Data minimization applied (only necessary fields)
- [ ] Encryption at rest and in transit
- [ ] User can access/export their data
- [ ] User can request deletion
- [ ] Audit log for data access
- [ ] Third-party processors have DPA

### Privacy Testing Scenarios
- Consent flow validation
- Data deletion verification
- Export functionality test
- Privacy notice display
```

**Expected Outcome**: User stories include privacy requirements
**Validation**: All data-handling stories have privacy criteria

### Step 2: Sprint-Level Privacy Assessment (Estimated Time: 30 minutes per sprint)
**Action**: Conduct privacy assessment during sprint planning

**Sprint Privacy Checklist**:
```python
from dataclasses import dataclass
from typing import List
from enum import Enum

class PrivacyRisk(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class SprintPrivacyAssessment:
    sprint_id: str
    stories_reviewed: int
    high_risk_stories: List[str]
    privacy_risks_identified: List[dict]
    mitigation_required: bool
    pia_required: bool
    compliance_impact: str

class SprintPrivacyAssessor:
    def assess_sprint(self, user_stories: List[dict]) -> SprintPrivacyAssessment:
        """Assess privacy implications of sprint"""

        high_risk_stories = []
        privacy_risks = []

        for story in user_stories:
            risk_level = self._assess_story_risk(story)

            if risk_level in [PrivacyRisk.HIGH, PrivacyRisk.CRITICAL]:
                high_risk_stories.append(story['id'])
                privacy_risks.append({
                    'story_id': story['id'],
                    'risk': risk_level.value,
                    'description': self._describe_risk(story)
                })

        # Determine if PIA required
        pia_required = len(high_risk_stories) > 0 or self._involves_new_processing(user_stories)

        return SprintPrivacyAssessment(
            sprint_id="sprint_123",
            stories_reviewed=len(user_stories),
            high_risk_stories=high_risk_stories,
            privacy_risks_identified=privacy_risks,
            mitigation_required=len(privacy_risks) > 0,
            pia_required=pia_required,
            compliance_impact="GDPR Article 35" if pia_required else "None"
        )

    def _assess_story_risk(self, story: dict) -> PrivacyRisk:
        """Assess privacy risk of single story"""
        data_types = story.get('data_collected', [])

        # High-risk data types
        sensitive_data = ['health', 'biometric', 'genetic', 'children', 'criminal']
        if any(dt in data_types for dt in sensitive_data):
            return PrivacyRisk.CRITICAL

        # Medium-risk: PII
        if any(dt in data_types for dt in ['email', 'phone', 'address', 'ssn']):
            return PrivacyRisk.MEDIUM

        return PrivacyRisk.LOW

    def _involves_new_processing(self, stories: List[dict]) -> bool:
        """Check if sprint involves new data processing"""
        for story in stories:
            if story.get('new_data_processing', False):
                return True
        return False

    def _describe_risk(self, story: dict) -> str:
        """Describe identified privacy risk"""
        return f"Story involves sensitive data: {story.get('data_collected', [])}"
```

**Expected Outcome**: Privacy risks identified early in sprint
**Validation**: High-risk stories flagged, PIA triggered if needed

### Step 3: Data Flow Mapping (Estimated Time: 20 minutes)
**Action**: Map data flows for features in sprint

**Data Flow Documentation**:
```python
@dataclass
class DataFlow:
    flow_id: str
    source: str
    destination: str
    data_elements: List[str]
    processing_purpose: str
    legal_basis: str
    encryption: bool
    third_party: bool
    cross_border: bool
    retention_days: int

class DataFlowMapper:
    def map_flows(self, feature: dict) -> List[DataFlow]:
        """Map data flows for feature"""
        flows = []

        # Example: User registration flow
        flows.append(DataFlow(
            flow_id="FLOW-001",
            source="User Browser",
            destination="API Server",
            data_elements=["email", "password", "name"],
            processing_purpose="Account creation",
            legal_basis="Contract",
            encryption=True,
            third_party=False,
            cross_border=False,
            retention_days=365
        ))

        flows.append(DataFlow(
            flow_id="FLOW-002",
            source="API Server",
            destination="Database",
            data_elements=["email", "password_hash", "name"],
            processing_purpose="Data storage",
            legal_basis="Contract",
            encryption=True,
            third_party=False,
            cross_border=False,
            retention_days=365
        ))

        return flows

    def generate_flow_diagram(self, flows: List[DataFlow]) -> str:
        """Generate ASCII flow diagram"""
        diagram = "Data Flow Diagram:\n"
        for flow in flows:
            diagram += f"{flow.source} -> {flow.destination}: {', '.join(flow.data_elements)}\n"
        return diagram
```

**Expected Outcome**: Data flows documented and visualized
**Validation**: All personal data flows mapped, cross-border transfers identified

### Step 4: Consent Mechanism Validation (Estimated Time: 15 minutes)
**Action**: Validate consent implementation meets legal requirements

**Consent Validation**:
```python
class ConsentValidator:
    def validate_consent_implementation(self, consent_config: dict) -> dict:
        """Validate consent mechanism compliance"""

        validation_results = {
            'compliant': True,
            'issues': []
        }

        # GDPR Requirements
        if not consent_config.get('explicit', False):
            validation_results['issues'].append("Consent must be explicit (GDPR Article 7)")
            validation_results['compliant'] = False

        if not consent_config.get('freely_given', False):
            validation_results['issues'].append("Consent must be freely given")
            validation_results['compliant'] = False

        if not consent_config.get('specific', False):
            validation_results['issues'].append("Consent must be specific to purpose")
            validation_results['compliant'] = False

        if not consent_config.get('informed', False):
            validation_results['issues'].append("Consent must be informed (privacy notice)")
            validation_results['compliant'] = False

        if not consent_config.get('withdrawable', False):
            validation_results['issues'].append("Consent must be easily withdrawable")
            validation_results['compliant'] = False

        # Check for pre-ticked boxes (prohibited)
        if consent_config.get('pre_ticked', False):
            validation_results['issues'].append("Pre-ticked consent boxes prohibited")
            validation_results['compliant'] = False

        # Check consent record keeping
        if not consent_config.get('records_maintained', False):
            validation_results['issues'].append("Must maintain consent records (GDPR Article 7.1)")
            validation_results['compliant'] = False

        return validation_results
```

**Expected Outcome**: Consent mechanisms validated for compliance
**Validation**: All consent requirements met, issues identified

### Step 5: Privacy Testing Automation (Estimated Time: 30 minutes)
**Action**: Implement automated privacy tests in CI/CD

**Privacy Test Suite**:
```python
import pytest

class PrivacyTestSuite:
    """Automated privacy tests"""

    def test_data_encryption_at_rest(self, database):
        """Verify sensitive data encrypted in database"""
        user_record = database.query("SELECT password, ssn FROM users LIMIT 1")

        # Password should be hashed
        assert not user_record['password'].startswith('plain_'), "Password not encrypted"

        # SSN should be encrypted
        assert self._is_encrypted(user_record['ssn']), "SSN not encrypted"

    def test_data_minimization(self, api_response):
        """Verify only necessary data returned"""
        # Check API doesn't return sensitive fields unnecessarily
        assert 'ssn' not in api_response, "SSN should not be in API response"
        assert 'password' not in api_response, "Password should never be in response"

    def test_consent_required_before_collection(self, user_session):
        """Verify consent obtained before data collection"""
        # Attempt to collect data without consent
        response = user_session.post('/api/profile', data={'email': 'test@example.com'})

        assert response.status_code == 403, "Should reject without consent"
        assert 'consent required' in response.json()['error'].lower()

    def test_user_data_deletion(self, database, user_id):
        """Verify user data fully deleted on request"""
        # Trigger deletion
        response = self.api_client.delete(f'/api/users/{user_id}')
        assert response.status_code == 200

        # Verify deletion
        user_data = database.query(f"SELECT * FROM users WHERE id = {user_id}")
        assert len(user_data) == 0, "User data not deleted"

        # Check related tables
        profile_data = database.query(f"SELECT * FROM profiles WHERE user_id = {user_id}")
        assert len(profile_data) == 0, "Profile data not deleted"

    def test_data_export_functionality(self, user_id):
        """Verify user can export their data (GDPR Article 20)"""
        response = self.api_client.get(f'/api/users/{user_id}/export')

        assert response.status_code == 200
        assert response.headers['Content-Type'] == 'application/json'

        exported_data = response.json()
        assert 'email' in exported_data
        assert 'profile' in exported_data

    def test_privacy_notice_displayed(self, browser):
        """Verify privacy notice shown during registration"""
        browser.visit('/register')

        assert browser.is_element_present_by_id('privacy-notice'), "Privacy notice not displayed"
        assert browser.is_element_present_by_id('consent-checkbox'), "Consent checkbox missing"

    def _is_encrypted(self, value: str) -> bool:
        """Check if value appears encrypted"""
        # Simplified check
        return len(value) > 20 and not value.isalnum()
```

**Expected Outcome**: Privacy tests automated in CI/CD
**Validation**: Tests pass, privacy violations caught automatically

### Step 6: GDPR/CCPA Compliance Validation (Estimated Time: 20 minutes)
**Action**: Validate sprint deliverables against compliance requirements

**Compliance Checklist**:
```python
class ComplianceValidator:
    def validate_gdpr_compliance(self, feature: dict) -> dict:
        """Validate GDPR compliance"""

        compliance = {
            'articles': {},
            'compliant': True
        }

        # Article 5: Principles
        compliance['articles']['Article 5'] = self._check_principles(feature)

        # Article 6: Legal basis
        compliance['articles']['Article 6'] = self._check_legal_basis(feature)

        # Article 7: Consent
        if feature.get('legal_basis') == 'consent':
            compliance['articles']['Article 7'] = self._check_consent(feature)

        # Article 15-20: Data subject rights
        compliance['articles']['Articles 15-20'] = self._check_subject_rights(feature)

        # Article 25: Privacy by design
        compliance['articles']['Article 25'] = self._check_privacy_by_design(feature)

        # Article 32: Security
        compliance['articles']['Article 32'] = self._check_security(feature)

        # Overall compliance
        compliance['compliant'] = all(a['compliant'] for a in compliance['articles'].values())

        return compliance

    def _check_principles(self, feature: dict) -> dict:
        """Check GDPR principles (Article 5)"""
        return {
            'compliant': feature.get('data_minimization', False) and
                        feature.get('purpose_limitation', False),
            'notes': 'Data minimization and purpose limitation verified'
        }

    def _check_legal_basis(self, feature: dict) -> dict:
        """Check legal basis (Article 6)"""
        valid_bases = ['consent', 'contract', 'legal_obligation', 'vital_interest', 'public_task', 'legitimate_interest']
        return {
            'compliant': feature.get('legal_basis') in valid_bases,
            'notes': f"Legal basis: {feature.get('legal_basis', 'NOT SPECIFIED')}"
        }

    def _check_consent(self, feature: dict) -> dict:
        """Check consent requirements (Article 7)"""
        return {
            'compliant': feature.get('explicit_consent', False),
            'notes': 'Explicit consent mechanism verified'
        }

    def _check_subject_rights(self, feature: dict) -> dict:
        """Check data subject rights implementation"""
        rights = ['access', 'rectification', 'erasure', 'portability', 'objection']
        implemented = [r for r in rights if feature.get(f'right_{r}', False)]

        return {
            'compliant': len(implemented) == len(rights),
            'notes': f"Implemented: {', '.join(implemented)}"
        }

    def _check_privacy_by_design(self, feature: dict) -> dict:
        """Check privacy by design implementation"""
        return {
            'compliant': feature.get('privacy_by_design', False),
            'notes': 'Privacy considerations in design phase'
        }

    def _check_security(self, feature: dict) -> dict:
        """Check security measures (Article 32)"""
        return {
            'compliant': feature.get('encryption', False) and feature.get('access_control', False),
            'notes': 'Encryption and access controls verified'
        }
```

**Expected Outcome**: Compliance validated before sprint completion
**Validation**: All applicable regulations complied with

### Step 7: Privacy Documentation and Sign-off (Estimated Time: 15 minutes)
**Action**: Document privacy decisions and obtain sign-off

**Expected Outcome**: Privacy documentation complete, sign-off obtained
**Validation**: Documentation complete, approvals recorded

## Expected Outputs

- **Privacy-Enhanced User Stories**: Stories with privacy requirements
- **Sprint Privacy Assessment**: Risk evaluation and mitigation plans
- **Data Flow Diagrams**: Visual representation of data movements
- **Consent Validation Report**: Compliance verification
- **Privacy Test Results**: Automated test pass/fail status
- **Compliance Report**: GDPR/CCPA validation results
- **Success Indicators**: 100% user stories privacy-reviewed, all tests pass, compliance verified

## Rollback/Recovery

**Trigger**: Privacy violation discovered, compliance failure, user rights request failure

**P-RECOVERY Integration**:
1. Immediate data processing halt if violation
2. Investigate scope of privacy incident
3. Notify affected users if required (72 hours GDPR)
4. Remediate and re-validate compliance

**Verification**: Violation resolved, compliance restored
**Data Integrity**: Critical - Privacy violations have legal consequences

## Failure Handling

### Failure Scenario 1: Privacy Requirements Omitted from User Story
- **Symptoms**: Feature deployed without privacy controls
- **Root Cause**: Privacy review skipped, incomplete story template
- **Impact**: Critical - Privacy violation, potential fines
- **Resolution**: Emergency privacy review, retroactive controls, incident response
- **Prevention**: Mandatory privacy checklist, automated story validation

### Failure Scenario 2: Consent Mechanism Non-Compliant
- **Symptoms**: Pre-ticked boxes, no withdrawal option
- **Root Cause**: Insufficient legal review, misunderstanding requirements
- **Impact**: High - GDPR violation, user trust loss
- **Resolution**: Fix consent flow immediately, re-obtain valid consent
- **Prevention**: Consent pattern library, legal review automation

### Failure Scenario 3: Data Deletion Incomplete
- **Symptoms**: User data remains after deletion request
- **Root Cause**: Missing database tables, backup retention, third-party sync failure
- **Impact**: Critical - GDPR Article 17 violation
- **Resolution**: Complete deletion, verify across all systems
- **Prevention**: Comprehensive deletion testing, cascade deletes, third-party coordination

### Failure Scenario 4: Cross-Border Transfer Without Safeguards
- **Symptoms**: EU data transferred to US without Standard Contractual Clauses
- **Root Cause**: Data flow not identified, inadequate transfer mechanism
- **Impact**: Critical - GDPR Chapter V violation, potential data processing ban
- **Resolution**: Halt transfers, implement SCCs or alternative mechanism
- **Prevention**: Data flow mapping, transfer impact assessment

### Failure Scenario 5: Privacy Tests Passing but Actual Violation
- **Symptoms**: Privacy tests pass but real privacy issue exists
- **Root Cause**: Insufficient test coverage, test blind spots
- **Impact**: High - False sense of security, violations undetected
- **Resolution**: Expand test coverage, manual privacy audit
- **Prevention**: Comprehensive test scenarios, periodic manual audits

### Failure Scenario 6: Sprint Delayed Due to Privacy Issues
- **Symptoms**: Sprint cannot complete until privacy fixes applied
- **Root Cause**: Privacy requirements discovered late, underestimated effort
- **Impact**: Medium - Development velocity reduced, deadlines missed
- **Resolution**: Extend sprint, prioritize privacy fixes
- **Prevention**: Early privacy review, accurate effort estimation, privacy capacity planning

## Validation Criteria

### Quantitative Thresholds
- User stories with privacy review: 100%
- Privacy tests passed: 100%
- Compliance requirements met: 100%
- Data flows documented: 100%
- Consent mechanisms validated: 100%

### Boolean Checks
- Privacy requirements in stories: Pass/Fail
- Sprint privacy assessment completed: Pass/Fail
- Data flows mapped: Pass/Fail
- Consent validated: Pass/Fail
- Privacy tests automated: Pass/Fail
- Compliance verified: Pass/Fail

### Qualitative Assessments
- Privacy integration smoothness: Development team (≥4/5)
- Compliance confidence: Legal team (≥4/5)
- User trust: Privacy advocates (≥4/5)

**Overall Success**: Thresholds met AND boolean checks pass AND assessments ≥4/5

## HITL Escalation

### Automatic Triggers
- High-risk story identified
- Privacy test failure
- Compliance violation detected

### Manual Triggers
- PIA requirement determination
- Legal basis selection
- Cross-border transfer approval

### Escalation Procedure
1. **Level 1**: Privacy-Engineer review and guidance
2. **Level 2**: Legal team for complex compliance questions
3. **Level 3**: CISO for risk acceptance decisions
4. **Level 4**: DPO for regulatory reporting

## Related Protocols

### Upstream
- **Product Requirements**: Define features requiring privacy review
- **User Story Creation**: Triggers privacy requirement addition

### Downstream
- **P-QGATE**: Includes privacy tests in quality gates
- **P-DEVSECOPS**: Integrates privacy in security pipeline
- **Incident Response**: Handles privacy violations

### Alternatives
- **Waterfall Privacy**: Big upfront PIA vs. sprint-level
- **Post-Development Review**: Reactive vs. proactive privacy

## Test Scenarios

### Happy Path
#### Scenario 1: Sprint with Privacy-Compliant Feature
- **Setup**: User registration feature with consent, encryption, data minimization
- **Execution**: Privacy review in planning, automated tests in CI/CD
- **Expected Result**: All privacy tests pass, GDPR compliance verified, feature deployed
- **Validation**: No privacy issues, compliant deployment

### Failure Scenarios
#### Scenario 2: Privacy Test Failure Blocks Deployment
- **Setup**: Feature missing data deletion capability
- **Execution**: Privacy test fails in CI/CD
- **Expected Result**: Deployment blocked, deletion capability added, retested successfully
- **Validation**: Privacy violation prevented, compliant after fix

### Edge Cases
#### Scenario 3: PIA Required for High-Risk Feature
- **Setup**: Health data processing feature (GDPR Article 35)
- **Execution**: Sprint assessment triggers PIA, completed before sprint end
- **Expected Result**: PIA completed, risks mitigated, DPO consulted, feature approved
- **Validation**: High-risk processing properly assessed and approved

## Metadata

### Version History
| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0 | 2025-10-10 | Initial protocol for Epic 111. Privacy-by-design in Agile with sprint assessments, consent validation, automated testing, 6 failure scenarios. | Privacy-Engineer |

### Review Cycle
- **Frequency**: Quarterly
- **Next Review**: 2026-01-10
- **Reviewers**: Privacy-Engineer, Legal, CISO, DPO

### Compliance Status
- **Framework Standards**: ✅ Compliant
- **Privacy Integration**: Required
- **Last Validation**: 2025-10-10

## Performance SLOs

- **User stories privacy-reviewed**: 100%
- **Privacy tests passed**: 100%
- **Compliance requirements met**: 100%
- **Data flows documented**: 100%
- **Consent mechanisms validated**: 100%
