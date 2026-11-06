---
created: "2026-11-05T00:32:47Z"
updated: "2026-11-05T00:32:47Z"
---

# Building, testing and adjusting arXiv queries

## Syntax

- Operators are AND, OR and ANDNOT, in uppercase only.
- Parentheses group terms and set precedence; use them in any query that mixes operators.
- Quotation marks search an exact phrase.
- A trailing asterisk matches any ending (authentica* matches authentication and authenticator). arXiv does not accept a wildcard at the start or in the middle of a term.
- Punctuation and special characters inside a term are generally not indexed: for OAuth2.0, search OAuth and 2 separately.
- Stemming is automatic in most fields.
- In an API request, spaces become + and parentheses become %28 and %29.

## Fields

| Field | Searches | Use |
|---|---|---|
| abs: | abstract | primary field for concept discovery |
| ti: | title | high precision; for well-defined concepts and for validating a cluster |
| all: | title, abstract, categories, authors | broadest; use sparingly, it inflates false positives |
| au: | author names | author-specific searches |
| cat: | category code | filter by research domain |
| submittedDate: | submission window, written [YYYYMMDDHHMM TO YYYYMMDDHHMM] | restrict to a date window |

Apply a cat: filter and a date window to every query.

## Query structure

A query chains four parts with AND: the core concept as an abs: group of synonyms joined by OR, the angle the scope requires (for a security scope, security OR attack* OR defen*), the scope context that marks the boundary of the scope statement, and 2 to 4 category codes joined by OR. For example, for LLM-assisted code review:

```text
abs:(code review OR review comment*) AND (LLM OR large language model*) AND (automat* OR generat*) AND (cat:cs.SE OR cat:cs.CL) AND submittedDate:[202401010000 TO 202512312359]
```

For each concept, list 5 to 10 synonyms or near-synonyms and group them into 2 to 3 OR groups per query. Over-expansion creates false positives (poisoning also finds toxicology papers); answer it with AND constraints on the angle or scope.

## Techniques, in this order

1. AND chaining: add one independent relevance signal at a time (an application context, an actor, the angle) until the count falls into the keep band.
2. OR expansion: add synonyms and variant terms for concepts the field names in more than one way.
3. ANDNOT exclusion: remove a recurring off-topic sub-domain. Overuse prunes relevant papers; use it conservatively and recheck the test set after adding it.

Ways to produce the variants of a cluster:

- Synonymy: a more general term, a broader context, a related concept.
- Abstraction level: a higher-level pair of concepts, or a lower-level pair of named standards or methods.
- Boolean restructuring: move terms between OR groups and AND clauses.
- Exclusion: an ANDNOT clause for a sub-topic outside scope.
- Author or date constraint: au: for a known author; a narrower submittedDate window.
- Title or abstract: a broad abs: variant and a narrow ti: variant of the same topic. The ti: variant is a quality filter: if it returns near zero results, the topic may be too narrow or missing.
- Context qualification: when two clusters or projects share a topic, add context terms that send each paper to one of them (internal pipeline terms against external vendor terms, for example).
- Date stratification: search the primary window first; search earlier years separately and label their papers baseline rather than primary.

## Result count adjustment

| Result count | Action | How |
|---|---|---|
| under 10 | Broaden | expand OR synonyms; remove the most restrictive AND clause; extend the date window back one year at a time; check misspellings and variant terms; run a ti: search to confirm the concept exists |
| 10 to 60 | Keep | proceed to screening |
| 61 to 100 | Refine | add a specificity AND clause on the angle or scope |
| over 100 | Tighten | add a category filter; replace generic terms with narrower ones; add an ANDNOT exclusion |

## Test set check

- The query retrieves all of its test-set papers: well scoped.
- It retrieves some: it may be too narrow; consider broadening synonyms.
- It retrieves none: it is likely off topic or poorly built; redesign it.
- A test-set paper that no query retrieves: compare its title and abstract with the query terms, add its phrasing as synonyms, try a ti: search on its central terms, and as a last step search the term with all:.

## Many off-topic papers at screening

When most of a query's screened papers are Red: add the angle or scope term, add the context of the scope statement, exclude the off-topic domains with ANDNOT, or tighten the category filter toward the primary category.

## Overlap between projects

Run the overlapping queries of both projects and count the papers that appear in both result sets. If the papers in both sets are more than 30% of all distinct papers of the two sets, revisit the partition and add context qualifiers.

## Category codes

| Code | Name | Use |
|---|---|---|
| cs.CR | Cryptography and Security | security research |
| cs.AI | Artificial Intelligence | AI and machine learning research |
| cs.SY | Systems and Control | orchestration, distributed systems, automated control |
| cs.CL | Computation and Language | LLM-specific and language research |
| cs.SE | Software Engineering | supply chain, DevOps, CI/CD |
| cs.DC | Distributed, Parallel, and Cluster Computing | federated and multi-agent systems |
