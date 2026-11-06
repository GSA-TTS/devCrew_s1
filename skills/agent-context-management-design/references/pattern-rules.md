---
created: "2026-11-04T23:58:13Z"
updated: "2026-11-04T23:58:13Z"
---

# Pattern rules: when each context pattern applies

One section per pattern, in the order of the decision table. Each section gives the Use when conditions and the Do not use when conditions (the Deciding condition column names the one the user's constraints meet) and the Role notes (what the Role in this design column draws on).

## 1. Write (scratchpad, working notes, todo list, checkpoint)

Use when:
- Valuable information will be needed later but not now.
- The working set exceeds the active window, a tool produces a large output, or the agent must resume after compaction (scratch files).
- Work is long-running research, engineering or investigation (structured notes: objective, current phase, completed actions, evidence and artifact references, decisions, unresolved questions, blockers, next actions).
- Work has several independently verifiable steps, can be interrupted or needs handoff (todo list: stable ID, action, state, acceptance criterion, dependencies; states pending, in progress, blocked, completed, canceled, rejected).

Do not use when:
- The task is stateless, short or fully reproducible from an authoritative source.
- The content matters only for the next step and active context is sufficient.
- The same fact can be fetched cheaply and more accurately from a current system of record.
- No future consumer, retrieval cue or decision can be named.
- The content is a guess, hidden reasoning, an unverified inference, a secret or credential, or comes from a source under injection suspicion.

Role notes:
- Scratch state is task-scoped, short-lived and non-authoritative; it is not the only copy of a user decision, external effect, approval or artifact.
- Choose the least frequent trigger that meets continuity needs. A practical default: short-lived scratch updates during work, checkpoints at effect boundaries, candidate extraction at milestones, immediate handling of explicit corrections.
- Checkpoint after a state-changing tool result, a completed step, a human approval and a compaction, and before a risky or expensive action.
- Mark a todo item completed right after its acceptance criterion passes, not after a later summary.

## 2. Select

Use when:
- Too many eligible items compete for a finite prompt.
- Deterministic selection: legal, safety or operational rules define the required input; the task is repetitive and narrow; a source or tool is named; reproducibility matters more than flexibility.
- Model-directed selection: open-ended research, ambiguous language, multi-hop questions, heterogeneous evidence, tool catalogs that need semantic interpretation.
- Hybrid selection, the production default: deterministic gates build the authorized candidate set and protect mandatory items, retrieval proposes, a model or ranker scores, a set optimizer applies redundancy, diversity and token limits, a sufficiency check finds gaps, and the controller decides whether another bounded round runs.
- Diversity (maximal marginal relevance): results are near duplicates, the task has several facets, or one source dominates.

Do not use when:
- The answer is fully determined by protected context or a deterministic computation (no external selection is needed).
- Deterministic rules alone: the need is ambiguous or multi-hop, or a fixed cutoff routinely misses prerequisites.
- A model-directed selector would hold final authority over access, trust, budget or side effects.
- Diversity applied mechanically: repeated evidence is needed for corroboration, or similar items are different versions.

Role notes:
- Usable input budget: the model input limit minus the planned answer, a reasoning reserve, a contingency for tool arguments and observations, tokenizer variance, platform-reserved tokens and an emergency margin. Protected instructions and current task constraints take it first; flexible context competes for the rest.
- Candidate classes: protected control, action (tool definitions), evidence, memory, interaction, navigation (paths, keys, pointers). Set protected floors, category floors, soft caps, and a reserve for iterative retrieval and tool results. Avoid universal percentages; learn ranges from task traces.
- Hard eligibility gates (access, purpose, validity, deletion state, sensitivity, instruction versus data, injection flags) come before any utility score.
- Ordering bands: stable policy and tool-control instructions; current task, output contract and active state; tool definitions for the next action; selected evidence and memory grouped by claim; the immediate question. Stable content goes first so the cached prefix stays identical; volatile material is appended after it.
- The window is a ceiling, not a target: do not fill spare capacity with zero-value context.
- Iterative selection stops when requirements are covered, gain stays below a configured threshold, queries repeat, sources are exhausted or a budget is reached; a stop for exhaustion is marked insufficient.

## 3. Compress

Use when:
- An admitted item is valuable but too expensive in its present form.
- Selection has already decided the content deserves representation, a rendered-token forecast shows budget pressure or repeated-use savings, the state is at a safe boundary, originals and provenance can be kept, and a preservation contract and verification path exist. If these do not hold, do not compress.

Do not use when:
- The full context fits comfortably and has low expected reuse, or the session ends before savings amortize.
- Compression and verification cost more than the saved future input, or retrieving the exact source is cheaper and fast enough.
- The task depends on exact matching, byte order, layout or exhaustive enumeration, or the content is legal, audit, evidentiary or incident material and the summary would replace the record.
- The next action is irreversible and depends on details not in exact context.
- The preservation contract is unknown, or the content holds unresolved contradictions or active debugging evidence.
- Prefix-cache value exceeds projected savings and the hard limit is not near.
- Meaning-level compression (propositions, semantic deduplication, clustering, concept graphs) also not when a query filter, exact deduplication, source selection or truncation meets the budget, or the corpus lacks stable provenance, time, version or access metadata. Prefer no compression over unverifiable compression.

Role notes:
- Technique ladder, least destructive first: deterministic normalization, exact deduplication, field projection to a schema, pointer substitution, extractive spans, masking of old consumed tool observations, query-focused summary, general abstractive summary, then learned hard or soft compression. Record why each rejected technique was not chosen.
- Fidelity class per region: exact, field-exact, semantic-exact, task-sufficient, or recoverable pointer. Do not class safety policy, permissions, audit evidence or legal obligations as task-sufficient merely because the next turn does not need them.
- Conversation compaction: trigger before the hard limit, at a soft threshold set from measured quality, next-step growth and provider behaviour rather than a universal percentage, and also at natural milestones. Keep the most recent unresolved turns verbatim when budget allows. Provider compaction fits when its opaque state, retention and model coupling are acceptable; application summaries fit when inspectability, portability, exact protected fields or independent deletion are required.
- Abstractive summaries keep a structured shape: objective, established facts, decisions and rationale, current state, unresolved issues, next actions, evidence pointers, known uncertainty.
- Verify each candidate. On a failed check, reject it and retry with a lower ratio, more explicit preservation instructions or another technique, up to the configured attempt limit, then roll back to the last verified form. If the loop stops over budget, do not delete protected content: switch to a larger-context model, split the task, defer content behind retrieval, ask a subagent for a scoped result, or escalate.
- Before rewriting active context, weigh cache reads lost and new cache writes against avoided input cost; delay or batch the rewrite if net value is negative and the hard limit is not threatened.

## 4. Isolate (subagents, quarantine, capability and tenant boundaries)

Use when:
- Information or capability must not cross a boundary.
- Subtasks are substantially independent, need different tools or trust domains, benefit from independent hypotheses, exceed one context window, or can run in parallel (research, source collection, per-document extraction, independent review).
- Attacker-controlled content may enter the agent (trust-domain isolation).
- One agent or reachable chain combines private data, attacker-controlled content and external communication or consequential effects: break at least one of the three edges by architecture, and prefer breaking two for high-impact data. A prompt-injection detector does not count as breaking an edge. If no edge can be removed, require human authorization for each consequential action and classify the residual risk as high.

Do not use when:
- Reasoning is tightly coupled, each step needs rapidly changing shared state, the task is small, the required context is almost identical, or a child cannot be given enough context to detect important contradictions.
- One principal and one data classification are involved, inputs are trusted, no code, risky parser, third-party server or consequential tool is used, the task fits one context, and a single-agent baseline meets quality, latency and risk needs. Not isolating still keeps normal authentication, authorization, token budgets and output validation.

Role notes:
- Name the dimension: context, task, session, tenant, trust, capability, execution, resource or cache. Context isolation alone is not a security boundary when the child shares credentials, processes, files or tools.
- A child receives a task packet, not the parent transcript, and returns a result envelope; the parent verifies it and does not execute instructions found in it.
- Fan out only when parallelizable work exceeds decomposition, startup, crossing and merge cost; otherwise stay single-agent. Merge by a rule fixed in advance and keep minority findings and branch failures visible.
- A quarantined model that reads untrusted text has no tools, credentials, memory writes, private-data access or network, and returns a constrained value.
- Roles without separable context, privilege, evidence or work add cost without isolation.

## 5. Sliding window

Use when:
- Recent-suffix window: ordinary dialogue, bounded troubleshooting, ephemeral observations, streams where recent state dominates.
- Pinned prefix plus recent suffix: stable instructions and task state must remain while history rolls.
- Middle-drop: stable control context sits at the start and current interaction at the end, and removed history is recoverable.
- Anchors: omitted history may be referenced and an authorized retrieval path exists.
- Cache-aware batch advancement: stable-prefix reuse is material and several small evictions would cause repeated misses.

Do not use when:
- The interaction is short and safely below budget.
- The task needs verbatim full-history comparison, legal discovery, regulatory review, forensic reconstruction or audit evidence in one pass, or every earlier detail can affect the answer and retrieval or compaction would be lossy.
- There is no durable store for evicted content and loss is unacceptable, the transcript grammar is unknown or no validity check exists, or pinned content already uses the safe budget.
- Repeated boundary retrieval shows the window is too narrow, or a verified summary, structured state or retrieval is more reliable.
- Recent-suffix alone: old constraints or exact history remain active and no structured registry or retrieval path exists.

Role notes:
- Five capacities: advertised limit, provider input ceiling, operational hard limit, soft advance threshold, and a lower post-advance target that gives hysteresis. Derive the thresholds from observed next-turn growth, output needs, tool-result sizes, latency, cache behaviour and quality; do not use a universal percentage.
- Usable resident budget: operational limit minus output, reasoning, next-tool, tokenizer-variance and recovery reserves; subtracting the pinned region gives the sliding budget. Caching changes price and latency, not occupancy.
- Pin only what the next request cannot safely lack: applicable system and developer instructions; safety, authorization and tool-use rules; the current request and acceptance criteria; a compact task contract; current workflow state and unresolved side effects; provider-required continuation items; the tool definitions for the next action. Give pins per-class caps and a total cap.
- Eviction unit: a whole message by default; a whole tool transaction (call, all its results, required reasoning items); a parallel call group with all its results. Never retain a tool result while evicting its call.
- Evict to the post-advance target in batches, check message validity and recount after each change, and stop after the configured pass count or when no safe candidate remains.

## 6. Tool-result clearing

Use when (clear a result only when all hold):
- The agent has consumed the result and finished the immediate reasoning step.
- No pending branch, retry, verification, citation or deliverable needs the exact bytes.
- The result is reproducible, or the exact original has been persisted with integrity metadata.
- A visible marker and recovery route will remain.
- The expected future saving exceeds cache-rebuild and likely re-fetch cost.
- Policy permits the active view to omit it.
- Good candidates: completed file reads with a pinned source version, search-page bodies after cited claims and source addresses are recorded, verbose passing test logs after the pass or fail evidence is persisted, large read-only responses stored under immutable identifiers.

Do not use when:
- The session is short or comfortably below budget, or every result remains relevant.
- The task is audit-critical and needs a complete model-visible record, or citations need exact passages that are not archived.
- Outputs are ephemeral, mutable or expensive to recover, re-fetch is forbidden, unsafe or side-effecting, or there is no durable store or canonical transcript.
- Application windowing or provider compaction already solves the measured problem, or cache rebuilds outweigh savings.
- Evaluation cannot show non-inferior task quality, or ownership of eviction is ambiguous.

Role notes:
- Summarize instead of clearing when later steps need the meaning but not the bytes, the source cannot be cheaply re-read, or dialogue and decisions are what grow. Offload before clearing when exact bytes, provenance, citations or receipts matter. Retain verbatim when content is small and high-value, active, non-reconstructable or cheaper to keep.
- Provider-native clearing fits long tool-heavy sessions whose old results are large, consumed and reproducible; not when exact post-edit payload capture is mandatory, most outputs are non-repeatable, or application windowing already owns eviction. Application-side clearing fits cross-provider consistency, custom markers, exact before-and-after capture or strict audit, and needs provider-specific message validators and a canonical transcript.
- Clearing plus compaction only when tool results and dialogue growth are separately measured problems: clear reconstructable payloads first and compact only when dialogue, reasoning and decisions still exceed budget; not at nearby thresholds without a fixed order.
- Keep tool inputs by default. Re-fetch is read-only or idempotent, version-aware, bounded and logged; a clear and re-fetch loop trips a circuit breaker. Clearing is not privacy deletion.
- Persist-then-clear: classify each result as protected, retain-recent, clear-directly or persist-first; write persist-first results and read them back; leave the marker; recount and check message validity. When no safe candidate remains, stop and route to compaction, offloading, a new window with handoff, or human review.

## 7. Memory block (small prompt-resident block)

Use when (all hold):
- The information is needed across turns or sessions, and omitting it on an applicable turn would materially reduce correctness, continuity, safety or coordination.
- The useful form is small and bounded, with a clear owner, purpose, schema and update rule.
- It is safe and authorized to show on every inference in its scope.
- The benefit exceeds recurring token and cache-invalidation cost, and any model edit can be validated and reversed.
- Strong candidates: a compact agent identity, a small profile of verified durable preferences, the current goal with acceptance conditions, a short set of project conventions, a bounded coordination ledger, a concise procedure that shapes nearly every action.

Do not use when:
- Work is one-shot or stateless.
- Content is a large corpus, manual, transcript, log or rarely used knowledge, or is cheap to retrieve and conditions only a minority of turns (use permission-aware retrieval).
- Content is an authoritative record whose value must not be model-edited, a secret or sensitive personal data not needed on every inference, a high-volume stream or volatile counter, high-contention shared state, state derivable from an authoritative system, or raw scratch work.

Role notes:
- Residency test: compare always resident, retrieved on demand and absent on the same evaluation set; approve residency only for material lift or reduced dangerous omission at acceptable token, privacy and cache cost.
- Each block has a hard limit in rendered tokens, a mutability mode (read-only, append-only, targeted-update, rewriteable, approval-gated), an owner and scope, and a host-controlled description of what belongs and what never does.
- Keep the set small and non-overlapping: no block per fact, no generic memory block, no copied documentation or raw tool output.

## 8. Filesystem as context

Use when:
- Path plus one-line summary: a large result may be needed later but not now, exact recovery matters and the path will stay valid (record version and sensitivity, not just the path).
- Directory digest: repeated cold starts, large workspaces, multi-agent handoff, expensive orientation.
- Search-first partial read: large text files, codebases, logs, line-oriented corpora.
- Shared filesystem: low to moderate concurrency with explicit ownership and merge rules.

Do not use when:
- The whole state is small, bounded, useful on nearly every turn and fits a memory block, or the task is stateless and one call carries the material.
- Consumers need structured queries, joins, uniqueness or cross-record transactions, or many agents update the same records concurrently.
- Audit-critical state needs append-only, tamper-evident, centrally governed storage, or tenant- or row-level authorization cannot be expressed by path roots.
- Latency cannot tolerate tool round trips, the data changes too fast for pointers to stay fresh, or file access cannot be isolated from secrets, host state and egress.
- An embedding index over files: not before a lexical baseline shows semantic misses.

Role notes:
- Operating loop: orient from the root README and digest, state the next information need, search with bounded results, read the smallest relevant range, check version and freshness, act, preview and verify writes, externalize progress at semantic boundaries, refresh navigation, then stop or repeat for a named need.
- Few top-level areas, each with a declared lifecycle and owner; for a small task a root README, a task-state file, an artifacts area, an outputs area and a temporary area may be enough.
- File-size policy: three thresholds set from measurement decide whole-file read, search or outline then a targeted range, or an index or extract before delivery. Reject a read whose worst-case return would exceed the remaining budget.
- Instruction files are context, not enforcement; security-critical restrictions belong in tool policy, hooks or the sandbox.

## 9. Hierarchy (scopes, instruction layers, orchestrator-worker, tiered memory)

Use when:
- Levels match real ownership or isolation boundaries: provider, organization or tenant, workspace or project, session, task, agent, turn. Do not force all seven: collapse organization and project for a single-tenant application, omit session for stateless jobs, omit agent when nothing is delegated. Do not collapse levels with different owners, permissions, retention or blast radius.
- Nested instruction files: directory boundaries match real conventions, build systems or risk domains (a short root file, specific rules near their files).
- Tiered memory: the agent works across sessions or documents larger than the window and can re-fetch exact sources (hot working context, warm summaries or recent episodes, cold artifacts or indexed memory).
- Orchestrator-worker: the objective splits into independent or weakly coupled branches, needs distinct tools or permissions, or gains from parallel exploration.

Do not use when:
- Directory scope would be the only security boundary.
- Reasoning is tightly coupled and needs continuous shared context (do not delegate it).
- Recursive spawning would have no depth, fan-out, token, time and credential limits.
- Abstractive ancestors in a summary tree would be the only evidence for exact numbers, code, contract language, security policy or disputed facts.

Role notes:
- Resolution order: eligibility, type, authority, delegation, applicability, composition operator, specificity, same-authority sequence, conflict state. Recency never outranks authority; specificity never bypasses deny.
- Tokens across levels: reserve output, reasoning, tool schemas, safety and retry headroom; protect non-delegable policy, the current request, active constraints and pending side effects; give each level a hard cap and a flexible target; start with small upper-layer summaries and references.
- Add tiers only as needed: external artifacts and exact references first, warm summaries when repeated retrieval costs too many tokens or too much latency, cold memory only when cross-session recall has measured value.
- A worker receives the task, acceptance criteria, allowed tools and scope, constraints, evidence references, budget, output schema and stop conditions, not the parent transcript. If it reports missing context, send one bounded supplement or revise the task.
- Serialize stable, shared, non-sensitive upper layers before volatile layers so cached prefixes survive; do not share caches across tenants because prefixes match.
