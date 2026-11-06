---
created: "2026-11-04T19:53:10Z"
updated: "2026-11-04T19:53:10Z"
---

# Retrieval signals: which method, what to read, what to include

## Method by signal

| The question contains or asks | Use first | Notes |
|---|---|---|
| A symbol or partial symbol, module, package, file or directory name; a stack trace, exception text, log message, UI label, protocol constant, feature flag, environment variable, route or configuration key; a dependency name, imported API, test identifier, issue identifier or commit hash; a pattern safely expressible as a regular expression | Exact or lexical search | Usually the strongest single signal: identifiers, paths, messages and keys are reused across definitions and call sites. |
| An identifier that is overloaded, shadowed, aliased, re-exported, generated or implemented in several types; definitions, references, implementations, callers, callees or type relationships; text hits mixed with comments, strings and unrelated namesakes | Symbol or language-server navigation | Operations: definition, references, document and workspace symbols, call hierarchy, type hierarchy. |
| An invariant or relationship (does user input reach a sink, which overrides omit an authorization check, where is an unsafe API used without a guard), stateable as syntax, type, control-flow or data-flow constraints, where false positives are costly | A precise structural or data-flow query (for example Semgrep for structural patterns, CodeQL for whole-program data flow) | Prefer exact search instead when one literal or identifier answers the question. |
| A concept whose vocabulary differs from the code; identifiers unknown after exact search and reconnaissance failed; analogous implementations or broad thematic candidates | Semantic (embedding) search, as candidate generation only | Verify every result against current source. Never the primary method for a known identifier, exact error, stack frame, reference list, rename impact, type hierarchy, data-flow property or a just-edited working tree. |
| Why, when, or with which related changes code evolved; a regression to relate to recent changes | Version history | See the history rules below. |

Read directly, without building any index or graph, when the question names one small file that fits in context, the relevant patch is already supplied, or an exact identifier resolves the target uniquely and its direct dependencies are obvious.

## Reconnaissance layers

- Directory layout and monorepo boundaries; language and package manifests.
- Build files, lockfiles, workspace definitions, compilation databases and generated-source rules.
- Entrypoints, service registration, routing, dependency injection and plugin configuration.
- README files and architecture decision records: claims to verify in code.
- Code-owner files: they map path patterns to owners, not proof of current expertise.
- Test directories, fixtures, snapshots, integration harnesses and test naming conventions.
- CI configuration and scripts, inspected before anything is executed.
- Ignore files, generated directories, vendored dependencies, submodules and large binaries.
- Recent commits, churn, linked issues and pull requests; a missing issue link does not mean irrelevance.

Infer boundaries from build and package systems, not directory names alone. Co-change, churn, recency and ownership are relevance priors, never proof of a dependency.

## Reading units

- Read at the narrowest meaningful boundary: function, method, constructor, class, interface, trait, enum, module, namespace, type alias or top-level declaration.
- Keep together the signature, type parameters, decorators or annotations, visibility, leading documentation, attached comments and body. Note file-level imports separately.
- Record the exact line span at the commit read.
- For a file with no reliable parser, fall back in order to language-server symbols, ctags-style symbols, conservative line ranges around exact hits, then bounded file reading; say which was used.
- For a symbol too large to read whole: keep its signature, documentation and member outline; read only the relevant parts of the body, split at statement, block or member boundaries, keeping each control-flow condition with the block it governs; read the full symbol when the reasoning depends on omitted state or control flow.
- A parse tree locates units; it does not resolve names or types. Compiler- or type-aware navigation resolves symbols more precisely than parse-only or ctags-style tools, which give declarations but not a complete type-correct reference graph. Search-based code navigation has lower fidelity than compile-time precise navigation.

## Static-analysis limits

Assume the call or reference graph is incomplete when the code uses:

- Dynamic dispatch and unresolved virtual calls.
- Reflection, dynamic imports, runtime registration, service locators or dependency injection.
- Metaprogramming, macros, templates, conditional compilation or generated code.
- Monkeypatching, prototype mutation, metaclasses or runtime evaluation.
- Native extensions, foreign-function interfaces, RPC, message buses, database callbacks or framework conventions.
- Build variants or feature flags not represented in the analysis.

List the possible targets rather than choosing one silently. A runtime trace proves an edge occurred for the observed workload, not that unobserved edges are impossible. When the uncertainty could change a patch or a security conclusion, escalate to build-aware analysis, targeted tests, tracing or human review.

## Version history

- Log and path history: find introductions, reversions and nearby fixes.
- Blame: link current lines to commits, then read the full patch and its discussion. Blame alone misleads after moves, copied code or deleted predecessors.
- Commit messages, linked issues and pull requests are hypotheses about intent, not specifications.
- Co-change frequency prioritizes files that change together; discount repository-wide formatting, generated files, bulk renames and dependency updates.
- Recency and churn are priors; high churn can mean active behaviour or mere instability.
- Bisect only when a repeatable test separates good from bad revisions.

## Crossing a dependency boundary

Go past the repository only when its source, manifests, lockfiles and the public API are not enough.

1. Identify the exact dependency name, source, version, checksum and build variant.
2. Prefer the version the lockfile or vendored tree selects, not the latest registry release.
3. Search the public API declarations and local call sites before reading dependency internals.
4. Read third-party source from the registry, a mirror or its source repository.
5. Keep external symbols apart and record repository, revision, package version, licence and trust status.
6. Check authorization separately for every repository; do not follow a cross-reference into a repository the user cannot access.
7. Stop at the boundary when implementation detail is not needed.

Label vendored and generated code, and leave it out of the default candidates unless the question names it, the stack trace enters it, or the local wrapper cannot explain the behaviour.

## Assembling the answer set

- Start from the question, repository, branch, commit read and staleness verdict.
- Add a compact repository map only when orientation is needed.
- Include primary symbols in full when they fit; include direct interfaces, types, state definitions, configuration and called helpers only when they affect the question.
- Include tests that encode the expected behaviour, especially regression tests near the target.
- Include history only when intent, regression timing or ownership matters.
- Never put same-named symbols side by side without file and qualified-name labels.
- Prefer ranked signatures or skeletons for breadth and full bodies for the narrow evidence set; when trimming, keep the signature, file path, line span and a marker for what was omitted.
- Closure depends on the question: a review question needs callers and contracts; a bug question needs tests and recent history; a security question needs sources, sinks, sanitizers and framework configuration.
