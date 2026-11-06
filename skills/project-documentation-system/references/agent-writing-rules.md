---
created: "2026-11-04T20:07:35Z"
updated: "2026-11-04T20:15:47Z"
---

# Writing rules agents can parse

## Structure for parsability

1. Hierarchical Markdown headings (main topic, subtopic, implementation detail, code example) so that a document chunks by meaning.
2. YAML front matter on each document with these fields: title, type, audience (a list), tags (a list), owner, last_updated, review_cycle.
3. Atomic paragraphs: one concept per paragraph, which also gives better vector embeddings.
4. Complete, copy-pasteable code examples: a full working function with its docstring (arguments and return value), not a fragment.

## Context grounding

1. Explicit links in a relations block: parent, dependsOn (a list), relatesTo (a list, for related issues and ADRs).
2. A Related Documentation section at the end of a document, with relative links to the related guides, ADRs and pages.

## Task specification block for issues

For work tracked as issues, each issue carries a YAML block with these fields:

- schemaVersion; issueID (optional human-readable ID).
- type: epic, story, task, bug, security, performance, documentation, refactor, chore or research.
- status: the canonical state in the agent lifecycle (a new story starts at pending-acceptance).
- priority: 1 to 5, 1 the highest (1 Critical, 2 High, 3 Medium, 4 Low, 5 Lowest).
- assignee: the assigned agent or person.
- spec: userStory (As a [role], I want [functionality] so that [benefit]) and acceptanceCriteria, each with given, when and then.
- quality: performance (response time at the 95th percentile), security (whether a vulnerability scan is required, the data encryption standard), maintainability (minimum code coverage percent), each set by the project.
- relations: parent, dependsOn (blocking dependencies), relatesTo (related issues and ADRs).

## Story issue template

On GitHub, write it as an issue form: the file story.yml in the ISSUE_TEMPLATE folder of the repository's .github folder, in YAML, with these keys:

- name: User Story; description: user-facing features with acceptance criteria; title: the prefix Story:; labels: type:story and status:pending-acceptance.
- body, in order: a markdown element showing the task specification block with empty values; a textarea User Story (required), described as the feature from the user's perspective, with the placeholder As a [role], I want [functionality] so that [benefit]; a textarea Acceptance Criteria (required), described as success criteria in Given, When, Then form, with a Given, When, Then placeholder; a dropdown Priority (required) with the options 1 (Critical), 2 (High), 3 (Medium), 4 (Low), 5 (Lowest).

For another tracker (this skill's convention), write the template in that tracker's own template format with the same fields, and name the file as that tracker expects or, if unknown, mark the file name to-choose.
