---
created: "2026-11-04T20:07:35Z"
updated: "2026-11-04T20:15:47Z"
---

# Documentation hierarchy and index

## Hierarchy

One docs root in the repository, one folder per documentation type, and a README in each major folder. Folders and their purpose:

```text
docs
  README.md                  main documentation index
  api                        API documentation
    README.md                API overview and reference
    endpoints                one document per endpoint
    schemas                  data model documentation
  architecture               system architecture
    README.md                architecture overview
    ADRs                     architectural decision records
      README.md              ADR overview, status definitions, index, creation steps
      template-ADR.md        ADR template
    diagrams                 architecture diagrams
    one file per component   component documentation
  development                developer guides
    README.md                getting started guide
    setup-guides             environment setup
    testing                  testing strategies
    troubleshooting          common issues
  deployment                 production deployment
    README.md                deployment overview
    environments             environment-specific guides
    monitoring               monitoring and alerting
  security                   security documentation
    README.md                security overview
    configuration-guide.md   security configuration
    SECURITY_NOTES.md        important security considerations
    compliance               compliance documentation
  planning                   project planning
    feature-specifications   feature planning documents
    requirements             business requirements
    roadmaps                 project roadmaps
  reports                    implementation and status reports
    README.md                report framework documentation
    templates                completion and verification report templates
      completion-report-template.md     implementation completion report template
      verification-report-template.md   verification report template
    implementation           feature implementation reports
    verification             verification reports
    metrics                  performance and quality metrics
  guides                     specialized guides
    user-guides              end-user documentation
    admin-guides             administrator guides
    integration-guides       third-party integration guides
  examples                   code examples and tutorials
    README.md                examples overview
    basic-usage              basic usage examples
    advanced-scenarios       advanced use cases
```

Outside the docs root, at the repository root, CONTRIBUTING.md holds the documentation guidelines (the writing rules, the quality and review checklists and the maintenance cadence). When automated reports are asked for, the reports folder also gets the subfolders security, performance and quality.

## Main documentation index

The README at the docs root contains, in this order:

1. Project title and a brief description of the project and its purpose.
2. Quick Start: links to the essential getting-started information.
3. Documentation Structure: one subsection per top-level folder, linked, with the topics it covers:
   - API: endpoint reference, request and response schemas, authentication guide, error handling, rate limiting.
   - Architecture: system architecture overview, component design, data flow diagrams, security architecture, scaling considerations.
   - Development: getting started guide, development workflow, code style guide, testing guidelines, debugging tips.
   - Deployment: deployment options, production configuration, monitoring setup, scaling guidelines, backup procedures.
   - Security: security practices, authentication and authorization, vulnerability management, compliance requirements, incident response.
   - Planning: project planning documents, feature specifications, requirements documentation, project roadmaps.
   - Reports: implementation reports, verification reports, performance metrics, quality assessments.
4. Quick Links: getting started, API reference, deployment guide, security notes.
5. Contributing: a link to CONTRIBUTING.md at the repository root, which holds the documentation guidelines.
6. Support: for questions or issues, first check the relevant documentation section, then search existing issues, then open a new issue.
