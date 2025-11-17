# P-USER-RESEARCH: User Interview and Research Protocol

## Objective
Define standardized workflow for conducting user research, interviews, and usability studies to inform Framework Phase 1 (Product Discovery & Requirements Engineering) with validated user insights and data-driven requirements.

## Tool Requirements

- **TOOL-DATA-002** (Statistical Analysis): User research data analysis, survey statistics, usability metrics calculation, and insight synthesis
  - Execute: Survey data analysis, statistical significance testing, quantitative research analysis, metrics calculation, trend analysis
  - Integration: Statistical analysis platforms, survey tools, data visualization systems, research analytics, statistical computing tools
  - Usage: Survey analysis, usability metrics, quantitative research validation, statistical testing, research insights generation

- **TOOL-COLLAB-001** (GitHub Integration): Research documentation, artifact management, requirements generation, and stakeholder coordination
  - Execute: Research documentation, artifact storage, requirements tracking, stakeholder collaboration, version control, issue management
  - Integration: CLI commands (gh, git), API calls, repository operations, documentation systems, project management workflows
  - Usage: Research artifact management, requirements documentation, stakeholder coordination, version control, project tracking

- **TOOL-DATA-003** (Privacy Management): Research participant privacy, consent management, and data protection compliance
  - Execute: Consent form validation, participant privacy protection, data anonymization, compliance monitoring, privacy impact assessment
  - Integration: Privacy management platforms, consent systems, data protection tools, anonymization systems, compliance frameworks
  - Usage: Research ethics compliance, participant consent, data privacy, anonymization validation, regulatory compliance

- **TOOL-UX-001** (Design Research): User research facilitation, usability testing coordination, and design validation support
  - Execute: Research session facilitation, usability test coordination, design validation, user feedback collection, research tool integration
  - Integration: User research platforms, usability testing tools, design systems, feedback collection, research coordination systems
  - Usage: Research session management, usability testing, design validation, user feedback analysis, research coordination

## Agent
Primary: Product-Owner
Participants: UX-UI-Designer, Business-Analyst, QA-Tester (usability testing)

## Trigger
- At project inception (Phase 1 start)
- When new feature proposal requires user validation
- During Phase 8 (Post-Launch) for optimization insights
- When user satisfaction metrics decline
- Before major product pivots or redesigns

## Prerequisites
- Research objectives defined (what questions need answering)
- Target user personas identified
- Research budget allocated
- Research tools available via **TOOL-UX-001** (survey platforms, interview scheduling, recording software)
- IRB approval obtained (if academic/regulated research)
- Privacy and consent forms prepared via **TOOL-DATA-003**

## Steps

1. **Research Planning and Scoping**:
   - Define research objectives:
     - **Exploratory**: Understand user needs, pain points, workflows
     - **Evaluative**: Test designs, prototypes, or existing features
     - **Generative**: Identify new opportunities or unmet needs
   - Identify research questions (3-5 key questions to answer)
   - Determine research methods:
     - User interviews (1-on-1, 30-60 minutes)
     - Focus groups (6-10 users, 60-90 minutes)
     - Surveys (quantitative data, N>100)
     - Usability testing (task-based, think-aloud protocol)
     - Field studies (contextual inquiry, shadowing)
   - Define success metrics (e.g., 80% user satisfaction, <5 clicks to complete task)

2. **Participant Recruitment**:
   - Define inclusion/exclusion criteria:
     - Target personas (e.g., "small business owners, 25-50 employees")
     - Demographics (age, location, industry, tech savvy)
     - Behavioral criteria (current product users vs. non-users)
   - Determine sample size:
     - Qualitative (interviews/usability): 5-8 users per persona (80% of issues discovered)
     - Quantitative (surveys): N>100 for statistical significance
   - Recruit participants:
     - Internal channels (existing user base, customer success teams)
     - External channels (UserTesting.com, Respondent.io, social media)
     - Incentives (gift cards, product credits, early access)
   - Screen participants (screening questionnaire to ensure fit)
   - Schedule sessions (use Calendly, Google Calendar, avoid back-to-back)

3. **Research Instrument Preparation**:
   - **For Interviews**: Prepare semi-structured interview guide:
     - Opening (5 min): Build rapport, explain study, obtain consent
     - Background (10 min): User context, current workflows, pain points
     - Core questions (30 min): Dive deep into research objectives
     - Closing (5 min): Thank participant, ask for referrals
   - **For Surveys**: Design survey with validated scales:
     - SUS (System Usability Scale) for usability
     - NPS (Net Promoter Score) for loyalty
     - CSAT (Customer Satisfaction) for satisfaction
     - Custom Likert scales (1-5 or 1-7) for specific attributes
   - **For Usability Testing**: Define test scenarios and tasks:
     - Realistic tasks aligned with user goals
     - Success criteria (task completion, time on task, errors)
     - Think-aloud instructions ("Tell me what you're thinking")
   - Pilot test instruments with 1-2 participants, iterate

4. **Data Collection**:
   - **User Interviews**:
     - Conduct sessions via video call (Zoom, Teams) or in-person
     - Record with consent (audio/video for later analysis)
     - Take notes on key quotes, pain points, feature requests
     - Use probing questions ("Can you tell me more about that?")
     - Avoid leading questions ("Don't you think...?")
   - **Surveys**:
     - Distribute via email, in-app prompts, social media
     - Monitor response rates (target 30%+ for email surveys)
     - Send reminder after 3-5 days for non-responders
   - **Usability Testing**:
     - Observe users completing tasks (screen share or in-person)
     - Record think-aloud commentary
     - Note errors, confusion, task completion time
     - Use post-task questionnaires (SEQ - Single Ease Question)
   - Store data securely (encrypted, GDPR/CCPA compliant)

5. **Data Analysis**:
   - **Qualitative Analysis (Interviews, Usability Tests)**:
     - Transcribe recordings (use Otter.ai, Rev, manual)
     - Code transcripts using thematic analysis:
       - Open coding: Identify recurring concepts
       - Axial coding: Group related concepts into themes
       - Selective coding: Connect themes to research questions
     - Use affinity diagramming (group similar findings)
     - Identify patterns across participants (need 3+ mentions for pattern)
   - **Quantitative Analysis (Surveys)**:
     - Calculate descriptive statistics (mean, median, standard deviation)
     - Segment by user type (e.g., power users vs. casual users)
     - Identify statistically significant differences (t-tests, ANOVA)
     - Visualize data (bar charts, heat maps, scatter plots)
   - Synthesize findings into key insights (3-5 major takeaways)

6. **Insight Synthesis and Prioritization**:
   - Create findings document:
     - Executive summary (1 page: objectives, methods, key findings)
     - Detailed findings (themes, supporting quotes, quantitative data)
     - Recommendations (actionable next steps)
     - Appendices (raw data, transcripts, survey responses)
   - Prioritize insights using RICE framework:
     - Reach: How many users affected?
     - Impact: How much will it improve user experience? (1-5)
     - Confidence: How confident are we? (percentage)
     - Effort: How much work to implement? (person-weeks)
     - Score = (Reach × Impact × Confidence) / Effort
   - Map insights to user pain points and opportunities

7. **Requirements Generation**:
   - Translate insights into product requirements:
     - User stories: "As a [persona], I want [goal] so that [benefit]"
     - Acceptance criteria: Specific, measurable conditions for completion
     - Personas: Update or create personas based on research
     - Journey maps: Visualize user workflows and pain points
   - Validate requirements with stakeholders:
     - Product team (alignment with vision)
     - Engineering team (technical feasibility)
     - Business team (ROI and business goals)
   - Prioritize requirements using MoSCoW:
     - Must have (critical for MVP)
     - Should have (important but not critical)
     - Could have (nice to have)
     - Won't have (out of scope)

8. **Research Report and Presentation**:
   - Create research report document:
     - Title page (project name, date, researchers)
     - Executive summary (1 page)
     - Methodology (research methods, sample size, timeline)
     - Findings (organized by theme, with quotes and data)
     - Recommendations (prioritized, with RICE scores)
     - Next steps (roadmap integration)
   - Present findings to stakeholders:
     - 30-minute presentation (15 slides max)
     - Use storytelling (user quotes, journey maps, personas)
     - Highlight top 3 insights and recommendations
     - Facilitate Q&A and discussion
   - Share artifacts: Report, presentation, raw data (anonymized)

9. **Handoff to Product Development (P-HANDOFF)**:
   - Package research deliverables:
     - Research report (PDF)
     - User stories and acceptance criteria (JIRA/GitHub issues)
     - Updated personas and journey maps
     - Video clips or quotes for reference
   - Hand off to Business-Analyst and System-Architect:
     - Business-Analyst: Translates insights into requirements
     - System-Architect: Considers technical implications
   - Create prd.md (Product Requirements Document) incorporating research findings

10. **Continuous Research Loop**:
    - Archive research for future reference (searchable repository)
    - Identify gaps in knowledge (areas needing more research)
    - Schedule follow-up research (quarterly or after major releases)
    - Track how research insights influenced product decisions
    - Measure impact: Did implementing research-driven features improve metrics?

## Expected Outputs
- Research plan document (objectives, methods, sample size, timeline)
- Recruitment screener and consent forms
- Research instruments (interview guides, surveys, usability test scenarios)
- Raw data (interview transcripts, survey responses, usability test recordings)
- Research report (findings, insights, recommendations, RICE prioritization)
- User stories and acceptance criteria (derived from research)
- Updated personas and journey maps
- Research presentation (stakeholder deck)
- prd.md (Product Requirements Document with research foundation)

## Failure Handling
- **Low Response Rate (<20%)**: Increase incentives, simplify survey, send reminders, extend timeline.
- **Participant No-Shows**: Overbook by 20%, send reminder emails 24 hours before, offer rescheduling.
- **Biased Sample**: Recruit from diverse channels, screen carefully, compare demographics to target.
- **Inconclusive Findings**: Increase sample size, refine research questions, use mixed methods (qual + quant).
- **Conflicting Data**: Segment users, look for patterns by persona, prioritize majority pain points.
- **Stakeholder Rejection**: Provide additional evidence, tie insights to business metrics, facilitate collaborative prioritization.

## Related Protocols
- **P-REQUIREMENTS**: Requirements Engineering (Step 7 feeds into this)
- **P-PERSONA**: Persona Creation (Step 7 updates personas)
- **P-JOURNEY-MAPPING**: User Journey Mapping (Step 7 creates journey maps)
- **P-HANDOFF**: Agent Handoff (Step 9 executes this)
- **QG-PHASE1**: Requirements Approval Quality Gate (validates research-driven requirements)

## Validation Criteria
- Research objectives clearly defined (3-5 key questions)
- Sample size meets method requirements (5-8 for qual, 100+ for quant)
- Data collection instruments validated (pilot tested, no leading questions)
- Qualitative data coded and analyzed (themes identified, 3+ mentions for patterns)
- Quantitative data analyzed with statistics (mean, median, significance tests)
- Findings prioritized using RICE framework
- User stories created from insights (with acceptance criteria)
- Research report completed and presented to stakeholders
- prd.md incorporates research findings
- Handoff to Business-Analyst/System-Architect complete

## Performance SLOs
- Research planning time: <1 week (objectives to recruitment)
- Participant recruitment time: <2 weeks (screening to scheduling)
- Data collection time: <3 weeks (first to last session)
- Data analysis time: <2 weeks (raw data to findings report)
- Stakeholder presentation time: <1 week (report completion to presentation)
- Total research cycle time: <8 weeks (planning to handoff, 95th percentile)
