---
created: "2026-11-04T20:07:35Z"
updated: "2026-11-04T20:15:47Z"
---

# Decision record and report templates

## ADR folder README

Kept in the ADR folder as README.md. Sections, in order:

1. Overview: the folder holds the project's official architectural decision records; each documents a significant architectural decision with its context, rationale and consequences.
2. Status definitions:
   - Proposed: under consideration and open for discussion.
   - Accepted: approved and to be followed.
   - Deprecated: previously accepted but no longer recommended.
   - Superseded: replaced by a newer ADR.
3. ADR index: a table with the columns ID, Title (linked to the record), Status, Date.
4. Creating a new ADR:
   1. Copy the ADR template.
   2. Use the next sequential number in the file name (ADR-XXX-decision-title).
   3. Set the status to Proposed.
   4. Fill all template sections.
   5. Submit a pull request for team review.
   6. Update the index when the record is accepted.

## ADR template

Kept in the ADR folder as template-ADR.md. Title line: ADR-[XXX]: [Decision Title]. Sections:

- Status: Proposed, Accepted, Deprecated, or Superseded by ADR-XXX.
- Context: the architectural issue and the environment in which the decision is made, with business and technical context.
- Decision: the architecture decision and the rationale for the choice.
- Consequences: Positive Consequences (benefits) and Negative Consequences (drawbacks and risks).
- Alternatives Considered: other viable options and why each was rejected.
- Implementation: required changes to existing systems, timeline considerations, resource requirements, success criteria.
- References: related ADRs, external documentation, relevant issues or discussions.

## Implementation completion report template

Kept in the reports templates folder as completion-report-template.md. Title line: Issue #[XX] Implementation Completion Report, then [Issue Title]. Sections:

- Executive Summary: what was accomplished and the business value delivered.
- Implementation Details: Key Features Implemented (each with description and business value); Technical Approach (architecture decisions made, implementation patterns used, external dependencies added); Files Created/Modified (affected files with a brief description of the changes).
- Quality Assurance Results: Test Coverage (overall coverage, unit tests passing, integration tests passing, critical path coverage); Code Quality Metrics (linting issues, type checking, complexity score, technical debt, each beside the project's target); Security Compliance (security scan results, vulnerability assessment, dependencies audit, compliance requirements as Met, Partial or Not applicable).
- Performance Impact: response time impact, memory usage impact, database query impact, resource utilization, each beside the project's target.
- Deployment Verification: Pre-deployment Checklist (checkboxes: all tests passing, security scans clean, performance benchmarks met, documentation updated, migration scripts tested, rollback plan prepared); Production Deployment (deployment date, deployment method such as blue-green, rolling or direct, downtime against target, rollback capability verified).
- Post-Deployment Validation (checkboxes): health checks passing, monitoring alerts configured, user acceptance testing completed, performance metrics within targets, error rates normal.
- Lessons Learned: What Went Well, Areas for Improvement, Recommendations.
- Appendices: A. Test Results; B. Security Scan Results; C. Performance Benchmarks.
- Footer: Report Generated (date), Reviewed By (name or role), Status (Complete, Pending Review or Approved).

## Verification report template

Kept in the reports templates folder as verification-report-template.md. Title line: Issue #[XX] Verification Report: [Title]. Sections:

- Verification Scope: the report gives evidence that all requirements of the issue have been implemented and tested.
- Requirements Checklist, each requirement a checkbox:
  - Functional Requirements: each with its Evidence and a Status of Verified, Failed or Pending.
  - Non-Functional Requirements: a performance item (the requirement with its target) with its Evidence, an Actual line for the measured value and a Status of Met, Exceeded or Testing; a security item with its Evidence and a Status of Clean, Issues found or Scanning.
- Acceptance Criteria Verification: one scenario per criterion in Given, When, Then form, with Test Evidence and a Result of Pass or Fail.
- Evidence Documentation: Automated Test Results; Manual Verification Steps (action, expected result, Verified or Failed); Screenshots or Visual Evidence.
- Regression Testing (checkboxes): existing functionality unaffected, no new critical or high severity bugs, performance degradation within the project's limit.
- Compliance Verification (checkboxes): coding standards followed, documentation updated, security requirements met, accessibility standards met where applicable, regulatory compliance maintained.
- Risk Assessment: Identified Risks (each with Probability and Impact as Low, Medium or High, and a Mitigation); Risk Mitigation Evidence.
- Deployment Readiness (checkboxes): all verification criteria met, rollback plan tested and documented, monitoring and alerting configured, team trained on the new functionality, documentation published.
- Verification Conclusion: Overall Status (Requirements Met, Requirements Not Met or Pending), Summary, Verified By (name, role, date), Review Status (Pending, Approved or Rejected).
- Next Actions: checkboxes for remaining tasks and follow-up items.

## Report sharing levels

Every generated report is published at one level; a report for a wider audience shows less.

| Level | Audience | Paths | Statistics, violations, time data | Hotspots listed |
|---|---|---|---|---|
| Public | external stakeholders | fully anonymized | none | at most 5 |
| Internal | internal teams | partly anonymized | included | at most 20 |
| Restricted | security teams | not anonymized | included | at most 50 |
| Full | administrators only | not anonymized | included | no limit |

Paths that are not anonymized still have their sensitive parts redacted:

- Names containing auth, password, secret, key, token or credential become [REDACTED].
- production or prod becomes [PROD]; staging or stage becomes [STAGE].
- IPv4 addresses become [IP]; UUIDs become [UUID].

## Automated report types

Generated scan, performance and quality reports are written into the subfolders security, performance and quality of the reports folder (add them to the Part 1 tree), with the date in each file name; coverage reports go where the coverage tool writes its formats:

- Test coverage: HTML for reading, XML for CI integration, JSON for programmatic access (Python: pytest with the coverage plugin).
- Security scans: code security scan, dependency vulnerability scan, static application security testing (Python: bandit, pip-audit and safety, semgrep).
- Performance: load test, API benchmark, memory profile (Python: Locust, a benchmark script, memory_profiler).
- Code quality: type checking, code complexity and maintainability, linting (Python: mypy, radon, flake8, pylint).
