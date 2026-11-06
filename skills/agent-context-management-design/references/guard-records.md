---
created: "2026-11-04T23:58:13Z"
updated: "2026-11-04T23:58:13Z"
---

# Guards and records: protected content, markers, handoffs

Sections 1, 2 and 7 give the protected items to list in Guards (keep those that apply to the user's agent). Sections 3 to 6 give the fields of each record the design uses.

## 1. Never cleared, compressed or evicted automatically

- A tool result the agent has not yet acknowledged or acted on; the call and result of an in-flight or unmatched tool transaction.
- A tool call whose exact arguments still establish provenance, scope or replay evidence.
- Errors, denials, rate-limit responses, conflict versions and diagnostics that explain the current state.
- Side-effect receipts, transaction identifiers, approval records and evidence needed for compensation.
- Results needed to verify, quote or cite a later answer, unless an immutable copy and a precise pointer exist.
- User uploads or ephemeral streams that cannot be reproduced.
- Security findings, taint labels, authorization context and policy decisions still governing execution.
- The current plan, unresolved questions, active constraints and branch-merge inputs.
- Memory-write confirmations until the write has been read back or otherwise verified.
- Content under legal hold or an audit rule requiring an unedited model-visible record.
- User corrections, commitments, permissions, deadlines, pending effects and failure state.
- Any item whose loss classification is unknown: unknown means retain.

## 2. Protected atoms in any compression or summary

Identifiers; entities; quantities with their units and qualifiers; dates and temporal relations; negations, exceptions, prohibitions, permissions and uncertainty; user intent and the authority behind each instruction; state (completed work, current work, unresolved questions, blockers, pending tool calls, next safe step); evidence (exact tool outcomes, citations, error messages); relationships (dependencies, contradictions, which evidence supports which claim). For high-risk material, every protected atom is retained and the output is either extractive or a pointer to the exact original.

## 3. Placeholder for a cleared tool result

- A stable clear-event ID.
- The original tool name and tool-call ID.
- A neutral statement that the payload was removed from active context.
- Whether the exact original was persisted, and a versioned pointer when permitted.
- A re-fetch action when replay is safe.
- The source version, retrieval time or content hash needed to detect change.
- A warning not to treat the marker as evidence.
- The retry budget, or a rule not to re-fetch automatically.

Keep secrets, full original arguments and sensitive paths out of the placeholder, and do not say the content was summarized when it was removed.

## 4. Window-handoff record (compaction)

- Original user objective and all active instructions; current plan and phase.
- Work completed, with outputs and artifact references; decisions and rationale; rejected alternatives; user corrections.
- Facts still needed; open questions, blockers and failed approaches.
- Current environment state: versions, branches, files, resources.
- Pending approvals and actions that must not be repeated.
- Critical names, IDs, numbers, dates, constraints and negations.
- Sources already consulted and their coverage.
- Next safe action and stop conditions.
- Compression lineage and where the original transcript is kept.

Before accepting the summary, check identifiers, numbers, deadlines, negation, permissions and tool-effect status against the source, and keep a pre-compaction recovery point.

## 5. Pointer to an offloaded artifact

Artifact ID and immutable version; content digest; media type and size; a one-sentence task-relevant digest; provenance and trust label; retrieval locator or tool; access scope; freshness status; whether rehydration is mandatory before a named action. Rehydrate before any irreversible action whose justification rests on pointer-only content.

## 6. Subagent task packet and result envelope

Task packet: objective, non-goals, completion criteria and deadline; allowed input references, not the full transcript; facts the child may assume, with provenance and freshness; trust tier and taint labels; tool allowlist, a credential handle, network and filesystem scope, resource budget; output schema, evidence and uncertainty fields, partial-result rules, maximum size; prohibited actions and escalation conditions. It leaves out the parent scratchpad, hidden reasoning, unrelated user data, reusable credentials, sibling outputs and tools added just in case.

Result envelope: terminal status (succeeded, partial, failed, blocked, timed_out, policy_denied); structured claims or artifacts with source identifiers; assumptions, uncertainty, unresolved conflicts and missing evidence; taint labels; actions attempted and side-effect status; tokens consumed; a short readable summary written after the structured result is fixed.

## 7. Untrusted content

- Label external documents, pages, email, tool results and model results as untrusted by default, and keep them in a channel separate from trusted instructions.
- Delimiting untrusted text is defense in depth, not the only control for private-data access, external communication, code execution or durable writes.
- A summary of untrusted material stays tainted unless a deterministic extractor produced a narrow typed value and policy permits declassification.
- Untrusted instructions, secrets and one-off tool output are not promoted into durable memory, and recalled text does not change policy, permissions or tool allowlists.
