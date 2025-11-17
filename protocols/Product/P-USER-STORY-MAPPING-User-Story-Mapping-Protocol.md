# USER-STORY-MAP-001: User Story Mapping Protocol

**Version**: 1.0
**Last Updated**: 2025-11-17
**Status**: Active
**Owner**: Product-Owner

## Objective

Transform user stories into cohesive narrative flows organized by user journey phases, providing visual storytelling that reveals gaps, dependencies, and prioritization opportunities for epic-level feature development.

## Tool Requirements

- **TOOL-PM-001** (Project Management): User story management, backlog integration, epic coordination, and story prioritization
  - Execute: User story management, backlog integration, epic coordination, story prioritization, dependency tracking
  - Integration: Project management platforms, backlog systems, story tracking tools, epic management, prioritization frameworks
  - Usage: Story mapping coordination, backlog management, epic planning, story prioritization, dependency management

- **TOOL-COLLAB-001** (GitHub Integration): Story documentation, mapping artifact management, and team collaboration
  - Execute: Story documentation, mapping artifacts, team collaboration, version control, documentation management
  - Integration: CLI commands (gh, git), API calls, repository operations, documentation systems, collaboration workflows
  - Usage: Story mapping documentation, team coordination, version control, artifact management, collaboration tracking

- **TOOL-UX-001** (Design Research): User journey validation, persona integration, and experience mapping
  - Execute: User journey validation, persona integration, experience mapping, journey analysis, user research integration
  - Integration: UX research platforms, journey mapping tools, persona management, experience validation, design systems
  - Usage: Journey validation, persona coordination, experience mapping, user research integration, design validation

- **TOOL-DATA-002** (Statistical Analysis): Story analytics, journey metrics, and mapping validation
  - Execute: Story analytics, journey metrics calculation, mapping validation, priority analysis, effectiveness measurement
  - Integration: Analytics platforms, metrics calculation, validation frameworks, priority analysis tools
  - Usage: Story mapping analytics, journey effectiveness measurement, priority validation, mapping optimization

## Trigger

- Epic planning session initiated (new feature development)
- Product-Owner completes epic definition requiring story breakdown
- STRAT-PRIO-001 identifies high-priority epic needing detailed user journey mapping
- Cross-functional team requests user story visualization for sprint planning
- Stakeholder feedback (FEEDBACK-INGEST-001) suggests user journey gaps
- UX research findings require story mapping integration

## Agents

- **Primary**: Product-Owner
- **Supporting**: UX-Researcher (journey validation), Business-Analyst (user persona insights)
- **Review**: Development Team (feasibility), QA-Tester (acceptance criteria validation)

## Prerequisites

- Epic defined with clear user value proposition
- User stories available in backlog via **TOOL-PM-001** (`/docs/product/backlog/backlog_{{sprint_id}}.yaml`)
- User personas documented via **TOOL-UX-001** (`/docs/product/personas/persona_{{type}}.yaml`)
- User journey phases defined (Discovery, Engagement, Activation, Retention, Advocacy)
- Acceptance criteria standards established
- Story mapping template available

## Steps

### Step 1: Load and Analyze User Stories (Estimated Time: 15m)
**Action**:
- Read user stories from `/docs/product/backlog/backlog_{{sprint_id}}.yaml`
- Filter stories by target `epic_id` for current mapping session
- Validate story completeness:
  - ✅ User story format: "As a [persona], I want [goal] so that [benefit]"
  - ✅ Acceptance criteria defined (Given/When/Then format)
  - ✅ Story points estimated
  - ✅ Epic_id assigned correctly
  - ✅ Dependencies documented

Extract story data:
```yaml
stories:
  - id: US-001
    epic_id: EPIC-042
    title: "User Registration"
    description: "As a new user, I want to create an account so that I can access personalized features"
    persona: new_user
    story_points: 5
    priority: high
    acceptance_criteria:
      - "Given I am on the registration page, When I enter valid email and password, Then my account is created"
      - "Given I create an account, When I verify my email, Then I can log in successfully"
    dependencies: []
    phase: discovery # Will be refined in Step 2
```

**Expected Outcome**: Complete list of epic stories with metadata
**Validation**: All stories have required fields, acceptance criteria clear, no orphaned stories

### Step 2: Group Stories by User Journey Phases (Estimated Time: 20m)
**Action**:
Map each story to appropriate user journey phase based on user behavior:

**Discovery Phase** (Awareness → Interest):
- User learns about product/feature
- Initial engagement, exploration
- Information gathering, comparison
- Examples: Landing page visit, feature discovery, onboarding start

**Engagement Phase** (Interest → Consideration):
- User interacts with core features
- Trial usage, basic functionality
- Feature exploration, value discovery
- Examples: Account creation, first feature use, tutorial completion

**Activation Phase** (Consideration → Purchase/Adoption):
- User achieves initial value milestone
- Key action completion, "aha moment"
- Commitment demonstration
- Examples: First successful workflow, data import, team invitation

**Retention Phase** (Adoption → Loyalty):
- User establishes usage patterns
- Advanced feature adoption
- Habit formation, routine integration
- Examples: Regular usage, advanced features, customization

**Advocacy Phase** (Loyalty → Evangelism):
- User promotes product to others
- Expansion within organization
- Feedback and feature requests
- Examples: Referrals, reviews, upgrade to paid plan

**Phase Assignment Logic**:
```python
def assign_phase(story):
    keywords = {
        'discovery': ['learn', 'discover', 'explore', 'browse', 'search', 'find'],
        'engagement': ['try', 'create', 'setup', 'configure', 'start', 'begin'],
        'activation': ['complete', 'achieve', 'succeed', 'accomplish', 'finish'],
        'retention': ['manage', 'organize', 'customize', 'optimize', 'improve'],
        'advocacy': ['share', 'invite', 'recommend', 'review', 'upgrade']
    }

    story_text = (story['title'] + ' ' + story['description']).lower()
    phase_scores = {}

    for phase, words in keywords.items():
        score = sum(1 for word in words if word in story_text)
        phase_scores[phase] = score

    return max(phase_scores, key=phase_scores.get)
```

**Expected Outcome**: Stories categorized by journey phase with confidence scoring
**Validation**: Phase assignments make logical sense, no phase completely empty

### Step 3: Order Stories Within Phases (Estimated Time: 15m)
**Action**:
Within each phase, sequence stories by:

1. **Chronological User Flow**: Natural progression of user actions
2. **Dependency Chain**: Prerequisites must come before dependents
3. **Value Priority**: High-impact stories earlier in phase
4. **Implementation Complexity**: Consider technical sequencing

**Ordering Algorithm**:
```python
def order_stories_in_phase(stories):
    # Step 1: Resolve dependencies (topological sort)
    ordered = topological_sort(stories, dependencies)

    # Step 2: Within dependency layers, sort by priority + complexity
    layers = group_by_dependency_level(ordered)

    for layer in layers:
        layer.sort(key=lambda s: (
            -priority_score(s['priority']),  # High priority first
            complexity_score(s['story_points'])  # Low complexity first within priority
        ))

    return flatten(layers)

def priority_score(priority):
    return {'critical': 4, 'high': 3, 'medium': 2, 'low': 1}[priority]

def complexity_score(points):
    return points  # Higher points = more complex
```

**Expected Outcome**: Stories sequenced logically within each phase
**Validation**: Dependencies respected, high-value stories prioritized, flow makes sense

### Step 4: Generate Story Map YAML (Estimated Time: 25m)
**Action**:
Create comprehensive story map file at `/docs/product/user_stories/story_map_{{epic_id}}.yaml`:

```yaml
epic_id: EPIC-042
epic_title: "User Onboarding Experience"
epic_description: "Streamline new user journey from discovery to activation"
owner: Product-Owner
created_date: 2025-10-08
status: draft # draft → reviewed → approved

metadata:
  total_stories: 15
  total_story_points: 89
  estimated_sprints: 3
  target_personas: [new_user, trial_user, converting_user]
  success_metrics:
    - activation_rate: ">40%"
    - time_to_first_value: "<7 days"
    - onboarding_completion: ">80%"

phases:
  - name: Discovery
    description: "User learns about product and explores value proposition"
    story_count: 3
    story_points: 13
    stories:
      - id: US-001
        title: "Landing Page Experience"
        description: "As a visitor, I want to understand the product value so that I can decide if it meets my needs"
        persona: visitor
        story_points: 5
        priority: high
        acceptance_criteria:
          - "Given I visit the landing page, When I read the headline, Then I understand the core value proposition"
          - "Given I'm on the landing page, When I click 'Learn More', Then I see detailed feature explanations"
          - "Given I want to try the product, When I click 'Sign Up', Then I'm directed to registration"
        dependencies: []
        flow_position: 1

      - id: US-002
        title: "Feature Discovery"
        description: "As a visitor, I want to explore key features so that I can assess product fit"
        persona: visitor
        story_points: 3
        priority: medium
        acceptance_criteria:
          - "Given I'm exploring features, When I click on a feature card, Then I see detailed explanation with screenshots"
          - "Given I'm viewing features, When I want to see more, Then I can access interactive demo"
        dependencies: [US-001]
        flow_position: 2

      - id: US-003
        title: "Social Proof Integration"
        description: "As a visitor, I want to see customer testimonials so that I can trust the product quality"
        persona: visitor
        story_points: 5
        priority: medium
        acceptance_criteria:
          - "Given I'm evaluating the product, When I scroll down, Then I see customer testimonials with photos"
          - "Given I see testimonials, When I want more proof, Then I can access case studies"
        dependencies: [US-001]
        flow_position: 3

  - name: Engagement
    description: "User creates account and explores core functionality"
    story_count: 4
    story_points: 21
    stories:
      - id: US-004
        title: "Account Registration"
        description: "As a new user, I want to create an account quickly so that I can start using the product"
        persona: new_user
        story_points: 8
        priority: critical
        acceptance_criteria:
          - "Given I want to register, When I enter email and password, Then my account is created in <30 seconds"
          - "Given I register, When I check my email, Then I receive welcome message with next steps"
          - "Given registration fails, When there's an error, Then I see clear error message and correction steps"
        dependencies: [US-003]
        flow_position: 4

      - id: US-005
        title: "Profile Setup"
        description: "As a new user, I want to complete my profile so that I get personalized experience"
        persona: new_user
        story_points: 5
        priority: high
        acceptance_criteria:
          - "Given I created an account, When I log in first time, Then I'm guided through profile setup"
          - "Given I'm setting up profile, When I skip optional fields, Then I can proceed to main app"
        dependencies: [US-004]
        flow_position: 5

      # ... additional stories for Engagement phase

  - name: Activation
    description: "User achieves first value milestone and core feature success"
    story_count: 4
    story_points: 32
    stories:
      - id: US-009
        title: "First Project Creation"
        description: "As a new user, I want to create my first project so that I experience core product value"
        persona: new_user
        story_points: 13
        priority: critical
        acceptance_criteria:
          - "Given I'm in the app, When I click 'Create Project', Then I'm guided through project setup wizard"
          - "Given I'm creating a project, When I complete required fields, Then my project is created successfully"
          - "Given I created a project, When I want to add content, Then I can easily add first item"
        dependencies: [US-006, US-007]
        flow_position: 9

      # ... additional Activation stories

  - name: Retention
    description: "User establishes regular usage patterns and explores advanced features"
    story_count: 3
    story_points: 18
    stories:
      - id: US-013
        title: "Usage Dashboard"
        description: "As an active user, I want to see my usage patterns so that I can track my progress"
        persona: active_user
        story_points: 8
        priority: medium
        acceptance_criteria:
          - "Given I've used the product for 7+ days, When I visit dashboard, Then I see usage analytics"
          - "Given I see my usage, When I want to improve, Then I see personalized recommendations"
        dependencies: [US-009, US-010]
        flow_position: 13

      # ... additional Retention stories

  - name: Advocacy
    description: "User promotes product and expands usage within organization"
    story_count: 1
    story_points: 5
    stories:
      - id: US-015
        title: "Team Invitation"
        description: "As a satisfied user, I want to invite team members so that we can collaborate"
        persona: satisfied_user
        story_points: 5
        priority: low
        acceptance_criteria:
          - "Given I want to collaborate, When I click 'Invite Team', Then I can send email invitations"
          - "Given I invite teammates, When they join, Then they see shared projects automatically"
        dependencies: [US-013]
        flow_position: 15

journey_flow:
  critical_path: [US-001, US-004, US-005, US-009, US-010]
  optional_branches: [US-002, US-003, US-006, US-007, US-008, US-011, US-012, US-013, US-014, US-015]
  drop_off_risks:
    - phase: engagement
      risk: "Complex registration process"
      mitigation: "Simplify form, add social login options"
    - phase: activation
      risk: "First project creation too complex"
      mitigation: "Improve wizard, add templates"

gaps_identified:
  - gap: "No clear path from trial to paid conversion"
    phase: activation
    recommendation: "Add billing/upgrade story in Activation phase"
  - gap: "Missing error recovery flows"
    phase: engagement
    recommendation: "Add error handling stories for common failure points"

dependencies_map:
  US-001: []
  US-002: [US-001]
  US-003: [US-001]
  US-004: [US-003]
  US-005: [US-004]
  # ... full dependency graph

validation_checkpoints:
  - checkpoint: "Discovery Phase Complete"
    criteria: "User understands value proposition, ready to register"
    success_metric: "Landing page conversion >15%"

  - checkpoint: "Engagement Phase Complete"
    criteria: "User has account and completed profile setup"
    success_metric: "Registration to profile completion >90%"

  - checkpoint: "Activation Phase Complete"
    criteria: "User created first project and added content"
    success_metric: "Time to first value <7 days for >70% users"

  - checkpoint: "Retention Phase Complete"
    criteria: "User returns for 3+ sessions, uses advanced features"
    success_metric: "D7 retention >40%, feature adoption >60%"

simulation_scenarios:
  # Generated in Step 5
  scenarios: []
```

**Expected Outcome**: Complete story map with narrative flow and metadata
**Validation**: YAML syntax valid, all stories included, phases logical, dependencies correct

### Step 5: Run Scenario Simulation (Estimated Time: 20m)
**Action**:
Apply Scenario Simulation pattern to validate user journey flows:

**Scenario 1: Happy Path (New User Success)**
```yaml
scenario_id: new_user_success
persona: new_user
description: "New user discovers product, registers, and achieves first value"
steps:
  - step: 1
    story: US-001
    action: "Visit landing page, read value proposition"
    expected_outcome: "User understands product benefit"
    success_criteria: "Time on page >30s, scrolls to features section"

  - step: 2
    story: US-004
    action: "Click 'Sign Up', complete registration form"
    expected_outcome: "Account created successfully"
    success_criteria: "Registration completes in <60s, confirmation email sent"

  - step: 3
    story: US-005
    action: "Complete profile setup, skip optional fields"
    expected_outcome: "Profile created, onboarding progresses"
    success_criteria: "Profile completion >50%, user proceeds to main app"

  - step: 4
    story: US-009
    action: "Create first project using wizard"
    expected_outcome: "Project created with first content item"
    success_criteria: "Project creation time <5 minutes, user adds ≥1 item"

simulation_results:
  completion_probability: 75%
  drop_off_points:
    - step: 2
      drop_off_rate: 15%
      reason: "Registration form too long"
      mitigation: "Simplify to email/password only"
    - step: 4
      drop_off_rate: 10%
      reason: "Project creation complex"
      mitigation: "Add project templates, improve wizard"
  total_time_estimate: "15-25 minutes"
  user_satisfaction_score: 8.2/10
```

**Scenario 2: Drop-off Path (Engagement Failure)**
```yaml
scenario_id: engagement_dropout
persona: hesitant_user
description: "User registers but fails to complete activation"
steps:
  - step: 1
    story: US-001
    action: "Visit landing page, quick browse"
    expected_outcome: "Partial value proposition understanding"
    success_criteria: "Time on page 15-30s"

  - step: 2
    story: US-004
    action: "Register with minimal info"
    expected_outcome: "Account created but no email verification"
    success_criteria: "Registration completes but verification skipped"

  - step: 3
    story: US-005
    action: "Skip profile setup completely"
    expected_outcome: "Incomplete profile, reduced personalization"
    success_criteria: "User clicks 'Skip' on all optional fields"

  - step: 4
    story: US-009
    action: "Attempt project creation, get confused, abandon"
    expected_outcome: "Project creation started but not completed"
    success_criteria: "User spends >10 minutes, exits without saving"

simulation_results:
  completion_probability: 25%
  abandonment_step: 4
  key_failure_points:
    - "No clear guidance in project creation"
    - "Too many options without explanation"
    - "No progress saving, user fears losing work"
  recommended_interventions:
    - "Add contextual help tooltips"
    - "Implement auto-save during project creation"
    - "Provide project templates for quick start"
```

**Scenario 3: Power User Path (Advanced Adoption)**
```yaml
scenario_id: power_user_adoption
persona: experienced_user
description: "User quickly adopts advanced features, invites team"
steps:
  - step: 1
    story: US-001
    action: "Quick landing page scan, immediate sign-up"
    expected_outcome: "Fast value recognition, eager to try"

  - step: 2-4
    story: US-004, US-005, US-009
    action: "Rapid account setup, profile completion, first project"
    expected_outcome: "Efficient onboarding, quick first value"

  - step: 5
    story: US-013
    action: "Explore usage dashboard, analyze patterns"
    expected_outcome: "Advanced feature discovery"

  - step: 6
    story: US-015
    action: "Invite team members, set up collaboration"
    expected_outcome: "Team adoption, viral growth"

simulation_results:
  completion_probability: 90%
  time_to_advocacy: "3-5 days"
  expansion_potential: "High - likely to invite 3-5 team members"
  churn_risk: "Low - high engagement, multiple use cases"
```

**Expected Outcome**: 3+ scenario simulations with success probabilities and interventions
**Validation**: Scenarios cover range of user behaviors, drop-off points identified, improvements suggested

### Step 6: Review and Validate with UX Team (Estimated Time: 15m)
**Action**:
- Save complete story map to git repository
- Create review package for UX-Researcher:
  - Story map YAML
  - Scenario simulation results
  - Gap analysis summary
  - Dependency visualization (if tools available)

```bash
# Commit story map
git add docs/product/user_stories/story_map_{{epic_id}}.yaml
git commit -m "Create user story map for {{epic_title}} ({{total_stories}} stories, {{estimated_sprints}} sprints)"

# Create GitHub issue for review
gh issue create --title "UX Review: User Story Map for {{epic_title}}" \
  --body "Story map created for epic {{epic_id}}: {{epic_title}}

## Summary
- **Total Stories**: {{total_stories}}
- **Story Points**: {{total_story_points}}
- **Estimated Sprints**: {{estimated_sprints}}
- **Target Personas**: {{personas}}

## Key Findings
- **Critical Path**: {{critical_path_stories}}
- **Drop-off Risks**: {{top_risks}}
- **Gaps Identified**: {{gap_count}}

## Next Steps
1. UX review of journey flow and user experience
2. Validate personas and user behavior assumptions
3. Prioritize gap resolution stories
4. Finalize sprint planning based on story sequence

@UX-Researcher please review story map and simulation scenarios. Focus on:
- Journey flow logical progression
- Drop-off risk mitigation strategies
- Missing user stories or acceptance criteria gaps
- Persona alignment with user research findings

**Story Map**: docs/product/user_stories/story_map_{{epic_id}}.yaml" \
  --label "user-stories,ux-review,epic-planning"
```

**Expected Outcome**: UX team notified, story map under review
**Validation**: GitHub issue created, story map accessible, review process initiated

### Step 7: Incorporate UX Feedback and Finalize (Estimated Time: 20m)
**Action**:
- Monitor GitHub issue for UX-Researcher feedback
- Common feedback categories and responses:

**Journey Flow Issues**:
- Feedback: "Discovery to Engagement transition too abrupt"
- Response: Add intermediate stories (email verification, welcome tutorial)
- Update: Modify story sequence, add transition stories

**Missing User Stories**:
- Feedback: "No mobile-specific stories for responsive experience"
- Response: Add mobile variant stories or acceptance criteria
- Update: Expand existing stories or create mobile-specific versions

**Persona Misalignment**:
- Feedback: "Power user persona not represented in Retention phase"
- Response: Add advanced user stories for complex workflows
- Update: Include power user journey branch

**Drop-off Mitigation**:
- Feedback: "Simulation scenarios too optimistic, real drop-off higher"
- Response: Adjust success probabilities, add intervention stories
- Update: Create recovery flow stories for common drop-off points

Finalize story map:
```yaml
# Update story map with UX feedback
version: 1.1
last_updated: 2025-10-10
review_status: approved
ux_reviewer: UX-Researcher-Name
review_date: 2025-10-09

ux_feedback_incorporated:
  - feedback: "Add email verification reminder story"
    action: "Added US-004b: Email Verification Reminder"
    priority: high

  - feedback: "Mobile experience needs specific stories"
    action: "Updated acceptance criteria to include mobile responsive design"
    priority: medium

  - feedback: "Power user path missing advanced workflows"
    action: "Added US-014: Advanced Project Management for power users"
    priority: low

final_validation:
  journey_flow: approved
  persona_alignment: approved
  gap_analysis: complete
  ready_for_sprint_planning: true
```

**Expected Outcome**: Story map finalized with UX approval, ready for development
**Validation**: UX feedback addressed, version updated, approval documented

## Expected Outputs

- **Primary Artifact**: User story map `story_map_{{epic_id}}.yaml`
- **Secondary Artifacts**:
  - Scenario simulation results
  - Gap analysis report
  - Dependency visualization
  - GitHub review issue
  - UX feedback integration summary
- **Success Indicators**:
  - All epic stories organized into logical journey phases
  - Critical path identified with clear sequence
  - Drop-off risks documented with mitigation strategies
  - UX team approval obtained
  - Story map ready for sprint planning

## Failure Handling

### Failure Scenario 1: Stories Don't Fit Journey Phases
- **Symptoms**: Stories don't naturally align with Discovery/Engagement/Activation/Retention/Advocacy phases
- **Root Cause**: Epic scope too broad, stories from multiple user journeys mixed together
- **Impact**: Medium - Confusing story map, unclear priorities
- **Resolution**:
  1. Review epic scope - may need to split into multiple epics
  2. Group stories by distinct user journeys or persona types
  3. Create separate story maps for each journey/persona
  4. Escalate to Product-Owner for epic redefinition if needed
- **Prevention**: Define epic scope clearly before story mapping, align with single user journey

### Failure Scenario 2: Circular Dependencies Detected
- **Symptoms**: Story A depends on B, B depends on C, C depends on A
- **Root Cause**: Stories not properly decomposed, logical dependencies unclear
- **Impact**: High - Cannot sequence stories for development, sprint planning blocked
- **Resolution**:
  1. Draw dependency graph to visualize circular dependencies
  2. Identify root cause story that should break the cycle
  3. Decompose complex stories into smaller, independent pieces
  4. Re-sequence based on true functional dependencies
  5. Update story map with corrected dependencies
- **Prevention**: Review dependencies during story creation, use dependency visualization tools

### Failure Scenario 3: UX Review Identifies Major Journey Gaps
- **Symptoms**: UX-Researcher finds missing critical user stories for successful journey completion
- **Root Cause**: Incomplete requirements gathering, user research gaps
- **Impact**: High - Story map incomplete, user journey fails in real usage
- **Resolution**:
  1. Conduct additional user research to identify missing stories
  2. Add identified gap stories to appropriate journey phases
  3. Re-run scenario simulations with additional stories
  4. Update effort estimates and sprint planning
  5. Document lessons learned for future story mapping
- **Prevention**: Thorough user research before story mapping, include UX team in initial planning

### Failure Scenario 4: Story Points Don't Align with Sprint Capacity
- **Symptoms**: Total story points (89) exceed team capacity for planned sprints (3 sprints × 20 points = 60)
- **Root Cause**: Overoptimistic effort estimates or too many stories for epic scope
- **Impact**: Medium - Sprint planning unrealistic, delivery timeline extended
- **Resolution**:
  1. Re-estimate story points with development team input
  2. Prioritize critical path stories, defer nice-to-have stories
  3. Split large stories (>8 points) into smaller pieces
  4. Extend sprint timeline or reduce epic scope
  5. Update story map with realistic effort estimates
- **Prevention**: Include development team in story point estimation, validate against team velocity

### Failure Scenario 5: Scenario Simulations Show High Drop-off Rates
- **Symptoms**: Simulation predicts <50% user completion rate through activation phase
- **Root Cause**: User journey too complex, too many friction points
- **Impact**: High - Epic unlikely to achieve success metrics, user adoption will be poor
- **Resolution**:
  1. Identify highest-impact drop-off points from simulation
  2. Add intervention stories to reduce friction (help text, tutorials, simplified flows)
  3. Remove or defer non-essential stories that add complexity
  4. Create A/B testing plan (EXPERIMENT-001) to validate journey improvements
  5. Re-run simulations with improved journey
- **Prevention**: Start with minimal viable journey, add complexity gradually based on user feedback

## Rollback/Recovery

**Trigger**: Major UX feedback requiring story map restructure, circular dependencies, scope change

**Standard Approach**: Invoke **P-RECOVERY** protocol for transactional rollback

**P-RECOVERY Integration**:
1. Before Step 4: CreateBranch for story map creation (`story_map_{{epic_id}}_{{timestamp}}`)
2. Execute Steps 4-7 with git checkpoints after each major change
3. On success: MergeBranch commits final story map to main branch
4. On failure: DiscardBranch reverts to previous epic state, no partial story map published
5. P-RECOVERY handles retry logic if UX feedback requires major rework
6. P-RECOVERY escalates to NotifyHuman if epic scope needs fundamental redefinition

**Custom Rollback** (story mapping specific):
1. If UX review rejects story map: Revert to backlog stories, restart mapping with new approach
2. If dependencies impossible to resolve: Escalate to Product-Owner for epic decomposition
3. Archive failed story map as learning artifact, document why approach didn't work
4. Restart story mapping with refined scope or different journey approach

**Verification**: Epic stories remain in backlog, no invalid story map published
**Data Integrity**: Low risk - story mapping is planning activity, doesn't affect production

## Validation Criteria

### Quantitative Thresholds
- Story coverage: 100% of epic stories included in story map
- Journey phases: All 5 phases have ≥1 story (or explicitly documented why phase skipped)
- Dependencies: 0 circular dependencies detected
- Scenario completion: ≥2 simulation scenarios with ≥50% completion probability
- UX review: Response received within 48 hours

### Boolean Checks
- All stories have acceptance criteria: Pass/Fail
- Critical path identified and documented: Pass/Fail
- Gap analysis completed: Pass/Fail
- Dependencies documented and validated: Pass/Fail
- Story map committed to git: Pass/Fail

### Qualitative Assessments
- Journey flow makes logical sense: UX team review
- Persona alignment accurate: User research validation
- Drop-off risks realistic: Historical data comparison
- Story complexity appropriate: Development team feedback

**Overall Success**: All quantitative thresholds met AND UX approval obtained AND development team confirms feasibility

## HITL Escalation

### Automatic Triggers
- Circular dependencies detected that cannot be automatically resolved
- Epic story points exceed team capacity by >50% (indicates scope creep)
- UX review identifies >5 critical missing stories (indicates requirements gap)
- Scenario simulations show <30% completion probability (indicates journey dysfunction)

### Manual Triggers
- UX team requests major story map restructure (journey approach wrong)
- Development team raises feasibility concerns (technical dependencies unclear)
- Stakeholder conflict over story prioritization (business alignment needed)
- Epic scope change during mapping (requirements evolved)

### Escalation Procedure
1. **Level 1 - Self-Recovery**: Re-sequence stories, adjust dependencies, iterate scenario simulations
2. **Level 2 - UX Collaboration**: Work with UX-Researcher to resolve journey issues, validate personas
3. **Level 3 - Human-in-the-Loop**: Escalate to Product-Owner supervisor, convene cross-functional review
4. **Level 4 - Epic Redefinition**: Major scope change requires stakeholder alignment, epic splitting

## Related Protocols

### Upstream (Prerequisites)
- STRAT-PRIO-001: RICE Scoring (identifies high-priority epics for story mapping)
- FEEDBACK-INGEST-001: Customer Feedback (informs user journey understanding)
- User research activities (persona definition, journey research)

### Downstream (Consumers)
- Sprint planning (uses story sequence for sprint backlog creation)
- EXPERIMENT-001: A/B Testing (validates journey assumptions with real users)
- QA-Tester protocols (acceptance criteria inform test case creation)

### Alternatives
- Manual story prioritization: For small epics with obvious sequencing
- User journey mapping tools: For visual-first teams (Miro, Figma journey maps)
- Agile story wall: For co-located teams preferring physical story boards

## Test Scenarios

### Happy Path Scenarios

#### Scenario 1: E-commerce Checkout Epic
- **Setup**: Epic with 12 stories covering shopping cart to order confirmation
- **Execution**: Map stories across Discovery (product browsing) → Activation (checkout completion)
- **Expected Result**: Clear funnel with drop-off mitigation, critical path identified
- **Validation**: Story map shows logical e-commerce flow, payment/shipping stories properly sequenced

#### Scenario 2: Mobile App Onboarding Epic
- **Setup**: Epic with 8 stories for new user mobile experience
- **Execution**: Focus on mobile-specific journey phases and touch interactions
- **Expected Result**: Mobile-optimized story map with responsive design considerations
- **Validation**: Stories include mobile-specific acceptance criteria, touch-friendly interactions

### Failure Scenarios

#### Scenario 3: Circular Dependencies in Social Features
- **Setup**: Social sharing epic where stories have complex interdependencies
- **Execution**: Attempt story mapping, detect dependency cycles
- **Expected Result**: Dependency cycle detected, stories decomposed, mapping retried
- **Validation**: Final story map has linear dependencies, no cycles remain

#### Scenario 4: UX Review Identifies Missing Authentication Stories
- **Setup**: Story map for premium features lacks authentication/authorization stories
- **Execution**: UX review catches security gap, requests additional stories
- **Expected Result**: Authentication stories added to Engagement phase, story map updated
- **Validation**: Complete user journey includes proper authentication flow

### Edge Cases

#### Scenario 5: Epic Scope Too Large for Single Journey
- **Setup**: Epic contains stories for multiple distinct user personas/journeys
- **Execution**: Attempt to map all stories to single journey phases
- **Expected Result**: Phase assignments don't make sense, epic split recommended
- **Validation**: Epic decomposed into multiple focused epics, separate story maps created

## Metadata

### Version History
| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0 | 2025-10-08 | Initial protocol creation, expanded from 26-line stub to full 14-section protocol | Claude Code (Sonnet 4.5) |

### Review Cycle
- **Frequency**: Per epic (story mapping is project-specific, not recurring)
- **Next Review**: After 3 epic completions, evaluate story mapping effectiveness
- **Reviewers**: UX-Researcher, Development Team Lead, Product-Owner supervisor

### Compliance Status
- **Framework Standards**: ✅ Compliant with 14-section template
- **Security Audit**: N/A (planning activity, no sensitive data)
- **Last Validation**: 2025-10-08