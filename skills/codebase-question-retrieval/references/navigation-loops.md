---
created: "2026-11-04T19:52:13Z"
updated: "2026-11-04T19:52:13Z"
---

# Navigation loops: entry, iteration, budget, dead ends, exit

Six bounded loops, run in the order they are needed. Every loop works on one pinned snapshot with the tools the user has authorized. The budgets are default starting points: reduce them for interactive work, and raise them only when the user approves.

## 1. Repository reconnaissance

- Enter when the repository is unfamiliar, the question names no unique file, or build and package boundaries are unknown.
- Each iteration: inspect one evidence layer (top-level layout; manifests and build files; entrypoints and configuration; tests; recent history). Record repository boundaries, languages, generated and vendored areas, likely target packages and available navigation tools. Form at most three localization hypotheses. Information gain is fewer plausible packages or strategies, a new exact token, or a confirmed build and test path.
- Budget: at most 3 iterations, 8 tool calls, 4,000 retrieved tokens or 5 minutes, whichever comes first.
- Dead ends: if an iteration adds no new exact token, boundary or discriminating hypothesis, do not repeat the same directory listing; go back to the question text, tests, stack trace or history. If generated metadata conflicts with the source layout, trust the pinned build configuration for what is included and note the conflict.
- Exit when one to three packages or files and a primary search strategy are identified. Escalate when the repository cannot be built or interpreted without tooling you lack. Abstain when the checkout or target revision cannot be authenticated.

## 2. Retrieval-strategy selection

- Enter after reconnaissance, or at once when the question holds a strong search key.
- Each iteration: classify the question (exact, symbol, structural, semantic, graph, historical, conceptual); choose the cheapest method expected to tell candidates apart; predict what evidence would confirm or falsify it; run a small probe. Information gain is fewer candidates, more precise current-source matches, or a resolvable symbol or test.
- Budget: 3 strategy revisions, 6 probe calls, 2,000 planning tokens.
- Dead ends: zero exact hits: normalize case and naming conventions, search the question's strings and the tests, then try symbols. Too many collisions: switch to path-scoped search, symbol resolution or a structural query. Semantic search returning generic utility code or boilerplate: drop that route and return to repository vocabulary, tests or graph neighbours.
- Exit when a strategy has a verifiable target and a manageable number of candidates. Move to a heavier method only after the cheaper probe failed for a stated reason. Abstain if every feasible method depends on unauthorized or stale data.

## 3. Exact search, then read

- Enter when the question contains, or reconnaissance found, identifiers, strings, paths, errors, tests, APIs or configuration keys.
- Each iteration: search the exact literals and identifiers, then controlled variants (naming convention, case, prefix, suffix). Scope by likely paths and exclude generated, vendored, binary, fixture or snapshot content unless it is relevant. Rank matches as definition, executable use, test, configuration, documentation, generated artifact or noise. Open the current file around the best matches and widen to the containing unit. Information gain is a newly verified definition, caller, test or entrypoint, or an eliminated hypothesis.
- Budget: at most 3 rounds, 6 search expressions per round, 8 newly opened files per round, 12 tool calls, 12,000 retrieved tokens.
- Dead ends: stop reformulating a string after two variants that gained nothing. If only comments or docs match, search the behaviour's tests, call sites, routes, error construction or manifest registration. If too many files match, add package, symbol-kind or call-site constraints rather than reading them all. If the only hit is stale or generated, trace its generator or its current replacement.
- Exit with verified current definitions and relevant uses. Pass ambiguous names to symbol navigation. Pass missing conceptual vocabulary to semantic candidate search. Abstain when a named artifact does not exist at the pinned snapshot and no rename or history evidence explains it.

## 4. Symbol and call-edge expansion

- Enter when the target symbol is known but its behaviour, callers, implementations or impact is not.
- Each iteration: resolve the symbol by fully qualified name, language, file and span. Expand one relation type chosen by the question (definitions, references, imports, callers, callees, overrides, implementations, type hierarchy, tests, build target). Open the most useful neighbouring units and check each edge against current source. Label each edge static, heuristic or runtime-observed, with a confidence. Information gain is a new behaviour-affecting dependency, a confirmed execution path, a relevant test or an eliminated branch.
- Budget: at most 3 hops, 25 new nodes per hop, 100 edges in total, 12 tool calls, 12,000 retrieved tokens.
- Dead ends: stop expanding generic framework hubs, logging utilities, serialization helpers or central registries unless the question is about them. If a call fans out through dynamic dispatch, go back to runtime registration, concrete types used in tests, configuration or targeted tracing. If two expansions in a row add nothing relevant, return to exact search or history.
- Exit when the relevant execution or dependency path is supported by current source and tests. Escalate unresolved dynamic behaviour to runtime observation or a specialist. Do not claim completeness when analysis cannot resolve reflection, code generation or runtime mutation.

## 5. Dependency-closure context assembly

- Enter when candidate symbols are verified and you must explain, review or plan an edit.
- Each iteration: add the primary target unit (signature, documentation, body); add only the dependencies needed to interpret types, state, control flow, configuration, contracts or expected behaviour; add the most relevant tests and fixtures; deduplicate repeated imports, generated fragments and boilerplate; order the set as question and snapshot, repository map or skeleton, primary target, direct dependencies, tests, then narrowly relevant history. Information gain is a resolved undefined symbol, hidden precondition, behavioural branch or expected outcome.
- Budget: at most 4 rounds, no more than 25 files by default, and assembled source capped at 24,000 tokens or the model's allowance, whichever is lower.
- Dead ends: remove a dependency that resolves no explicit uncertainty. If the set grows through common infrastructure, replace full bodies with ranked signatures or skeletons. If one symbol dominates the budget, split it at syntactic boundaries and keep its signature and parent identity. If trimming removed a signature, branch condition, exception path or test assertion, restore it and prune lower-value material instead.
- Exit when every material claim is supported by included source or an explicit tool result. Raise the budget only when a named unresolved dependency is likely to change the conclusion. Abstain when the minimal context cannot fit and no tool can answer the omitted relationship.

## 6. Verification against HEAD

- Enter before presenting a conclusion, proposing a patch or reusing assembled context.
- Each iteration: read the query-time HEAD, the branch or worktree and the dirty status; compare them with the commit every selected unit was read at; reopen changed files and remap symbols and line spans; rerun the decisive exact or symbol queries over the affected files. Information gain is confirmation that the evidence is unchanged, or a changed conclusion found.
- Budget: 2 repair iterations, 6 tool calls, 4,000 retrieved tokens.
- Dead ends: if HEAD changes again during verification, invalidate the affected evidence and restart once. If the tree stays unstable, freeze one snapshot or stop. If uncommitted changes overlap the selected symbols, treat the working tree as a separate overlay and never merge it silently with committed results.
- Exit with one verdict: `verified`, `verified_with_dirty_overlay` or `stale_but_nonmaterial`. Escalate when rebuilding or freezing needs privileges you do not have. Abstain when staleness is material or the snapshot keeps changing.
