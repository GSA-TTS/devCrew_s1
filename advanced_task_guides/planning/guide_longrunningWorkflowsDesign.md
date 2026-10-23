# Guide to designing long-running workflows

For humans and SI agents that design, revise or review a multi-step workflow that an orchestrator runs with sub-agents, external services, operator gates and a machine-readable run record. The rules are general.

Version: 0.1 (Oct2026)  

Important notes:

- This guide aims to support the design of any multi-step workflow (not just coding workflows)   
- You are ultimately responsible for the workflows you produce.  
- Please feel free to comment and provide inputs/proposed changes.

## 1\. The key rules

* Make the run unattended-capable before it starts. Pre-approve the exact commands the workflow runs, make every file change through the harness's native edit tools, and keep shell calls short and single-purpose. §12.  
* Never wait passively. Every background job gets a progress file, a timeout and a scheduled check; the orchestrator never ends a turn on "waiting". §10.  
* Attribute every second. Tools write events for working, awaiting the operator, awaiting a permission, rate-limit waits, session pauses and agents running, at the moment each starts and ends. §10.  
* Freeze the spec and state each rule once. Record the spec hash at `run_start`; generate any restatement (kickoff, brief) from the source. §3.  
* Write the data contracts before the process rules: an ID for every way an item enters, a terminal status for every way it leaves, a detail schema per event type, a locator format per source format, an enumerated column for anything a tool reads. §4.  
* Build a small tested core once (clock, CSV and locks; vocabularies; request chain; event log; ledger; briefs; verifier) and make every step tool use it. §5.  
* Enforce in code, not in prose: caps in the dispatcher, budgets and waits in the sender, prohibitions in permissions, pre-checks as preconditions, schemas at emit time. §5, §7.  
* Measure before you plan: count probes before the planning gate, per-item stage times including the slow tail, channel yield on a sample, metadata error rate against the primary source. §6, §11.  
* Ask decisions as structured questions with 2 to 4 options, their consequences and one recommendation; pre-decide failure policies at the first gate; grant standing authority as a rule over conditions, not as a list of steps. §8.  
* Verify with deterministic checks first and never loosen them; keep evaluation sets away from whoever tunes against them; feed gate fixtures straight into gate code; define every metric in code. §9.  
* Budget tokens per step from the fan-out and its verification layer; a dispatch costs tens of thousands of tokens before it does any work; the orchestrator's own context costs most. §87, §10.  
* Close cleanly: promote every cited file out of scratch before cleanup, route every operator decision that removes items into the deliverable's caveats, and end with one carry-forward list. §13.

## 2\. Design procedure

1. Write the design brief: objective, outputs, a success contract whose metrics are defined operationally (stage, numerator, denominator, script), the event model that makes each metric computable, and the operator's standing rules and availability.  
2. List every item route: each way an item enters (search, merge, rescue, manual admission, fixture), each way it leaves (rejected per gate, deferred by budget or operator, unavailable, failed) and each source format, fallbacks included. Give each an ID form, a status and a locator rule.  
3. Measure cheaply before planning: count probes for every query family, a timed slice of every per-item stage (including the slow tail), the yield of each channel on a few items, and the error rate of any metadata a gate will trust, checked against the primary artifact.  
4. Write the contracts: one config file with vocabularies, ID grammars, the status machine, event schemas, budgets with pre-gate values and caps. The spec names this file.  
5. Build or reuse the core kit (§5.1) and test it on replayed real data, including two-item concurrency and every operator numeric rule.  
6. Write the spec on the step template (§3.4), with one home per rule; generate the kickoff restatement from it.  
7. Review it. An independent reader lists every rule with two readings and every item route with no named ID, status or schema; a linter checks the step graph for gate dependencies and reads of values never produced.  
8. Dry-run each step on a small real slice end to end: requests, agents, verifier and run-record build.  
9. Prepare the environment: an allowlist for the commands the run uses, native edit tools, shell traps in every brief, the harness's rules for sub-agents, and a staging plan for a shared working tree (§12).  
10. Freeze: write the spec and config hashes into `run_start`. Any later change is a recorded amendment.

## 3\. The spec

### 3.1 Freeze and pin

- Freeze the spec before `run_start` and record its version and hash there.  
- Change a running spec only through a recorded amendment that lists the agents to re-brief and the artifacts to re-check.  
- Address spec text by stable anchors (sub-step IDs, headings), never by line numbers.

### 3.2 One home per rule

- If a rule must be repeated to survive context compaction, generate the copy from its source and diff the two at kickoff. Never let a summary table restate a rule; point to it.  
- Where prose and a machine schema disagree, say which wins.

### 3.3 Proportions

- Write more details for data structures that multiple tools rely on, and use fewer words for rules that code and tools handle automatically.  
- Keep contingency mechanisms as short stubs with a trigger, and expand one only when it fires.  
- Judge proportions by where stops and rework happened, not by wall-time shares, until waits are attributed.

### 3.4 Step template

#### Reads, Produces

Defines all inputs consumed by the step and all outputs generated, including required tools, execution logs, and data spreadsheets.

#### Consumes decisions

Identifies the decision gate items, operator approvals, or upstream sign-offs that the step depends on before execution.

#### Volume

Specifies the expected item count and total workload distribution allocated per agent.

#### Agents

Details the maximum concurrency cap and expected total agent count as separate fields, specifying processing priority orders across item types rather than fixed lane assignments.

#### Network

Contains the explicit external network and request policy rules governing the step, or explicitly specifies no external calls.

#### Sub-steps

Outlines stable sub-step identifiers, execution dependencies, and non-overlapping output targets.

#### Failure rule

Defines the explicit programmatic reaction and handling strategy for each error or failure class encountered.

#### Evidence location

Designates which step outputs are preserved permanently as official records versus those treated as temporary working files.

#### Time estimate

Provides processing time estimates per stage and per item, explicitly accounting for slow tail latency.

#### Done when

Specifies the exact verification script invocation that must finish with a zero-error result to close the step, including gate verification steps.

### 3.5 Order and dependencies

- Nothing that needs a gate's decision may run before that gate.  
- Lint the step graph before the run: reachability, reads of values never produced, gate dependencies, whole-workflow constraints.  
- Design one workflow per task class as a typed, checkable graph, not per input or as free-form code.  
- Turn every carried-over lesson into an executable check (a test, a validator, a dispatcher refusal).

## 4\. Data contracts

Clear data contracts prevent ambiguity and costly downstream rework across automated workflow tools. Below are the core contract rules governing item state, event telemetry, and data integrity:

- **IDs:** Establish an explicit ID grammar for every way an item enters or is rebuilt (search, merge, rescue, manual admission, fixture). Use a separate namespace for synthetic and back-filled rows, and never reuse a cancelled ID.  
- **Terminal statuses:** Define an explicit terminal status for every potential exit path (rejected per gate, deferred by budget, deferred by operator, unavailable, or failed). Standardize all done-when completion criteria over the gate-approved set.  
- **Status machine:** Declare all states, ranks, and terminal status sets once in configuration. Every sub-state and filtered subset must be derived programmatically in code rather than re-declared across individual modules.  
- **Request vs. item:** Maintain request processing status and underlying item status in completely separate fields to prevent execution failures from corrupting item state.  
- **Event schema:** Specify required detail fields for each event type directly within the schema and strictly validate them at emission time.  
- **Source formats:** Define a deterministic locator rule for every source format, including fallbacks, and preserve locator references throughout all downstream checks.  
- **'Not stated' values:** Provide an explicit, accepted "not stated" sentinel value for every required field so automated agents never invent missing information.  
- **Machine-read meaning:** Provide an enumerated column for every data category read by automated tools, avoiding free-text parsing.  
- **Gate outcomes:** Assign a specific code for every failure condition at a gate, along with an explicit mapping for external source taxonomy and type vocabularies.  
- **File and column ownership:** Designate a single, named writer and reader for every file and column, testing reader implementations on real output generated by writers.  
- **One meaning per name:** Maintain a single, canonical definition for each term and field across all files and documentation in the workflow.  
- **Authority:** Establish a single authoritative artifact for every fact, ensuring corrections propagate automatically or trigger divergence flags.  
- **Config:** Consolidate all gate tunables into a single configuration file named in the specification, from which all tools read parameters.  
- **Dates:** Pin every execution date in a plan to its fixed as-of timestamp rather than evaluating against the live wall clock.  
- **Labels:** Ensure every assigned label cleanly separates items into distinct, actionable categories.  
- **Cross-field validity:** Enforce mechanical, automated validation checks across related and co-dependent fields.

## 5\. Tools

### 5.1 Build the core kit first

* **core:** injectable clock; CSV read and write with a header check; atomic write; run directory from an argument; `lock(path, timeout, tries)` that raises and logs.  
* **vocab:** ID grammars as compiled patterns with mint functions; status machines; rejection codes; verdicts; all generated from the config.  
* **chain:** one request in flight; raw response and sidecar saved before the hook; completion recorded as an event; budgets and the retry reserve as exit codes; `requeue <idx> --reason`; one queue status vocabulary; wait-start and wait-end events.  
* **runlog:** `emit(step, type, message, detail)` that validates the full per-type contract under a lock; a derived, schema-checked run record; reconcile; critical path; agent, wait and decision records.  
* **ledger:** `open` at launch with the agent id; `close` by append from the harness notification; separate prepared, launched and reported stamps; attempt numbers that increment.  
* **briefs:** render one shared brief and the packets from a table; `check` scoped to exactly the packets about to go; return the brief hash for the ledger.  
* **verify:** per output type: unique-key YAML, unknown keys fail, verbatim quote and locator checks, one logged row per round, exit codes.

- The costly failures sat in untested glue code (ledger writers, a lock wrapper, event emitters), not in the well-tested parsers.   
- Pass step and node IDs into tools as arguments, and keep shared helpers in a library that no step owns.  
- Keep per-step scripts thin and disposable.

### 5.2 Test what breaks

- Write every operator-stated numeric rule (waits, caps, thresholds) as a unit test before the first live call.  
- Test every mapping of an external vocabulary against saved real responses.  
- Test every concurrent path with real processes on at least two items; use bounded locks that raise; put a timeout on every subprocess.  
- Give every shared file one writer function with its own lock.  
- Test drivers that write shared state (ledger, inventory, queue) as hard as parsers.  
- Rehearse each tool on a small real slice of its step's input, and calibrate heuristic checks on a labelled pilot.  
- Include a UTC midnight rollover and the run's `as_of` in replay tests.  
- Inject clock, sleep, randomness, network and subprocess runners.  
- Make environment checks run each tool, not just find the executable.  
- Make counting tools fail on a missing input rather than report zero (as `stats.py` did).

### 5.3 Make repair a feature

- Provide a requeue command, atomic open and close appends, and a repair helper that writes a backup and a note with before-and-after counts.  
- Emit an event when an artifact is deleted or superseded.  
- After fixing a tool, list every artifact that consumed its output and regenerate each.  
- Fix a small defect where it is found, or ticket it to a named step.  
- Read lint-suppression counts as a design signal. The modules with the most are the ones to split.

## 6\. External services and rate limits

- Put every external call behind one queue-driven client that owns ordering, spacing, the raw-response cache, logging, retries and budgets; nothing else sends.  
- Save each raw response with a provenance sidecar before processing, and make processing a replayable hook.  
- Make budgets hard stops with exit codes and warnings at 50% and 90%. Give a budget that a later gate sets a concrete pre-gate value (0 for downloads).  
- Size budgets from each call's batching factor and freeze the estimate at the approval gate.  
- Let the function that consumes a cap enforce it and refuse to exceed it; record every override as a decision carrying the new value.  
- Log every physical send, refusals included, and count retries as total sends.  
- Pre-decide the reaction to refusals. Write the wait as `wait >= max(Retry-After, floor)` and test it.  
- Before retrying a side-effecting step whose outcome is unclear, read the external state, and retry only transient errors. \[M\] K-E10-41, K-E10-42 (one group).  
- Keep slow local processing out of a rate-limited chain.  
- Give every conversion a timeout derived from the median, and try the cheaper structured source first.  
- Run a negative control (a query that must return almost nothing) before spending search budget \[R\] (queue rows 1-3).  
- Probe each source's coverage and yield on a few items before designing a channel around it.  
- Scrub secrets at the emitter and refuse key-bearing URLs at the queue.  
- Give the operator a sanctioned, recorded way to suspend a named rule.

## 7\. Agents

### 7.1 Briefs and packets

- Write one shared brief per step, byte-identical for every agent so it caches, plus a per-item packet rendered from a table (item, inputs, scratch folder, output, "open only these files"). Keep the dispatch prompt to a short pointer plus the hard prohibitions.  
- Make the pre-dispatch check a precondition: run it in a separate turn, or in one script that checks and then launches.  
- Put the shell, the OS and their traps, file sizes and a reading recipe in every brief.  
- Ask for large outputs in several writes.  
- Check the harness's rules for sub-agents before designing what they write.  
- Specify the reply: status on the first line, at most 5 lines, the output path.  
- Give agents the verifier the orchestrator will apply and have them run it before replying.  
- Enforce prohibitions that matter with permissions or wrappers, because brief text leaks.  
- Tell synthesis agents to report a suspect input table instead of computing their own denominator.

### 7.2 Work units and concurrency

- Size each agent's packet from measured volume, with a per-agent maximum; one writer per output file; one owner per shared item.  
- Batch tiny tasks.  
- Budget a repair round for open-ended design tasks (plans, tools); well-specified per-item tasks rarely need one.  
- Enforce the concurrency cap with a counter checked at launch, and never put more Agent calls in one message than there are free slots.  
- Use slot pools, not waves, and size the cap from the measured binding resource (rate limits, operator review throughput).  
- Fan out only independent items, aggregate centrally, and start from a single agent  
- Merge passes that read the same large input into one agent context unless the second pass must be independent.

### 7.3 The dispatch ledger

- Write ledger rows through one function: `open` at the real launch with the agent id; `close` by append from the harness's completion notification (tokens, tool uses, duration); separate prepared, launched and reported stamps; an attempt number that increments; the step passed in; the matching event written in the same call.  
- Drive dispatch from a script-generated target list.  
- Log a resumed agent as its own row.  
- Count agents only from the ledger.

### 7.4 Deadlines and liveness

- Set deadlines you can observe and act on: measure active time apart from wall time, and let a watchdog flag or re-dispatch.  
- Give every agent a deadline, including the closing-step and retrospective agents.

### 7.5 Models

- Set each agent's model explicitly.  
- Name model tiers relative to the pinned default, and write pilot triggers that hold whatever a gate decides.  
- Treat a 3-item tier pilot as a smoke test, and keep measuring tier agreement during the run before moving bulk work to a cheaper model.  
- Choose each step's model by measuring it on that step's tasks. Never adopt a router that has not beaten always-small, always-mid and always-large on your own tasks, counting its own calls.

## 8\. Operator decisions and gates

- Ask every decision as a structured question: 2 to 4 options, each with its cost, time, coverage and quality consequences, one recommendation, and a blocking flag.  
- Expect decisions between gates and give them a form: a decision event holding the options, the recommendation, the answer and an evidence path.  
- Pre-decide failure policies at the first gate: retry after a refusal, cap raises, fallback modes, what happens to overflow.  
- Grant standing authority as a rule over conditions ("continue unless a check fails, a ceiling is hit or a gate is due"), not as a list of steps.  
- When asking to approve an investigation, ask in the same question for the rule to apply to each outcome.  
- Compute every number in a request by script just before asking, with the counting rule stated (data rows only).  
- When a gate changes the scope, list the downstream steps whose preconditions no longer hold and what must run first if the scope widens again.  
- Never act on an item that is still pending at a gate, and generate configuration from the recorded decision instead of retyping it.  
- Offer real options, because operators do choose against defaults.  
- When an operator choice removes a check's input, list the items that lost the check and decide on a compensating control.  
- Reconcile the operator's standing policies with the workflow's tool steps at kickoff.  
- Push progress during long phases: done and total, rate, and an ETA from a pilot that includes the slow tail.

Gate packets:

- Build them by script as numbered tables, put demand next to its limit, and end each section with the exact choice requested.  
- Include the recommended option, the alternatives with their cost, time and coverage effects, the known data-quality risks and reconciled counts.  
- Freeze each packet as presented and append the decision; write the post-decision state to a separate file.  
- Write `gate_requested` the moment the packet is shown.  
- Give the closing gate an "accept as exception" category with an owner and a carry-forward entry.

## 9\. Verification and quality measurement

- Make a deterministic verifier the acceptance gate, give agents the same verifier, and never loosen it; change it only by a recorded, narrow, tested decision.  
- Re-run the verifier after every later edit and keep a real round counter.  
- When a check rejects good items, fix the estimator with a regression test and record that the threshold stayed.  
- Keep the evaluation set away from the agents that tune against it, and require a minimum test-set size before a pass rate counts.  
- Derive negative probes from every rejection code a downstream gate applies.  
- Feed known-answer fixtures straight into the gate code, and report "not exercised" separately from "passed".  
- Choose fixtures clearly inside the scope.  
- Re-validate recall and precision at the operative threshold after every budget-driven cut, and report what each cut removed.  
- Define every metric once in code (stage, numerator, denominator), count distinct entities, and never count items admitted by hand.  
- Specify what an audit must measure (precision, false-negative rate, sample sizes), not only what it rescued.  
- Check every gate field taken from a secondary source against the primary artifact, for the whole admitted set, before any expensive step.  
- For second reads, use a narrow trigger or a sample, keep them blind, apply one adjudication rule in every double-read step, and record each layer's change rate.  
- Measure agreement per label on an early sample, and decide in advance what a disagreement does (downgrade, third read, report only).  
- Blind-check a random sample of the agreed judgements too.  
- Make `step_end` refuse to write unless the step's last required check passed.  
- Tag each check with its own policy and check ID.  
- Calibrate heuristic screens per source format, track their false-positive rate, and verify an agent's safety verdict on the flagged evidence yourself.  
- After every batch, reconcile item states by script against the expected set instead of reading the last stop message.  
- Turn every risk an agent writes into its plan into a check that runs on the first live result.

## 10\. Time, telemetry, cost and context

### 10.1 Event model

- Before choosing a time-based KPI, design an event model that gives every second a class: working, awaiting the operator, awaiting a permission, rate-limit wait, session paused, agents running. Add agent records (start, end, attempt), wait records (start, end, cause), decision records, refusal events, an "awaiting operator" step state and an "approved with changes" gate decision.  
- Have tools enforce pause records: refuse an event more than N minutes after the previous one unless it carries a pause reason.  
- Write every record when the event happens.  
- Validate every event against the schema at write time, because an append-only log cannot take a bad entry back.  
- Derive each event's level from its type in one mapping.  
- Keep the run-record schema small at the core with optional sections, write empty categories as explicit zeros, and point to source logs instead of copying rows.  
- Publish each metric's formula and time window beside it.  
- Report the time profile two ways: gaps of more than xx minutes between events and time with no event and no agent running.

### 10.2 Never wait passively

- Give every background job a progress file, a timeout and a scheduled check by the orchestrator, and never end a turn on a passive wait.  
- Emit a one-line status at fixed intervals during long turns, and treat the harness's silence reminders as a defect signal.

### 10.3 Cost

- Track tokens per verified output, split into producing and verifying.  
- Budget from the per-item fan-out and its verification layer.  
- Budget by role (count × active minutes × tool calls), not by step.  
- Keep the orchestrator lean; its whole context is re-read on every turn.  
- If spend matters, enforce a token or dollar budget per step before dispatch, by reservation.  
- Log tokens per call as cached input, uncached input and output, attributed to the role.  
- Score cost per successful output next to quality and keep the Pareto set.  
- Track a fixed metric set on every run. Every "continue", "go" or progress question marks a place where the workflow could not proceed or report on its own.

### 10.4 Context

- Assume the harness will compact the context without warning. Keep all run state on disk so a compaction equals a hand-off, and rerun the entry reconciliation after one.  
- Feed each step a bounded, curated selection rather than the history.

## 11\. Discovery, search and selection

These rules apply to any step that finds candidate items and filters them.

- Run count-only probes before the planning gate, so plans are approved against measured sizes.  
- Express monotonic requirements as structure a linter can check before any request is spent.  
- Make accepting a truncated sample an explicit, logged decision that states its recall risk.  
- Persist each refinement decision in the same write as the request it triggers.  
- Define a cross-cutting criterion once, in a shared list that parallel agents may extend but not redefine, and review it across agents at the gate.  
- Filter boilerplate before harvesting expansion terms, and apply the same band rules to expansion queries.  
- Report the marginal yield of every rescue or expansion pass.  
- Run cheap metadata gates before expensive scoring and reading.  
- Derive acquisition caps from measured funnel ratios at the gate, or state in advance what happens to overflow.  
- Move the remaining budget toward the higher-yield channel after the first pass (§6).  
- When a channel returns nothing on a topic, widen the channel before concluding the topic is unstudied.

## 12\. Environment, harness and collaboration

- Prepare the permission layer before an unattended run: allowlist the exact commands the workflow uses, make every file change through the native Write and Edit tools, and keep shell calls short and single-purpose, without heredocs or command substitution. Give agents the same rule.  
- Keep each command to one purpose with a checked exit code.  
- Name the shell and its traps in every brief, or require edits through Python or the native tools. Never build a command or path list from an unquoted string.  
- In a shared working tree, stage by explicit path, commit at small checkpoints, check `git log` against the step's expected file set before each step commit, and record outside commits that touched the run's folders.  
- Put a step's commit hash in the next log entry or the operator report; an entry cannot contain its own commit's hash.  
- Record session pauses even when no hand-off happens.  
- During the dry run, verify each harness behaviour the spec relies on: whether sub-agents may write report files, the default scratch location, how to wait on a background job, and the time limit on foreground commands.

## 13\. Synthesis, deliverables and close-out

Synthesis:

- Keep every number with its setting and never average across settings; classify each disagreement as one of setting, measurement, definition or fact.  
- Grade evidence by independent sources, not by the number of findings.  
- Keep "no evidence in scope" apart from "refuted", and treat failure modes as a first-class kind of finding (139 of 542 cards, 18 of the 52 strong ones).  
- End every analysis with an explicit list of unknowns tied to the next action.  
- Measure what each automatic pre-step contributes, and drop or fix it when its output is close to its input.

Deliverables:

- Route every operator decision that removes items (caps, waves, deferrals) into the deliverable's caveats automatically.  
- State what was read and what was not, and size the output by the evidence.

Close-out:

- Classify every artifact as scratch or record in the spec. Before cleanup, promote every file that a gate ruling, an exception, a repair or the retrospective cites, and make cleanup fail if a cited path would vanish. The sibling run kept its briefs in `logs/evidence/briefs/` before deleting its cache.  
- Keep backups outside scratch.  
- End with one machine-readable carry-forward list: item, owner, evidence path outside scratch.  
- Keep a fixed log-entry schema: State; Produced (counts from scripts); Deviations or decisions; Defects found and fixed; Open items; Next.  
- Require a deviations-and-mistakes section in every step report, and back up before any repair of an append-only record.  
- End the run with a measured critical-path report and a scored, evidence-cited change list.

## 14\. Checklists

Design review, before the spec is frozen:

- [ ] Success metrics defined in code (stage, numerator, denominator), with the events that make them computable.  
- [ ] Every item route has an ID form, a terminal status and a locator rule, fallbacks and gate deferrals included.  
- [ ] Every event type has required detail fields in the schema, validated by one emitter.  
- [ ] Every rule has one home; the kickoff and the briefs are generated from it.  
- [ ] Every step follows the template (§4.4), gate steps included, with done-when scripts.  
- [ ] Failure policies and standing authority are decided at the first gate, as rules.  
- [ ] Every budget has a pre-gate value and a batching factor; every step has a token or dollar budget if spend matters.  
- [ ] Every agent kind has a work-unit size, an explicit model, a watched deadline and one writer per output.  
- [ ] Evaluation sets and gate fixtures are held out, fed straight into gate code, and include negatives for every rejection code.  
- [ ] Every artifact is classified as record or scratch; cited evidence goes to record.  
- [ ] An independent reader has listed ambiguous rules and unrouted items, and a linter has checked the step graph.

Before the run:

- [ ] Spec and config hashes are written to `run_start`.  
- [ ] The allowlist covers the run's commands; orchestrator and agents edit with native tools; briefs name the shell and OS traps.  
- [ ] Core-kit tests pass, including the operator's numeric rules, two-item concurrency, a midnight rollover and replay of saved responses.  
- [ ] Count probes, stage timings with their tails, channel yields and metadata error rates are measured.  
- [ ] Each step has been dry-run on a small real slice.  
- [ ] The operator's standing policies are reconciled with the tool steps (formatters, automatic fixes, approvals).

Every step:

- [ ] Entry: reconcile the disk against the logs, with the disk winning; again after any context compaction.  
- [ ] Dispatch only through the counter and the scoped pre-check, from a script-generated target list; the ledger row opens at launch.  
- [ ] Background jobs have progress files, timeouts and scheduled checks; status goes to the operator on a schedule.  
- [ ] Every number in a report or request comes from a script run at that moment.  
- [ ] Exit: the done-when script passes; stamps are checked; the log entry follows the fixed schema with deviations and defects; the commit stages explicit paths.

Every gate packet:

- [ ] Numbered tables built by script; demand next to its limits; reconciled counts.  
- [ ] Options with cost, time, coverage and quality effects; one recommendation; known data-quality risks.  
- [ ] Asked as a structured question; `gate_requested` written when shown; packet frozen; decision appended.  
- [ ] Downstream steps whose preconditions the decision changes are listed.

Close-out:

- [ ] Every cited path promoted out of scratch; cleanup refuses if a cited path would vanish.  
- [ ] Operator decisions that removed items appear in the deliverable's caveats.  
- [ ] Every consumer of a fixed tool regenerated.  
- [ ] One carry-forward list with owners and evidence paths.  
- [ ] A retrospective built from the measured critical path with attributed waits.

## 15\. What this guide cannot tell you

- Whether the overnight approval waits cost real time: operator presence was not logged, and the operator may have been away anyway.  
- The time cost of each defect, and the operator's working time inside gaps.  
- What the 77 second reads and 9 third reads were worth per token, beyond their disagreement counts.  
- The speed effect of turning OCR off (different papers before and after the switch), and the net gain of the faster conversion chain (the download gap fell 8.6x, but a 4 h deadlock followed).  
- Dollar cost: the ledger records tokens only.  
- Transfer: this is one run in one domain on one harness and model, corroborated in places by one sibling run; most of the survey evidence is single-run preprints.  
- The meaning of the transcript field used for approval waits, which is inferred from its name and its timing.
