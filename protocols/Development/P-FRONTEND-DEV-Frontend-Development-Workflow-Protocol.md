# P-FRONTEND-DEV: Frontend Development Workflow Protocol

## Objective
Define standardized workflow for client-side application development, ensuring components meet design specifications, accessibility standards (WCAG 2.1 AA), performance budgets (Lighthouse >90), and follow Test-Driven Development (P-TDD) methodology.

## Tool Requirements

- **TOOL-DESIGN-001** (Design Platform): Design specification access and component development coordination
  - Execute: Design mockup access, design token management, responsive design validation, design system integration
  - Integration: Design platforms (Figma, Sketch, Adobe XD), design system tools, component libraries, design token generators
  - Usage: Design specification review, component design validation, responsive design implementation, design system compliance

- **TOOL-TEST-001** (Load Testing): Frontend testing, accessibility validation, and performance benchmarking
  - Execute: Component testing, accessibility scanning, performance testing, visual regression testing, E2E testing
  - Integration: Testing frameworks (Jest, Vitest, Cypress, Playwright), accessibility tools (axe-core, Pa11y), performance tools (Lighthouse)
  - Usage: TDD implementation, accessibility compliance validation, performance optimization, regression testing

- **TOOL-COLLAB-001** (GitHub Integration): Source code management, API contract integration, and collaboration
  - Execute: Frontend code management, API contract access, design specification tracking, team collaboration
  - Integration: CLI commands (gh, git), API calls, repository operations, project management workflows
  - Usage: Code versioning, API contract integration, design specification management, team coordination

- **TOOL-CICD-001** (Pipeline Platform): Build automation, deployment, and development environment management
  - Execute: Build process automation, deployment pipelines, development server management, package management
  - Integration: Build tools, bundlers, deployment platforms, package managers, development servers
  - Usage: Development workflow automation, build optimization, deployment coordination, environment management

- **TOOL-DEV-003** (API Testing): API integration testing and contract validation
  - Execute: API integration testing, contract validation, mock server management, data flow testing
  - Integration: API testing tools, mock servers, contract testing frameworks, integration testing tools
  - Usage: Backend integration validation, API contract compliance, data flow testing, integration verification

## Agent
Primary: Frontend-Engineer
Participants: UX-UI-Designer, Backend-Engineer, QA-Tester, Code-Reviewer

## Trigger
- After design specifications approved (design-spec.md, Figma mockups)
- During Framework Phase 5 (Core Frontend Development)
- When frontend feature or component is assigned to Frontend-Engineer
- After Backend-Engineer provides API contracts (OpenAPI spec)

## Prerequisites
- UI/UX design mockups approved (Figma links, design specs) accessible via **TOOL-DESIGN-001**
- Design system and component library available (design tokens, style guide) through **TOOL-DESIGN-001**
- API contracts from Backend-Engineer (OpenAPI/Swagger documentation) via **TOOL-COLLAB-001**
- Development environment configured (Node.js, package manager, build tools) using **TOOL-CICD-001**
- Frontend framework selected (React, Vue, Angular, Svelte) with testing infrastructure via **TOOL-TEST-001**
- Source code management and collaboration workflows established through **TOOL-COLLAB-001**
- API testing and integration validation tools configured via **TOOL-DEV-003**
- Design specification access and validation tools operational through **TOOL-DESIGN-001**

## Steps

1. **Design Specification Review**: Frontend-Engineer reviews design requirements:
   - UI mockups (Figma, Sketch, Adobe XD)
   - Component specifications (props, state, behavior)
   - Design tokens (colors, typography, spacing, shadows)
   - Responsive breakpoints (mobile, tablet, desktop)
   - Interaction patterns (animations, transitions, micro-interactions)
   - Accessibility requirements (keyboard navigation, screen reader support, ARIA labels)

2. **API Contract Integration**: Review backend contracts for data integration:
   - OpenAPI/Swagger spec from Backend-Engineer
   - Request/response schemas
   - Authentication requirements (JWT tokens, OAuth flows)
   - Error response formats (4xx, 5xx handling)
   - Real-time data requirements (WebSocket, SSE)

3. **Component Test Creation (P-TDD Step 1 - RED)**:
   - Write failing component tests before implementation:
     - **Render tests**: Component renders without crashing
     - **Prop tests**: Component accepts and displays props correctly
     - **Interaction tests**: User actions (click, input, submit) trigger expected behavior
     - **State tests**: Component state updates correctly
     - **Edge case tests**: Loading states, error states, empty data
   - Use Testing Library, Jest, or Vitest
   - Ensure tests fail (no implementation yet)

4. **Component Implementation (P-TDD Step 2 - GREEN)**:
   - Build component to pass failing tests:
     - **Structure**: JSX/template markup following design mockups
     - **Styling**: CSS/SCSS/Tailwind matching design tokens
     - **State Management**: Local state (useState, ref) or global state (Redux, Zustand, Pinia)
     - **Event Handlers**: Click, input, form submission, keyboard events
     - **API Integration**: Fetch data using API hooks (useQuery, useSWR, Axios)
     - **Accessibility**: ARIA labels, roles, keyboard navigation, focus management
   - Run tests - ensure all pass

5. **Component Refactoring (P-TDD Step 3 - REFACTOR)**:
   - Optimize implementation while keeping tests green:
     - **Performance**: Memoization (useMemo, React.memo), lazy loading, virtualization
     - **Code Quality**: Extract reusable hooks, simplify complex logic, remove duplication
     - **Accessibility**: Improve ARIA semantics, enhance keyboard navigation
     - **Styling**: Apply design system patterns, ensure responsive behavior

6. **Accessibility Audit (WCAG 2.1 AA)**:
   - Run automated accessibility checks:
     - **axe-core**: Scan for WCAG violations (color contrast, ARIA usage, semantic HTML)
     - **Pa11y**: CLI accessibility testing
     - **Lighthouse**: Accessibility score ≥95
   - Manual accessibility testing:
     - Keyboard navigation (Tab, Enter, Escape, Arrow keys)
     - Screen reader testing (VoiceOver, NVDA, JAWS)
     - Focus indicators visible and clear
   - Fix violations before proceeding

7. **Performance Optimization (Core Web Vitals)**:
   - Optimize for performance budgets:
     - **FCP <1.8s**: Minimize critical rendering path, inline critical CSS
     - **LCP <2.5s**: Optimize images (WebP, lazy loading), prioritize above-fold content
     - **CLS <0.1**: Reserve space for dynamic content, avoid layout shifts
     - **Bundle Size**: JS <200KB, CSS <50KB (gzipped)
   - Run Lighthouse audit - Performance score ≥90
   - Implement code splitting for routes (React.lazy, dynamic imports)

8. **Design Fidelity Validation**:
   - Compare implementation with design mockups:
     - **Visual Regression**: Percy, Chromatic, BackstopJS
     - **Pixel Perfection**: Overlay mockup on implementation, verify spacing/typography
     - **Responsive Behavior**: Test all breakpoints (320px, 768px, 1024px, 1440px)
     - **Interactive States**: Hover, focus, active, disabled states match design
   - Obtain UX-UI-Designer approval for design fidelity

9. **API Integration Testing**:
   - Test backend API integration:
     - **Mock Service Worker (MSW)**: Mock API responses for component tests
     - **Loading States**: Verify loading indicators display during API calls
     - **Error Handling**: Test 4xx (validation errors), 5xx (server errors) responses
     - **Data Transformation**: Ensure API response mapped correctly to component state
     - **Optimistic Updates**: Validate optimistic UI updates for mutations

10. **Code Quality Validation**:
    - Run linting and formatting:
      - **ESLint**: Enforce code quality rules, no console.log in production
      - **Prettier**: Auto-format code for consistency
      - **TypeScript**: Type safety (if using TS)
    - Ensure no code smells:
      - Component complexity <200 lines
      - No prop drilling (use Context/Redux for global state)
      - Proper component composition (atomic design principles)

11. **Submit for Quality Gate (QG-PHASE5)**:
    - Package deliverables for QG-PHASE5 validation:
      - Component source code (feature branch)
      - Test suite (≥80% coverage)
      - Lighthouse report (Performance ≥90, Accessibility ≥95)
      - axe-core accessibility audit (0 violations)
      - Bundle size analysis (JS + CSS < 250KB)
      - Design fidelity screenshots/videos
    - Submit to QG-PHASE5 for automated validation
    - If QG-PHASE5 PASS → trigger HITL gate for human approval
    - If QG-PHASE5 FAIL → address feedback and resubmit

12. **Handoff to QA-Tester (P-HANDOFF)**:
    - After QG-PHASE5 HITL approval, hand off to QA-Tester:
      - Component storybook or demo URL
      - Test environment access
      - Component documentation (props, usage, examples)
      - Known limitations or edge cases
    - QA-Tester performs integration testing
    - Address any integration issues found

## Expected Outputs
- Implemented UI component(s) matching design specifications
- Component test suite (≥80% coverage, all tests passing)
- Lighthouse report (Performance ≥90, Accessibility ≥95)
- Accessibility audit report (WCAG 2.1 AA compliance, 0 violations)
- Bundle size analysis (within performance budget)
- Design fidelity validation (UX-UI-Designer approval)
- API integration tests (MSW mocks, error handling)
- Component documentation (storybook, props, usage)
- QG-PHASE5 approval (automated + HITL)

## Failure Handling
- **Design Fidelity Issues**: Return to Step 4 (Component Implementation). Adjust implementation to match design. Re-validate with UX-UI-Designer.
- **Accessibility Violations**: Return to Step 6 (Accessibility Audit). Fix ARIA labels, keyboard navigation, color contrast. Re-run axe-core until 0 violations.
- **Performance Below Budget**: Return to Step 7 (Performance Optimization). Implement lazy loading, code splitting, image optimization. Re-run Lighthouse until ≥90.
- **Test Coverage <80%**: Return to Step 3 (Component Test Creation). Add tests for uncovered code paths. Ensure coverage ≥80%.
- **API Integration Errors**: Return to Step 9 (API Integration Testing). Debug API response handling. Verify contract alignment with Backend-Engineer.
- **QG-PHASE5 Failure**: Review QG-PHASE5 feedback. Address specific issues (tests, accessibility, performance, design). Resubmit for validation.

## Related Protocols
- **P-TDD**: Test-Driven Development (Steps 3-5 follow TDD cycle)
- **P-ACCESSIBILITY**: WCAG Compliance Protocol (Step 6 applies this)
- **P-PERFORMANCE**: Performance Optimization (Step 7 applies this)
- **QG-PHASE5**: Frontend Development Review Quality Gate (Step 11 submits to this)
- **P-HANDOFF**: Agent Handoff Protocol (Step 12 executes this)
- **P-API-CONTRACT**: API Contract Design (provides contracts in Step 2)
- **GH-1**: GitHub Issue Triage (source of frontend tasks)

## Validation Criteria
- Component tests pass with ≥80% coverage
- Lighthouse Performance ≥90, Accessibility ≥95, Best Practices ≥90
- Core Web Vitals: FCP <1.8s, LCP <2.5s, CLS <0.1
- axe-core accessibility audit: 0 violations (WCAG 2.1 AA)
- Bundle size: JS <200KB, CSS <50KB (gzipped)
- Design fidelity validated by UX-UI-Designer
- API integration tested with MSW (loading, error, success states)
- ESLint and Prettier pass (code quality and formatting)
- QG-PHASE5 PASS (automated validation + HITL approval)
- Handoff to QA-Tester complete with documentation

## Performance SLOs
- Component development time: <8 hours per component (95th percentile)
- Test suite execution time: <30 seconds for component tests
- Lighthouse audit time: <2 minutes per component
- QG-PHASE5 submission to HITL approval: <4 hours (during business hours)
