---
created: "2026-11-04T19:34:32Z"
updated: "2026-11-04T19:34:32Z"
---

# Inventory and classification

## Scope parameters

Fix these before listing any method:

- Organizational level: enterprise-wide, departmental, project-specific or domain-specific.
- Target areas: business processes, technical methods, decision frameworks or classification schemas.
- Time boundary: current-state methods only, or historical methods as well.
- Inclusions and exclusions, stated as a list.
- Success criteria the user or sponsor gave.

## Discovery sources

Use every source the user can supply, and cross-check them against each other:

- Manual: interviews with method owners, workshop notes, observation notes, existing documentation (procedures, guidelines, manuals, records), survey answers.
- System data: event logs, ticket or workflow records, metrics.
- Gaps: a method that people describe but no document records is tacit; record it, with its evidence source as the person or note that describes it.

Merge duplicates: two entries with the same purpose, inputs and outputs are one method; keep the other name under alternative names.

## Inventory record

Each method gets a unique identifier (for example M-01) and these fields; leave a field as to-confirm when the material does not give it:

- Name and alternative names
- Purpose and intended outcome
- Scope and conditions where it applies
- Inputs and preconditions; outputs and deliverables
- Roles (owner and practitioners)
- Tools, resources and dependencies
- Frequency of use
- Performance metrics or success criteria, if any exist
- Known variations, risks and limitations
- Evidence source (document, record, interview, log, user statement)

## Relationships

Record, per pair of related methods:

- Sequence: A must precede B.
- Hierarchy: parent and child, general and specific.
- Dependency: prerequisite, co-dependency or conflict.
- Interaction: data flow, handoff or integration point.

Flag circular dependencies and methods that many others depend on (bottlenecks).

## Classification approach

- Enumerative: fixed, predefined categories; use for a stable domain or a small set.
- Faceted: several independent dimensions (facets), each with its own categories; use for a complex or varied set.
- Hybrid: a fixed top level with facets below it.

Candidate facets: purpose, method type, complexity, domain or area, criticality, control requirements (the last two for compliance-driven work).

Build the scheme in three planes:

- Idea plane: choose the facets and the categories within each.
- Verbal plane: one standard label per category, used everywhere.
- Notational plane: a hierarchical code per category (for example A, A.1, A.1.2) applied to each method.

## Classification principles

- Differentiation: categories differ on a characteristic that matters for the purpose.
- Relevance: categories serve the intended use of the inventory.
- Homogeneity: methods within a category are alike on the defining characteristic.
- Mutual exclusivity: within one facet, a method fits one category only.
- Completeness: every method can be placed.
- Scalability: a new method can be added without restructuring.

## Category definition

For each category write:

- A description with its boundary.
- Inclusion criteria and exclusion criteria.
- A threshold for any quantitative criterion.
- A decision rule for ambiguous cases.
- One prototypical method from the inventory.

## Assignment and confidence

- Assign each method by applying the inclusion and exclusion criteria in a fixed order, and write the rule that decided it.
- Give each assignment a confidence. At 80% or above, assign it. Between 70% and 80%, assign it and list it for review. Below 70%, do not choose: list the candidate categories with the reason for each and ask the user to decide.
- Methods that fit no category go to an unclassified register with the reason.

## Validation

- Internal consistency: no method in two categories of the same facet; every method placed or in the unclassified register; child categories sit within their parent.
- Overlap: when several methods fit two categories, the definitions overlap; tighten the inclusion and exclusion criteria, add a disambiguation rule and reassign the affected methods.
- Expert check: when the user can, have a second person reassign a sample without seeing the first result and compare agreement.
