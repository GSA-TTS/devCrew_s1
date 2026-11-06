---
created: "2026-11-04T23:16:15Z"
updated: "2026-11-04T23:16:15Z"
---

# Evaluation and release: criteria, case kinds, loops, versions and reviews

The Evaluation and Lifecycle and ownership areas are rows of the Findings table (Area, Status, Criteria not met, Evidence, Fix); put the IDs of failed criteria in the Criteria not met column. The case kinds and loops feed the Evaluation plan (ID, Kind, Variant, Prompt or setup, Expected); the version, changelog and review rules feed the Release and governance part.

## Evaluation criteria

- V1: a labelled case set exists and covers the case kinds below that apply to the skill.
- V2: trigger behaviour (precision, recall, over-trigger rate) is tested separately from task success, and autonomous discovery and no-skill behaviour are tested, not only explicitly named invocation.
- V3: every outcome case runs the candidate skill, the previous production version (when one exists) and a no-skill baseline.
- V4: thresholds are declared before running; the release threshold for critical security outcomes is zero.
- V5: outcome checks prefer deterministic validators (file hashes, schema checks, database state, compiler results, policy decisions, domain assertions); where human or model judgement is needed, raters are blind to the version, a rubric is defined and agreement is measured. A zero exit code, a fluent answer or a model's self-report is not verified success.

## Case kinds

- Positive triggers: paraphrases, a terse request, a long request, an implicit trigger, and explicit named invocation.
- No-skill: ordinary questions, direct deterministic calls, and tasks already covered by persistent instructions.
- Near-neighbour: neighbouring skills, overlapping terminology, duplicate display names.
- Outcome: the happy path, every decision branch, boundary values, missing inputs, ambiguous intent and malformed artifacts.
- Multilingual (when the skill serves more than one language): native-language, mixed-language, misspelled, transliterated and locale-specific prompts.
- Script (when the skill bundles scripts): timeouts, nonzero exits, silent errors, malformed structured output, nondeterminism.
- Security (when the skill reads outside content or runs scripts): prompt injection in the description, body, references, examples, filenames, script output, error output and retrieved documents; secret access, path traversal, network exfiltration and package installation.

Report results by stage: discovery (was the skill eligible and present), triggering (was it activated only when appropriate), use (did the agent follow the procedure, read only necessary files, call scripts or tools correctly) and outcome (did the postconditions pass without prohibited behaviour and within budget).

## Trigger metrics

- Trigger precision: TP / (TP + FP); a false positive is an activation on a labelled no-skill or other-skill task.
- Trigger recall: TP / (TP + FN); a false negative is a task requiring the skill on which it does not activate.
- Over-trigger rate: no-skill tasks that activate the skill / all no-skill tasks. It is not one minus precision, because the denominators differ.

## Loops and their stop limits

- Authoring loop (a new skill or a redesign whose boundaries are not stable): write the job statement, positive and negative cases, near neighbours, inputs, outputs, risks and oracle before the body; draft the shortest procedure that covers the positive cases; run lint, unit, trigger, outcome and security tests; change one major variable per iteration (description, body, example, resource structure or script). Exit when all critical cases pass, thresholds are met and two consecutive iterations produce no new high-severity failure. Stop after five iterations and revisit the skill's boundaries or the choice of mechanism.
- Trigger-tuning loop (recall, precision, over-trigger or collision rate misses its threshold): freeze a labelled set of positive, negative, ambiguous, multilingual and near-neighbour prompts; run the exact host and model pair with the full, realistic catalog order; separate retrieval misses, ranking errors, activation errors, forced invocation and policy filtering; revise only the name and description first; re-run the full set, not only the failed examples. If precision and recall cannot both meet target after three description revisions, split, merge, namespace or add deterministic routing. Exit only when held-out thresholds pass and no critical no-skill case activates the skill.
- Failure-transcript loop (a verified production failure, near miss, repeated manual correction or unexplained regression): redact and freeze the trace, inputs, catalog, versions, loaded resources, actions, outputs and verifier evidence; classify the root cause before editing as non-discovery, over-trigger, under-trigger, conflicting instructions, stale fact, missing branch, bad example, script defect, unavailable dependency, runtime drift, policy denial or invalid oracle; turn the failure into a minimal regression case and a near-neighbour control; patch the smallest responsible layer, without broad instructions for a one-off failure; run the new case, the full regression suite, the security suite and the with-versus-without comparison. Stop after three failed revisions and escalate to architectural redesign, tool creation or skill retirement.

## Lifecycle and ownership criteria

- L1: the skill has a primary owner, backup owner, domain approver, security classification, review interval, and a retirement date or a no-planned-retirement state.
- L2: it carries a semantic version for its behavioural contract. Patch: wording or implementation fixed without intentionally changing triggers, authority, required inputs, outputs or procedure. Minor: backward-compatible cases or optional resources added. Major: activation boundaries, output contract, required environment, permission, side effect or established procedure changed. Treat a description change as potentially major, since a wording-only change can alter activation. Any expansion of allowed-tools, network access, filesystem scope, secret class or external destination is security-significant and needs explicit approval whatever the version label.
- L3: each release has a changelog stating trigger changes, instruction changes, resource and script changes, permissions, dependencies, compatibility, migration, evaluation deltas, known limitations and the rollback target.
- L4: production is pinned by immutable host version plus content digest; latest, a mutable branch or an unpinned tag is used only in development.
- L5: reviews before release: domain-owner review for correctness and platform-owner review for compatibility; security review for new code, tools, secrets, network, filesystem, side effects or third-party dependencies; two-person review for an organization-scoped skill; a threat model for a skill that grants tools, executes code, accesses secrets or changes external state. Every required reviewer approves the same digest, and approval of one digest never transfers to another. After three review cycles that repeat the same unresolved finding, or when a critical issue cannot be mitigated or ownership is absent, the change exits rejected and goes to redesign.
- L6: a skill written or patched by an agent was reviewed, as an exact diff and digest, by a human or a policy-authorized reviewer; an agent may propose drafts, patches, tests or failure classifications but may not approve, sign, publish, self-install, broaden its own permissions or overwrite the version currently guiding it.
- L7: a retired skill is marked deprecated with its replacement or reason; new installations stop; owners are notified with a migration deadline; consumers move in bounded cohorts with two migration attempts per consumer by default, unresolved consequential workflows going to a human owner; a tombstone prevents reuse of the name for at least one major release cycle.
