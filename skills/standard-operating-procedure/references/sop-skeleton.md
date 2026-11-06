---
created: "2026-11-04T19:05:12Z"
updated: "2026-11-04T19:05:12Z"
---

# SOP skeleton and section contents

Fill every bracket. Keep the section numbers and order. Add sections (risk and safety, KPIs, records management) only when the user's regulatory context needs them, after section 6 and before the appendices.

## What each section holds

| Section | Holds | Keep out |
|---|---|---|
| Header | Action-oriented title, unique ID, version, effective date, page count; author, reviewer(s), approver(s), owning department, controlled status. Optional: classification (critical, high-risk), related system or site, confidentiality marking. | Narrative |
| 1. Purpose | One to three sentences: why the SOP exists and what outcome it supports, so a reader can tell whether they are in the right document. | Any procedural detail |
| 2. Scope | Activities, products, systems and locations covered; who it applies to by role or group; exclusions when helpful. | Individuals' names |
| 3. References | Related policies, higher-level procedures, work instructions, forms, checklists, external standards, each with its controlled identifier. | Copied text of those documents |
| 4. Definitions | Specialized terms, acronyms and role labels, defined operationally and briefly; point to the organization's glossary instead of duplicating it. | Terms everyone knows |
| 5. Roles and Responsibilities | Each role that appears in the procedure, with a short summary of its responsibility in this process; for multi-role work, a small RACI table or a swimlane in the appendix. | Step detail |
| 6. Procedure | Numbered steps grouped into phases. Each step: who acts (role), what they do, in what order, and critical parameters (time limits, thresholds, required tools). Separate Note, Caution and Warning lines at risks, decision points and common pitfalls. Point to work instructions or job aids for highly variable detail. | Background, configuration detail, training content |
| 7. Appendices | Flowcharts, swimlane diagrams, RACI table, checklists, forms, templates, screenshots, worked examples. | Mandatory steps not also in section 6 |
| 8. Revision History | Table of version, date, description of change, author, approver. | |

## Fill-in skeleton

```markdown
SOP Title: [Verb + object, e.g. "Receive and Log ..."]
SOP ID: [ORG-PROC-XXX]   Version: [1.0]   Effective Date: [YYYY-MM-DD]
Owner: [Role]   Author: [Role]   Reviewer(s): [Roles]   Approver(s): [Roles]
Owning department: [Department]   Status: [Draft | Controlled]

1. Purpose
   [One to three sentences: why this procedure exists and the outcome it supports.]

2. Scope
   Applies to: [activities, systems, locations].
   Applies to roles: [roles or groups].
   Excludes: [out-of-scope cases, or "No exclusions"].

3. References
   [ID] [Title of related policy, SOP, work instruction, form or standard]

4. Definitions
   [Term]: [operational definition]

5. Roles and Responsibilities
   [Role]: [responsibility in this process, one or two sentences]

6. Procedure
   6.1 [Phase]
       1. [Role] [active verb] [object] [within N minutes / at threshold X].
       2. [Role] records [item] in [system or form].
       3. If [condition], then [Role] [action]; otherwise [Role] [action].
          Caution: [risk and how to avoid it].
       4. [Role] passes [item] to [Role] by [format]; [receiving Role] accepts it
          only when [acceptance criterion].
   6.2 [Next phase]
       1. ...

7. Appendices
   A. Process flowchart or swimlane
   B. RACI table
   C. Checklists and forms
   D. Examples

8. Revision History
   | Version | Date       | Description of Change | Author | Approver |
   |---------|------------|-----------------------|--------|----------|
   | 1.0     | [YYYY-MM-DD] | Initial release     | [Role] | [Role]   |
```
