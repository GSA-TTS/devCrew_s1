# Agent Control Plane

**Status**: Beta

**Change logs**:

- [09/08/2026] - Initialization

***

## Executive Summary

An agent control plane constitutes the task family of governing an agent fleet rather than any single run: registering identities and their attached authority, evaluating policy as a deterministic gate, enforcing budgets and quotas as limits rather than targets, routing requests to capability, recording what happened under whose authority at what cost, and containing failures that exist only at fleet scale. This guide provides AI agents with a structured protocol built on one separation: the control plane decides what is permitted and allocates resources, and the data plane executes the work. It specifies an identity model in which authority attaches to a registered identity rather than being inherited ambiently from whoever started a run, a default-deny policy gate at named points in the request path that denies rather than fails open when the policy engine is unavailable, a four-dimension budget ledger enforced at run and fleet scope with a declared partial result at exhaustion, a minimum event schema carrying a disclosure boundary, and detection signals with bounded responses for correlated failure, retry storms, and runaway agents. It fixes the execution-tier partition: the deterministic tier owns essentially the whole method, and the control plane holds no model-tier decision authority. It emphasizes structured execution protocols, quality assurance checkpoints, and error handling procedures so that an agent never widens its own authority scope.

***

## I. Foundational Concepts and Definitions

### 1.1 Core Terminology

**Control plane**: The layer that governs an agent fleet rather than any single run. It owns registration and identity, policy and authorization, budgets and quotas, routing to capability, observability, and lifecycle. It decides what is permitted and allocates resources; it does not perform the work.

**Data plane**: The layer that executes admitted work. It carries requests, invokes tools, runs models, returns results, and enforces the control plane's decision at the point where an effect can occur.

**Agent identity**: A registered, unique, non-transferable identifier bound to one agent deployment, its owner, its environment, its tenant scope, and its lifecycle state. Identity is issued by the control plane, never asserted by the agent.

**Authority scope**: The complete set of capabilities, data classes, destinations, side-effect classes, and budgets an identity may exercise. Authority attaches to an identity; it is not inherited ambiently from whichever process, session, or human initiated a run.

**Non-amplification invariant**: An agent never widens its own authority scope, and a delegation to a sub-agent grants a subset of the delegator's scope, never a superset and never an unrelated addition.

**Policy gate**: A deterministic evaluation point in the request path that returns exactly one of allow, deny, require-approval, or allow-with-constraints over a canonical input, and returns it without model inference.

**Default-deny posture**: The gate's behaviour when no rule grants the request, when a required attribute is missing or ill-typed, when policy is staler than its declared bound, or when the policy engine is unreachable. The result is deny in every one of those cases.

**Budget ledger**: The declared numeric limits on tokens, tool calls, wall clock, and money, held per run and per fleet, decremented by reservation before dispatch rather than by accounting after the fact.

**Quota**: A shared-resource limit held above the run, scoped to a tenant, an agent class, a capability, a destination, or the fleet, that no single run may exhaust.

**Execution grant**: A short-lived, single-purpose credential issued after the gate allows, bound to an exact capability version, a canonical argument hash, a destination, a deadline, and a reserved budget allocation.

**Capability descriptor**: The immutable registered record of one capability version: identifier, owner, schema hashes, side-effect class, reversibility class, required scopes, data classes, permitted destinations, cost estimate, health state, and lifecycle state.

**Lifecycle state**: The registered status of an identity or capability version, drawn from a closed vocabulary: draft, validating, approved, canary, active, degraded, quarantined, deprecated, disabled, or retired.

**Declared partial result**: A terminal output emitted when a budget or quota is exhausted, stating what was completed, what was not attempted, and what remains unverified, in place of silence or an unmarked fragment.

**Disclosure boundary**: The rule separating decision metadata, which is logged, from hidden reasoning content and raw sensitive payloads, which are not.

**Correlated failure**: Simultaneous failure of many agents sharing one dependency, one configuration version, one credential, or one model endpoint, where the fleet-level symptom is a step change in a common failure class rather than a distribution of unrelated errors.

**Retry storm**: Amplification in which retries across the fleet exceed the capacity the retried dependency lost, converting a recoverable degradation into an outage.

**Runaway agent**: A single identity whose consumption of a shared quota rises without a corresponding rise in verified completions, starving the remaining fleet.

**Reconciliation**: The continuous comparison of signed desired state against observed actual state across registries, policy bundles, credentials, enforcement points, and kill switches, followed by bounded corrective action.

### 1.2 The Control Plane and Data Plane Separation

**The separation stated**: The control plane decides what is permitted and allocates resources. The data plane executes the work. This division is the guide's organising distinction and every later requirement derives from it. The separation is well established outside agent systems: a cluster control plane exposes an API, persists desired state, and runs controllers that drive actual state toward it, while worker components run the workloads [1]; a service mesh separates a control plane that manages configuration from proxies that mediate workload traffic [2].

**What mixing produces**: A system in which the two planes are fused permits an agent to grant itself budget or authority mid-run, because the component that executes the work is also the component that decides what the work may do. This guide prohibits exactly that. An agent proposes an intent; the control plane resolves that intent to a versioned capability, binds it to authenticated identities, evaluates policy over canonical arguments, admits only bounded work, records the decision, and dispatches to a separately constrained executor. The executor, not the model, owns side effects.

**Complete mediation**: Every consequential path must cross an enforcement point the data plane worker cannot bypass. A control plane that can be circumvented by calling a tool, a secret store, or a peer agent directly is an observability product, not an enforcement boundary. Bypassability is measured, not assumed: the fleet-health procedure in Phase 6 requires a signed probe attempting each known bypass path at least once per 24 hours.

**Agent-specific addition**: The cluster and mesh analogy is incomplete in one respect. The same capability may be permitted for one principal, record, argument, destination, purpose, or workflow stage and denied for another, so some decisions cannot be resolved from configuration alone and must be evaluated inline at invocation time against the request itself.

**Boundary against the per-call invocation contract**: This guide owns the fleet-governance layer. The contract for one individual tool invocation, covering schema declaration, argument validation, result typing, and per-call error handling, is owned by the companion tool-use and function-calling guidance and is not restated here. This guide specifies where in the request path that per-call contract is gated, budgeted, logged, and revoked, not how the call itself is shaped.

**Boundary against routing**: This guide specifies routing only as a control-plane function: deterministic eligibility filtering, admission, and version resolution. The selection of a model, a specialist agent, or a ranking strategy among already-eligible candidates is a separate task family, and dedicated routing guidance is planned for this corpus but does not yet exist. Where this guide names a ranking step, it constrains that step rather than specifying its internals.

### 1.3 The Entry Gate: When a Control Plane Is Warranted

A control plane is infrastructure with a standing cost. Agents must evaluate a cheap entry gate before provisioning one, bounded to 2 percent of the projected first-quarter operating cost of the fleet it would govern, returning provision, defer with a named substitute, or federate.

**Provisioning conditions**: Provision a networked control plane where at least one of the following holds: more than 1 agent, framework, team, tenant, or environment must follow common policy; capabilities or identities change independently of model deployments; any task reads private data, crosses a trust boundary, changes state, spends money, changes permissions, or contacts a person; the capability catalog exceeds 30 entries, at which point full-catalog exposure degrades selection and inflates context cost; operations require approval, cancellation, durable recovery, cost limits, or emergency disablement; or an auditor must reconstruct who proposed, approved, authorized, executed, and verified an action.

**Deferral conditions**: Defer where a single-process, single-principal, read-only deployment holds no more than 3 trusted local capabilities, touches no sensitive data, produces no side effects, and requires no central governance. The substitute is an in-process typed registry with a deterministic validator, holding the same interface shape so the agent is not taught a call path that later enforcement must remove.

**Federation conditions**: Federate rather than centralise where data residency, regulatory isolation, latency, or availability requirements forbid routing the request byte path through one region. Centralise authority and evidence semantics; distribute enforcement points and cached decisions deliberately. A regional cache must never create authority absent from the global policy.

**Entry Gate Decision Table**:

| Observable condition | Governance requirement | Gate verdict |
| :-- | :-- | :-- |
| 2 or more agents, teams, or tenants under common policy | Shared identity and policy authority | Provision |
| Any side effect, spend, permission change, or external contact | Inline enforcement before effect | Provision |
| Capability catalog above 30 entries | Policy-aware filtering and disclosure | Provision |
| Audit must reconstruct authority for an action | Correlated append-only evidence | Provision |
| Data residency or regulatory isolation binding | Local enforcement, global authority | Federate |
| Decision-path latency budget below 50 milliseconds | Local decision cache with signed bundles | Federate |
| 3 or fewer local capabilities, read-only, no sensitive data | Type checking only | Defer; use a typed registry |
| Application already knows the exact operation | Authorization only, no selection | Defer selection; retain the gate |

**Numeric gate rules**: Provision where at least 1 provisioning condition holds. Where the projected control-plane cost exceeds 25 percent of projected fleet execution cost and no provisioning condition names a side effect, sensitive data, or an audit obligation, defer and record the estimate for the next review. Where the gate defers, the identity, policy, and evidence interfaces are still declared, because retrofitting an enforcement boundary onto a fleet that has learned to bypass it is the most expensive correction in this method.

### 1.4 The Execution-Tier Partition

The partition below is a design requirement of the method, not an artifact of current model capability. The control plane contains no model-tier decision authority at any point.

**Deterministic tier**: Identity issuance and binding, authority-scope computation, delegation attenuation, policy evaluation, budget accounting, quota reservation and release, eligibility filtering, admission and load shedding, version resolution, grant issuance and expiry, canonicalization, idempotency, event emission, retention enforcement, circuit breaking, kill-switch activation, and reconciliation. Each requires exactness, reproducibility, auditability, or a scale that model inference cannot supply. Each is expressed as a query, a schema validation, an arithmetic operation, or a policy-engine evaluation.

**Model tier**: Work inside the data plane only. The model proposes an intent, drafts arguments, interprets a returned result, and decides what to attempt next within an already-granted authority scope. The model tier holds no authority over any deterministic-tier artifact and never decides whether an action is permitted.

**Hybrid tier**: Two handoffs and no more. First, capability selection: the deterministic tier computes the eligible set and the model ranks within it, with the deterministic tier holding authority, so a model selection outside the eligible set is rejected rather than reconciled. Second, argument repair: the deterministic tier returns a structured validation error and the model proposes a correction, with the deterministic tier re-running every check from the beginning, so a repair that changes intent, recipient, destination, amount, data scope, or side effect is rejected as a new proposal rather than accepted as a fix.

**Execution-Tier Ownership by Artifact**:

| Artifact | Owning tier | Authority on disagreement |
| :-- | :-- | :-- |
| Agent identity and authority scope | Deterministic | Deterministic; no model input accepted |
| Policy decision and reason code | Deterministic | Deterministic; model reasoning is never a policy result |
| Budget ledger and quota reservation | Deterministic | Deterministic; model estimates are advisory only |
| Eligible capability set | Deterministic | Deterministic; selections outside the set are rejected |
| Ranking within the eligible set | Hybrid | Deterministic constrains; model orders |
| Canonical arguments and idempotency key | Deterministic | Deterministic; model-supplied values are stripped |
| Proposed intent and draft arguments | Model | Deterministic validation is final |
| Result interpretation inside a granted scope | Model | Deterministic verification of postconditions is final |
| Event record and retention class | Deterministic | Deterministic; no model redaction judgement |
| Kill-switch activation and reconciliation | Deterministic | Deterministic; never model-initiated |

**What the deterministic tier rejects unconditionally**: A request carrying a model-supplied tenant, principal, role, scope, approval status, idempotency key, or budget field; a capability reference that does not resolve to an approved immutable version; a grant presented after its expiry; a delegation whose scope exceeds its parent; a policy decision produced by anything other than the pinned engine over the canonical input; and a write dispatched without a persisted durable record preceding it.

***

## II. Operational Framework: Fleet Governance Through a Non-Bypassable Decision Path

The framework assumes the entry gate in Section 1.3 has returned provision or federate. Phases 1 and 2 are configuration phases executed before any run is admitted and re-executed on every material change. Phases 3 through 5 execute on every run. Phase 6 runs continuously across the fleet and does not terminate with any single run. An agent operating within an established control plane executes Phases 3 through 5; an agent configuring one in an agent-managed deployment executes Phases 1, 2, and 6 as well.

### Phase 1: Identity and Authority Registration

**Objective**: Bind every agent instance and every capability version to a registered identity carrying an explicit authority scope, so that what an agent may do is a property of a record rather than a property of whoever started it.

#### Step 1.1: Register the Agent Identity and Its Authority Envelope

**Required Actions**:

- Issue one unique workload identity per agent deployment, bound to owner, human sponsor, environment, tenant scope, region, model and orchestrator versions, and attested runtime, using short-lived verifiable identity documents rather than static workload secrets [9].
- Issue separate identities for development, staging, and production, and for any two authority classes that differ in side-effect class or data class.
- Record the authority envelope as an explicit enumeration of permitted capability namespaces, data classes, destination classes, side-effect ceiling, maximum delegation depth, and budget profile.
- Reject any registration whose authority envelope is expressed as an exclusion list rather than an enumeration, because an exclusion list grants every capability added after it was written.
- Set the initial lifecycle state to draft and require an owner attestation before any transition to approved.
- Preserve both the workload identity and the delegated principal on every user-bound action, and never collapse an agent acting for a named principal into a shared service account.

**Required Outputs**:

- One agent identity record per deployment, with owner, sponsor, environment, tenant scope, and attested runtime.
- An authority envelope enumerating permitted namespaces, data classes, destinations, side-effect ceiling, delegation depth, and budget profile.
- A lifecycle state field drawn from the closed 10-state vocabulary in Section 1.1.

**Quality Checkpoints**:

- Every deployed agent resolves to exactly 1 registered identity, and 0 agents operate under a shared identity.
- Every authority envelope is an enumeration; 0 envelopes are expressed as exclusions.
- No identity spans 2 environments and no identity spans 2 side-effect classes.
- Identity issuance is disabled within 60 seconds of the owning agent record entering disabled or retired state.

***

#### Step 1.2: Register Capability Descriptors and Their Lifecycle State

**Required Actions**:

- Register each capability version as an immutable descriptor carrying identifier, namespace, owner, provenance attestation, semantic version, input and output schema hashes, description hash, side-effect class, reversibility class, required scopes, data classes, permitted destinations, region constraints, timeout, retry semantics, idempotency behaviour, cost estimate, approval class, health state, and deprecation deadline.
- Publish by atomic pointer or signed manifest, never by in-place mutation of a descriptor an approved run may already hold.
- Classify every capability into exactly 1 side-effect class from the closed set: public read, private read, reversible write, externally visible write, financial or security change, destructive, privileged administration, or arbitrary execution.
- Require a major version increment for any new side effect, broadened destination, changed unit, changed identity semantics, renamed required field, or changed error meaning.
- Expose only descriptors in approved, canary, or active lifecycle state, and treat a passing health check as insufficient to override lifecycle or policy.
- Re-run the registration validation suite on any change to a schema hash or description hash, since a changed description is a changed instruction to the model tier.

**Required Outputs**:

- An immutable capability descriptor per version, with the full field set and a recorded content hash.
- A side-effect classification assigning exactly 1 class per capability version.
- A lifecycle state and deprecation deadline per version.

**Quality Checkpoints**:

- 100 percent of exposed capability versions carry an owner, a provenance attestation, and a side-effect class.
- 0 descriptors are mutated in place; every change produces a new immutable version.
- Any descriptor whose description hash changed without a validation run is quarantined within 1 reconciliation cycle.
- The registry rejects a second registration under an identifier already held by a different owner.

***

#### Step 1.3: Bind Delegation as Monotone Attenuation

**Required Actions**:

- Record every delegation as a durable record naming source and target identities, originating principal and tenant, purpose, task subset, allowed capability namespaces, data-class ceiling, destination constraints, budget allocation, deadline, remaining depth, policy version, and parent delegation identifier.
- Compute the child authority scope as a subset of the parent scope, and reject any delegation request whose computed scope contains an element absent from the parent.
- Cap delegation depth at 3 for interactive work and 5 for durable background work, and refuse a delegation that would exceed the cap rather than truncating it silently.
- At a branch join, grant the intersection of the inherited scopes, and require a fresh authorization record where a broader scope is genuinely needed.
- Re-anchor every consequential decision to the original request and the current policy, rather than to a paraphrased handoff produced by an intermediate agent.
- Prohibit any path by which an agent submits its own scope, tenant, role, clearance, or budget; the control plane computes these from trusted state and strips model-supplied values before evaluation.

**Required Outputs**:

- A delegation record per sub-agent invocation, carrying parent identifier and remaining depth.
- A computed child authority scope with a recorded subset proof against the parent scope.
- A rejection record for every delegation refused for scope excess or depth exhaustion.

**Quality Checkpoints**:

- 0 delegations hold an authority element absent from the parent scope.
- 0 runs exceed the declared delegation depth cap.
- Every delegation record resolves to a parent record or to the originating run, with no orphans.
- The originating principal and tenant are present and unchanged at every depth.

***

### Phase 2: Policy Declaration and Gate Placement

**Objective**: Establish policy evaluation as a deterministic gate at named points in the request path, with a default-deny posture and a stated behaviour when the policy engine is unavailable.

#### Step 2.1: Declare the Policy Input Schema and Decision Shape

**Required Actions**:

- Declare a canonical policy input schema containing the authenticated principal and agent identities, tenant, delegation chain, purpose code, environment, region, capability identifier and version, canonical arguments, resource and relationship attributes, destination class, input and output data classes, workflow stage, prior decisions, approval artifact, timestamp, budget state, and risk class.
- Canonicalize every argument before evaluation, resolving aliases, encodings, redirects, and relative references, so that two textually different requests with the same effect produce the same policy input hash.
- Return a structured decision rather than a boolean: effect drawn from allow, deny, require-approval, or allow-with-constraints; a decision identifier; engine and bundle versions; reason codes; obligations; filtered fields; maximum result class and size; credential scope; deadline; quota allocation; approval class; and expiry [4][5].
- Compose the authorization models to the question rather than adopting one: coarse role assignment for administrative duties, attribute evaluation for tenant, purpose, data class, time, risk, and destination, relationship evaluation for ownership and assignment questions, and attenuated capability grants for delegated operations [6][7].
- Evaluate policy over arguments, not only over capability names, covering recipients, account identifiers, record filters, paths, resolved destinations, amounts, date ranges, batch sizes, and requested permissions.
- Return to the model tier a stable reason code only, never the policy body, the matched rule text, or any hint that assists evasion.
- Prohibit network calls and mutable side effects inside policy evaluation; supply external data as bounded, freshness-labelled input.

**Required Outputs**:

- A canonical policy input schema with every field typed and a declared required or optional status.
- A structured decision record per evaluation, carrying decision identifier, effect, bundle version, and reason codes.
- A canonicalization specification stating the normal form for every argument class.

**Quality Checkpoints**:

- 100 percent of runtime decisions are produced by the pinned engine over the canonical input; 0 are produced by model inference.
- Every decision carries a decision identifier and a bundle version, enabling offline replay.
- 0 policy bodies, rule texts, or matched-rule identifiers reach model context.
- Two requests differing only in argument encoding produce the same policy input hash in 100 percent of canonicalization tests.

***

#### Step 2.2: Place the Gate at Named Points in the Request Path

**Required Actions**:

- Place the gate at exactly 4 named points and record which point produced each decision: run admission, before capability disclosure, immediately before dispatch, and before any result classified above the run's output data class is returned.
- Require that the pre-dispatch evaluation be the last operation before the executor receives the grant, with no intervening step able to alter arguments, destination, or identity.
- Locate enforcement at ingress, at the capability gateway or execution broker, at the sandbox broker where arbitrary execution exists, at the peer-agent boundary, and at the downstream service where it can independently authorize [14][15][16].
- Require downstream services to enforce authorization independently rather than trusting a header asserted by an upstream component reachable from an arbitrary network.
- Treat every returned artifact, document, message, and metadata field as untrusted data and never as authority, including capability descriptions and peer-agent messages, since descriptions of behaviour are untrusted unless obtained from a trusted server [17].
- Prohibit the model tier from converting a denied action into an equivalent effect through a different channel, by evaluating destination and data class at the effect boundary rather than at the capability name.
- Verify non-bypassability by a signed probe attempting each known bypass path, run at least once per 24 hours and after every topology change.

**Required Outputs**:

- A gate placement record naming the 4 evaluation points and the enforcement component at each.
- A bypass-probe result set covering every known direct path to a capability, a secret store, or a peer agent.
- An enforcement-point inventory with independent-authorization status per downstream service.

**Quality Checkpoints**:

- 100 percent of consequential dispatches carry a decision identifier produced at the pre-dispatch point.
- The bypass probe reports 0 successful bypasses in the most recent 24-hour window.
- 0 arguments, destinations, or identity fields change between the pre-dispatch decision and the executor's receipt of the grant.
- Every downstream service in the inventory is marked as independently authorizing, or is listed with a dated remediation owner.

***

#### Step 2.3: Declare Unavailability Behaviour and Staleness Bounds

**Required Actions**:

- Declare deny as the result whenever the policy engine is unreachable, the bundle fails signature verification, a required attribute is missing or ill-typed, or the loaded bundle is staler than its declared bound. Failing open is prohibited for every consequential action.
- Set a maximum staleness per distributed artifact: 300 seconds for policy bundles, 300 seconds for capability catalogs, 60 seconds for credential revocation state, and 30 seconds for kill-switch state. An enforcement point unable to prove freshness within its bound restricts to read-only or denies according to risk class.
- Propagate emergency denies, revocations, and kill switches on an accelerated channel separate from ordinary configuration distribution, targeting first confirmed enforcement within 60 seconds and full fleet confirmation within 300 seconds.
- Permit a documented restricted mode only for read-only, non-sensitive operations against a local allowlist, bounded to 900 seconds, issuing no new credentials, raising an alert on entry, and reconciling every decision made in that mode afterwards.
- Prohibit restricted mode for writes, cross-tenant access, sensitive egress, credential issuance, and administrative operations without exception.
- Distribute policy as signed immutable bundles through offline replay, shadow evaluation, canary enforcement, and phased enforcement, and require named review for every broadened allow observed in differential replay.

**Required Outputs**:

- A declared unavailability behaviour per enforcement point, stating the denied classes and any permitted restricted mode with its bound.
- A staleness bound per distributed artifact with the observed propagation lag distribution.
- A differential replay report classifying each decision change as expected allow, expected deny, unexpected broadening, unexpected restriction, or indeterminate.

**Quality Checkpoints**:

- 0 consequential actions are permitted during any policy-engine outage.
- Configuration stale-read rate stays at or below 0.1 percent of runtime decisions; a higher rate halts new rollouts.
- Every restricted-mode entry produces an alert and a reconciliation record, with 0 unreconciled entries after 24 hours.
- 0 broadened allows reach canary enforcement without a named owner recorded against them.

***

### Phase 3: Budget and Quota Enforcement

**Objective**: Convert budgets and quotas from advisory targets into enforced limits held by the control plane, so that exhaustion terminates a run cleanly with a declared partial result rather than degrading the fleet.

#### Step 3.1: Declare the Budget Ledger Across Four Dimensions and Two Scopes

**Required Actions**:

- Declare a numeric limit on each of 4 dimensions for every admitted run: tokens, tool calls, wall clock, and money. A run with an undeclared dimension is refused at admission rather than admitted with an implicit limit.
- Declare the same 4 dimensions at fleet scope, partitioned by tenant, agent class, capability family, destination class, and global pool, so that no run's limit is the only thing standing between one agent and the shared resource.
- Separate read, write, approval, evaluation, and administrative pools so that one class of work cannot starve another.
- Attach a default budget profile to every registered agent identity, and require that a run's requested budget be a subset of its identity's profile, rejected on excess rather than clamped silently.
- Record the money dimension in a single declared currency, converting provider costs at a recorded rate rather than mixing units.
- Prohibit any path by which the model tier proposes, amends, or extends a budget. A budget increase is a management-plane write requiring a distinct authority and producing a new versioned record.
- Set default interactive-run ceilings of 8 model turns, 12 logical tool calls, 2 selection rounds, and 2 argument repairs, and raise them only inside a durable workflow with monitoring and no increase in authority.

**Required Outputs**:

- A budget ledger per run with a numeric limit and current consumption on each of the 4 dimensions.
- A fleet-scope quota table partitioned by tenant, agent class, capability family, destination class, and global pool.
- A per-identity budget profile recorded on the agent identity record.

**Quality Checkpoints**:

- 100 percent of admitted runs carry a numeric limit on all 4 dimensions.
- 0 runs hold a budget element exceeding the requesting identity's profile.
- Every fleet-scope pool has a declared limit and a declared starvation floor reserved for other classes.
- 0 budget amendments originate in the model tier.

***

#### Step 3.2: Reserve Atomically Before Dispatch and Release on Completion

**Required Actions**:

- Reserve the estimated consumption on every affected dimension and scope atomically before dispatch, and refuse the dispatch where any scope cannot satisfy the reservation.
- Bind the reservation to the execution grant, so that a grant presented without a live reservation is rejected at the enforcement point.
- Release unused reservation immediately on completion, cancellation, or grant expiry, and reconcile any reservation outstanding longer than the grant deadline plus 60 seconds.
- Record estimated and actual consumption per attempt, and use the observed ratio to correct future estimates rather than to retroactively amend the ledger.
- Count retries against the budget as separate attempts, so that retry amplification is visible in cost rather than hidden inside a single logical call.
- Meter the control plane's own consumption against a distinct pool, so that decision-path cost is measured rather than treated as free overhead.
- Deduct approval waiting time from the wall-clock dimension only where the run holds a worker or a credential open; a durably parked run consumes no wall clock.

**Required Outputs**:

- An atomic reservation record per dispatch, naming the affected scopes and the reserved units.
- A release or reconciliation record per reservation, with 0 reservations outstanding beyond the deadline grace period.
- An estimate-versus-actual consumption series per capability family.

**Quality Checkpoints**:

- 0 dispatches proceed without a satisfied reservation on every affected scope.
- Quota breach rate, measured as operations whose actual usage exceeds an enforced quota without an authorized reservation, stays at 0 for write and financial classes.
- Retry amplification, measured as execution attempts over logical calls executed, stays at or below 1.5; a value above 2.0 opens the containment procedure in Step 6.2.
- Estimate error above 50 percent for a capability family for 3 consecutive days triggers re-estimation rather than a budget increase.

***

#### Step 3.3: Terminate Cleanly at Exhaustion With a Declared Partial Result

**Required Actions**:

- On exhaustion of any dimension at any scope, stop issuing new grants for the affected run immediately, allow in-flight work holding a valid grant to complete or reach its deadline, and enter termination rather than requesting an extension.
- Emit a declared partial result naming what was completed and verified, what was completed but unverified, what was not attempted, the exhausted dimension and scope, and the consumption figure at termination.
- Distinguish the terminal states explicitly and never conflate them: completed, partial, denied, failed, compensated, and unknown.
- Where the run committed reversible side effects and a mandatory later step cannot be reached, execute the registered compensations in declared reverse order, each with its own idempotency key and verification, and report partially-compensated with an escalation where any compensation is exhausted or an effect is irreversible.
- Never invent a compensation at failure time; where no reviewed compensation exists, preserve evidence and escalate to the named owner.
- Prohibit silent truncation: a run that ends without an emitted terminal record is classified as unknown and enters reconciliation.
- Where exhaustion is at fleet scope rather than run scope, record the starving identity and enter the runaway containment procedure in Step 6.3 rather than terminating the victim runs alone.

**Required Outputs**:

- A terminal record per run carrying exactly 1 of the 6 terminal states.
- A declared partial result for every budget-exhausted or quota-exhausted termination.
- A compensation ledger listing each attempted reversal and its verification outcome.

**Quality Checkpoints**:

- 100 percent of terminated runs carry a terminal record; 0 runs end without one.
- Every partial result names the exhausted dimension, the exhausted scope, and the consumption at termination.
- 0 runs continue to request grants after exhaustion is recorded.
- Every irreversible effect left uncompensated produces an escalation to a named owner within 300 seconds.

***

### Phase 4: Capability Routing and Admission

**Objective**: Resolve a proposed intent to exactly one approved capability version through deterministic filtering followed by bounded selection, admitting only work the fleet has capacity to complete safely.

#### Step 4.1: Filter Deterministically Before Any Ranking

**Required Actions**:

- Compute the eligible set by deterministic filter before any lexical, semantic, graph, or learned ranking runs, filtering on tenant, principal, agent authority scope, purpose, environment, region, protocol, lifecycle state, health, data class, side-effect ceiling, required scopes, remaining budget, and policy eligibility.
- Treat policy as a constraint on the candidate set and never as a score contributed to a ranking, since a sufficiently high similarity score must never outweigh an ineligibility.
- Expose the full catalog to the model tier only where it holds at most 30 entries that are stable, distinct, and cheap in context; above that threshold, disclose progressively from the eligible set.
- Bound selection to at most 2 rounds, retrieving a diversified candidate set of 5 to 10 entries per round, and broaden once with alternate phrasing only where the first round returns no eligible candidate covering the task.
- Require a minimum calibrated score or a minimum margin between the top 2 candidates before accepting a selection, and return a capability-unavailable outcome rather than selecting on a tie or a below-threshold score.
- Permit abstention and clarification as first-class outcomes, and treat a selection produced without an eligible candidate as a denial rather than a fallback.
- Compute the exposed capability set per request from trusted session state, record the exact ordered set and its hash, and reject any attempt by the model tier to submit its own role, tenant, clearance, or approval status.
- Bypass model selection entirely, but never the gate, wherever deterministic application logic already knows the only valid operation.

**Required Outputs**:

- An eligible-candidate set per selection round with a recorded filter-rejection count by reason.
- An exposure record naming the exact ordered candidate set and its hash.
- A selection outcome of exactly 1 capability version, an abstention, a clarification request, or capability-unavailable.

**Quality Checkpoints**:

- 100 percent of selections resolve to a member of the eligible set computed before ranking.
- 0 selections are accepted on similarity alone without a calibrated threshold or margin.
- No selection exceeds 2 rounds; a third round is refused and returns capability-unavailable.
- 0 role, tenant, clearance, or approval fields reaching the filter originate in model output.

***

#### Step 4.2: Admit or Shed at Two Named Admission Points

**Required Actions**:

- Evaluate admission twice: once at run entry before any expensive retrieval or model work, and again immediately before dispatch, since state may have changed between them.
- Check at each point the authentication result, tenant lifecycle, agent lifecycle, risk class, data class, region constraint, capability lifecycle, budget and quota headroom, concurrency ceiling, queue depth, dependency health, policy freshness, approval requirement, and emergency-control state.
- Shed load deliberately before overload degrades throughput, rejecting excess work with a stable reason code rather than admitting it into a saturating queue [21].
- Operate tenant-fair queues with declared priority classes, and reserve a floor of at least 10 percent of decision capacity per active tenant so that no single tenant or agent class consumes all of it.
- Refuse to enqueue an already-expired request, a revoked capability, or an approval whose bound operation hash has changed, and re-evaluate policy on dequeue wherever identity, policy, configuration, or resource state may have changed while parked.
- Require a recorded human authorization before any externally visible, destructive, financial, security-affecting, or difficult-to-reverse action, binding the authorization to an operation hash over principal, agent, tenant, capability version, canonical arguments, destination, disclosed data, side-effect class, reversibility, policy version, and expiry.
- Treat an authorization as satisfying a policy precondition and never as overriding a prohibition or supplying a missing downstream permission, and re-evaluate policy immediately before dispatch after the authorization returns.
- Allow at most 1 clarification and 1 revised authorization request per intent; after a second denial or expiry, stop or escalate to the named owner rather than rephrasing the same operation.

**Required Outputs**:

- An admission decision per point with a stable reason code and the observed headroom on each checked dimension.
- A shed-request record naming the saturated resource and the applied priority class.
- An authorization artifact per gated action, carrying the operation hash and expiry.

**Quality Checkpoints**:

- 100 percent of dispatches carry an admission decision produced at the pre-dispatch point.
- Every active tenant retains at least 10 percent of decision capacity during shedding.
- 0 authorizations execute after a bound field has changed; a mismatch blocks dispatch rather than warning.
- 0 intents receive more than 2 authorization requests.

***

#### Step 4.3: Resolve to an Exact Version and Issue a Bounded Execution Grant

**Required Actions**:

- Resolve every proposed alias to an exact immutable capability identifier and version before validation, and reject a reference that resolves to a draft, deprecated, quarantined, or disabled version.
- Inject trusted identity, tenant, purpose, idempotency key, and operation identifier after stripping any model-supplied value for those fields.
- Issue a short-lived execution grant bound to the resolved version, the canonical argument hash, the destination, the reserved budget allocation, an absolute deadline, and an expiry no longer than 300 seconds for interactive work and 900 seconds for durable background work.
- Exchange the principal's authority for a narrower, audience-restricted, least-privilege credential rather than forwarding a broad token onward, and treat the exchange as constrained to the intersection of principal authority, agent authority, task purpose, and capability requirement rather than as an amplification step [8].
- Resolve secrets inside the execution broker or the worker, never in model context, prompts, schemas, capability descriptions, model-visible errors, or workflow history; store references and record a credential-reference hash instead.
- Persist the durable call record before dispatching any operation with a side effect, so that an unknown outcome is reconcilable rather than merely lost.
- Verify the returned result against its declared schema, provenance, tenant, freshness, and data class before it reaches model context, and normalize, classify, and bound its size at that point.
- Query authoritative state to verify the postcondition for every consequential claim, rather than accepting the executor's own report of success.

**Required Outputs**:

- A resolved capability identifier and version per call, recorded with the alias it replaced.
- An execution grant with bound version, argument hash, destination, budget allocation, deadline, and expiry.
- A verified result record carrying schema validation, provenance, classification, and postcondition verification outcomes.

**Quality Checkpoints**:

- 100 percent of dispatches reference an exact immutable version; 0 reference a mutable alias.
- 0 grants outlive their declared expiry, and 0 expired grants are accepted at an enforcement point.
- 0 secrets appear in model context, prompts, capability descriptions, logs, or workflow history.
- Unknown side-effect rate, measured as write calls ending without an authoritative outcome, stays at or below 0.5 percent; a higher rate halts write authority for the affected capability family.

***

### Phase 5: Observability and the Disclosure Boundary

**Objective**: Emit evidence sufficient to answer, after the fact, what an agent did, under whose authority, at what cost, and on what evidence, without retaining hidden reasoning content or raw sensitive payloads.

#### Step 5.1: Emit the Minimum Event Schema With Correlated Identifiers

**Required Actions**:

- Emit an append-only event at each of 8 mandatory points: run admission, identity binding, capability selection, policy decision, authorization, grant issuance, each execution attempt, and result verification. A logical call missing any applicable event is an audit gap, not a logging preference.
- Carry the 5 correlation identifiers on every event: trace identifier for one interactive execution path, task identifier surviving restarts and region failover, capability-call identifier for one logical proposal, attempt identifier unique per retry under one execution identifier, and delegation identifier preserving authority lineage.
- Use the established generative-AI attribute conventions where they are defined and stable, and stable namespaced attributes for the remainder, keeping sensitive content out of capture by default [23].
- Keep high-cardinality identifiers, hashes, resource names, and destinations in traces and logs rather than in metric labels, and bound metric dimensions to environment, region, tenant tier, capability family, policy bundle, effect, risk class, outcome, error class, and release.
- Never reuse an identifier across tenants, and never reuse an attempt identifier across execution identifiers.
- Chain event hashes or write to an immutable ledger wherever non-repudiation is claimed, and never describe an ordinary mutable application log as non-repudiable.
- Record the control plane's own cost allocation on the run's cost event, so that cost per verified successful task includes decision-path cost rather than only model and capability cost.

**Minimum Event Schema**:

| Field group | Required fields | Present on |
| :-- | :-- | :-- |
| Correlation | trace, task, capability-call, attempt, delegation identifiers | Every event |
| Identity | principal reference, tenant, agent identity and version, workload identity, delegation chain hash, purpose code | Every event |
| Authority | policy decision identifier, engine and bundle version, effect, reason codes, obligations, grant identifier and expiry | Decision, grant, attempt |
| Capability | capability identifier and version, schema and description hashes, canonical argument hash, destination class, side-effect class | Selection, decision, attempt |
| Cost | reserved and actual tokens, calls, wall clock, money, currency, allocated control-plane cost | Grant, attempt, terminal |
| Evidence | result schema hash, provenance, freshness, classification, redaction count, postcondition verification outcome | Verification |
| Outcome | terminal state, error class, retryability, unknown-outcome flag, external operation identifier | Attempt, terminal |

**Required Outputs**:

- An append-only event stream carrying all 8 mandatory event types per logical call.
- A correlation index resolving any 1 of the 5 identifiers to the complete run record.
- A cost record per run attributing model, capability, infrastructure, and control-plane cost separately.

**Quality Checkpoints**:

- Audit completeness rate, measured as sampled logical calls carrying every applicable mandatory event, stays at or above 99.5 percent; a lower rate blocks release.
- 100 percent of events carry all 5 correlation identifiers or a recorded reason for a null.
- 0 identifiers are reused across tenants.
- Every metric label set falls within the bounded dimension list; unbounded labels are rejected at ingestion.

***

#### Step 5.2: Enforce the Disclosure Boundary on Every Emitted Event

**Required Actions**:

- Log decision metadata and never hidden reasoning content. Reason codes, evidence references, decision identifiers, cost figures, validator outcomes, and signal source classes are recorded; private chain-of-thought and unrestricted internal transcripts are neither requested nor persisted.
- Replace raw payloads with content hashes or storage references wherever the hash or reference answers the audit question, retaining full content only where a declared obligation requires it.
- Prohibit bearer tokens, secret values, raw sensitive prompts, raw arguments, raw results, and full capability definitions from ordinary telemetry, recording reference hashes in their place.
- Scan every event against the boundary before it leaves the emitting component, and drop or quarantine a violating event rather than emitting it and redacting later.
- Where a component cannot justify a decision without exposing hidden reasoning, record the decision as unjustified and escalate, rather than relaxing the boundary for that case.
- Assign the redaction decision to the deterministic tier, driven by declared data classes and field lists; the model tier never decides what is safe to log.
- Record a redaction count per event so that under-redaction and over-redaction are both measurable rather than invisible.

**Required Outputs**:

- A disclosure-boundary specification listing the permitted field set and the prohibited field set by data class.
- A pre-emission scan result per event, with a quarantine record for every violation.
- A redaction count series by capability family and data class.

**Quality Checkpoints**:

- 0 events containing hidden reasoning content, secret values, or bearer tokens reach the evidence store.
- 100 percent of events pass a pre-emission boundary scan before leaving the emitting component.
- 0 redaction decisions originate in the model tier.
- Any detected breach halts evidence release and triggers purge and re-instrumentation before the store is reopened.

***

#### Step 5.3: Set Retention, Access, and Integrity Rules

**Required Actions**:

- Declare a retention class per event type with a numeric duration, and default to 400 days for authority and decision events, 90 days for attempt and cost events, and 30 days for high-volume selection and filtering events, adjusting only against a recorded obligation.
- Separate writer and auditor roles so that no identity can both emit and delete evidence, and record every administrative access to the evidence store as an event in that store.
- Encrypt records at rest and in transit, synchronize time across emitters, sign exports, and test restoration from backup at least quarterly.
- Scope evidence access per tenant, and run automated cross-tenant negative tests continuously rather than at release only.
- Map controls to obligations where a governance framework applies, without claiming framework compliance from architecture alone; risk-management frameworks organize ownership, measurement, and lifecycle evidence [24], statutory regimes may impose record-keeping, human-oversight, robustness, and cybersecurity requirements whose applicability depends on role and risk classification [25], and assurance criteria require demonstrated operating effectiveness of actual controls rather than a purchased tool [26].
- Compute the metric set over declared windows and cohorts, counting logical calls separately from attempts, and report percentiles rather than averages for every latency figure.
- Retain a replay corpus of canonical policy inputs, decisions, and grants sufficient to re-evaluate a bundle change offline, and replay writes only against simulators.

**Required Outputs**:

- A retention schedule naming a numeric duration per event type and its governing obligation.
- An access-control matrix separating emitter, auditor, and administrator roles with a tested restoration record.
- A metric report covering availability, decision latency percentiles, deny and false-outcome rates, drift, quota breach, retry amplification, audit completeness, and cost per verified successful task.

**Quality Checkpoints**:

- 100 percent of event types carry a declared retention class; 0 default to indefinite retention.
- 0 identities hold both emit and delete authority over the evidence store.
- Cross-tenant negative tests report 0 successful accesses in the most recent 24-hour window.
- Restoration from backup is verified within the last 90 days; a longer gap blocks any non-repudiation claim.

***

### Phase 6: Fleet Health and Containment

**Objective**: Detect and bound the three failure modes that do not exist for a single agent, so that a fleet degrades in a declared way rather than collapsing through a shared dependency, an amplified retry, or one starving identity.

#### Step 6.1: Detect and Contain Correlated Failure

**Required Actions**:

- Enumerate every shared dependency at registration time: model endpoints, policy bundles, credential issuers, capability gateways, registries, evidence backends, and regional infrastructure, recording for each the count of agent identities that would fail with it.
- Declare a concentration ceiling of 40 percent, above which no single shared dependency may serve more than that share of the fleet's consequential paths without a declared and tested fallback.
- Detect correlated failure by a step change in a single failure class: a rise above 20 percentage points within a 300-second window in the share of failures attributable to one dependency, one configuration version, one credential issuer, or one model endpoint, distinguished from an ordinary distribution of unrelated errors.
- Respond by shedding to the declared fallback for the affected class where one exists, and by restricting the affected identities to read-only where none exists, rather than by allowing every agent to retry against the failed dependency.
- Treat agreement among agents sharing a base model, a premise, or an evidence source as correlated rather than independent, and refuse to satisfy an independent-verification requirement with signals that fail the source-class test.
- Deploy decision and enforcement components across at least 2 failure domains, replicating signed configuration rather than mutable in-memory state.
- Test region evacuation, certificate failure, clock skew, queue backlog, evidence-backend outage, and dependency partition at least quarterly, and add every validated failure to a permanent regression set.

**Required Outputs**:

- A shared-dependency inventory with a blast-radius count and a declared fallback per entry.
- A correlated-failure detection rule per dependency class, with its window, threshold, and bounded response.
- A quarterly fault-injection report naming the injected failure, the observed degradation, and the recovery time.

**Quality Checkpoints**:

- 0 shared dependencies serve above 40 percent of consequential paths without a tested fallback.
- Every detected correlated failure produces a recorded containment action within 300 seconds of detection.
- 0 independent-verification requirements are satisfied by signals sharing a source class.
- Every decision and enforcement component is present in at least 2 failure domains.

***

#### Step 6.2: Bound Retry Amplification and Damp Thundering-Herd Storms

**Required Actions**:

- Assign exactly 1 retry owner per logical call and prohibit retries at every other layer, since stacked retries across client, proxy, workflow, and application layers multiply attempts geometrically.
- Retry only a classified transient failure, and only where the operation is idempotent or reconciliation has proved the earlier attempt had no effect.
- Cap attempts at 2 retries after the first for interactive work and 4 for durable background work, lowering the cap for costly dependencies, and reuse the same logical call identifier, operation identifier, and idempotency key on every safe retry [20].
- Apply exponential backoff with full jitter, honour any valid server-supplied delay, and never schedule fleet retries on an aligned interval, since synchronized retry is the mechanism by which a recoverable degradation becomes an outage.
- Open a circuit breaker when the rolling failure or latency threshold for a dependency is crossed, fail fast during cooldown, permit a small fixed number of half-open probes, and close only after the success threshold is met; bound connections, pending requests, requests, and retries rather than counting errors alone [22].
- Detect a storm by fleet-scope retry amplification above 2.0 sustained for 120 seconds, or by attempt volume against one dependency rising above 3 times its trailing 7-day peak.
- Respond by reducing the fleet retry cap to 0 for the affected dependency class, shedding new admissions for that class, and holding the reduced cap until amplification falls below 1.5 for 300 seconds.
- Place bulkheads so that a dependency, tenant, or high-cost capability cannot exhaust shared workers, connections, queues, or budgets, without creating partitions so small that capacity becomes unusable.

**Required Outputs**:

- A retry-owner assignment per capability family, with a recorded prohibition at every other layer.
- A breaker configuration per dependency naming the failure threshold, cooldown, probe count, and close threshold.
- A storm detection rule with its window, threshold, damping action, and release condition.

**Quality Checkpoints**:

- Exactly 1 layer retries any logical call; a second retrying layer is a defect halting release.
- 0 retries are issued against a non-idempotent operation whose prior attempt has not been reconciled.
- Fleet retry amplification stays at or below 1.5 outside declared incidents.
- Circuit-open rate above 5 percent of eligible execution requests for 300 seconds escalates to the dependency owner.

***

#### Step 6.3: Contain a Runaway Agent and Reconcile Desired Against Actual State

**Required Actions**:

- Detect a runaway identity by consumption of any shared quota rising above 25 percent of the pool while its verified completion rate falls below 50 percent of its trailing 7-day median, evaluated over a 300-second window.
- Respond in bounded order: reduce the identity's quota allocation to its declared floor, refuse new run admissions for it, allow in-flight grants to reach their deadline, and emit a containment event naming the identity, the pool, and the observed figures.
- Escalate to disablement where consumption remains above the pool share for 900 seconds after allocation reduction, preferring reversible disablement and quarantine over deletion so that forensic evidence is preserved.
- Maintain kill switches scoped independently by agent, capability, version, tenant, destination, model, region, and side-effect class, operating outside the model tier and outside the ordinary deployment pipeline.
- Require a kill-switch activation to atomically stop new dispatch, cease credential issuance, revoke outstanding credentials, remove the asset from discovery, cancel work that is safe to cancel, quarantine uncertain outputs, and open reconciliation.
- Reconcile continuously and after every registry, policy, identity, gateway, quota, or kill-switch change: read the signed desired-state version, enumerate actual versions at every enforcement point, compare hashes, lifecycle states, endpoint health, credential status, and enforcement mode, and apply idempotent corrections in bounded batches beginning with deny and disable operations.
- Retry a reconciliation target at most 5 times in one cycle, then mark it degraded, remove it from routing where safe, and alert its owner.
- Never declare convergence from configuration delivery alone; confirm enforcement behaviour with a signed probe before recording a target as converged.

**Required Outputs**:

- A runaway detection record naming the identity, the pool, the consumption share, and the completion-rate figure.
- A containment ledger recording each bounded response step and its timestamp.
- A reconciliation report per cycle listing desired version, actual versions, drift fields, drift age, corrective actions, and convergence confirmation.

**Quality Checkpoints**:

- 0 identities exceed 25 percent of a shared pool for longer than 300 seconds without a recorded containment action.
- Kill-switch activation reaches first confirmed enforcement within 60 seconds and full fleet confirmation within 300 seconds.
- Registry drift rate, measured as active targets whose actual descriptor, policy, route, or lifecycle hash differs from desired state beyond the grace period, stays at or below 1 percent.
- 0 targets are recorded as converged on configuration delivery alone; every convergence carries a signed probe result.

***

## III. Implementation Guidance for AI Agents

AI agents operating within or configuring a control plane must follow systematic protocols ensuring that every consequential action is mediated, bounded, attributable, and revocable. The following guidance translates the framework above into agent-executable instruction.

### A. Structured Execution Protocol

**Control Plane Components**:

1. **Registry Agent**: Owns identity records, capability descriptors, lifecycle states, and delegation records. It alone may transition a lifecycle state, and every transition is versioned and attributed. It never evaluates a runtime request.
2. **Policy Decision Agent**: Evaluates the pinned policy bundle over the canonical input and emits a structured decision. It returns deny where any required attribute is missing, ill-typed, stale beyond bound, or unreachable. It never receives model output as an input field.
3. **Budget Agent**: Owns the run ledger and the fleet quota table, performs atomic reservation and release, and refuses a dispatch whose reservation cannot be satisfied at every affected scope. It alone may record exhaustion.
4. **Admission and Routing Agent**: Computes the eligible set by deterministic filter, applies admission checks at both named points, sheds load under saturation, and resolves an alias to an exact immutable version.
5. **Execution Broker**: Validates the grant at the enforcement point, injects trusted identity fields after stripping model-supplied values, resolves secrets, dispatches with an idempotency key, and verifies the postcondition against authoritative state. It owns every side effect.
6. **Evidence Agent**: Emits the append-only event stream, enforces the disclosure boundary before emission, applies retention classes, and computes the metric set. It may withhold an evidence release where a boundary breach is detected.
7. **Fleet Health Agent**: Monitors concentration, amplification, and per-identity consumption across the fleet, activates kill switches, and drives reconciliation. It operates outside the run and outside the model tier.

**Authority Statement**: The seven components above constitute the deterministic tier. None of them accepts a model-tier decision as authoritative on identity, policy, budget, eligibility, redaction, or containment. This is a design requirement of the method rather than a gap awaiting a more capable model: the property that makes a control plane an enforcement boundary is that the component executing the work cannot decide what the work is permitted to do. A model tier that could set its own budget or widen its own scope would collapse the two planes and return the system to the condition Section 1.2 prohibits.

**Reasoning Disclosure Boundary**: Every component logs decision metadata and no component logs hidden reasoning content. Reason codes, decision identifiers, evidence references, cost figures, validator outcomes, and source classes are recorded; private chain-of-thought, raw sensitive payloads, secret values, and full capability definitions are not. Where a component cannot justify a decision without exposing hidden reasoning, it records the decision as unjustified and escalates.

**Workflow Execution Pattern**:

```
STATE: Pre_Dispatch_Authorization
INPUTS:
  1. Resolved capability identifier and immutable version
  2. Canonical arguments with model-supplied identity fields stripped
  3. Current authority scope for the acting identity
  4. Budget ledger state at run and fleet scope
ACTIONS:
  1. Recompute canonical policy input and its hash
  2. Evaluate pinned bundle; emit structured decision
  3. Reserve budget atomically at every affected scope
  4. Issue execution grant bound to version, argument hash, destination, deadline
  5. Persist durable call record before any side effect
VALIDATION:
  - policy_engine_reachable == TRUE
  - bundle_age_seconds <= 300
  - decision_effect IN {ALLOW, ALLOW_WITH_CONSTRAINTS}
  - authority_scope_contains_capability == TRUE
  - delegation_scope_subset_of_parent == TRUE
  - reservation_satisfied_all_scopes == TRUE
  - model_supplied_identity_fields_present == FALSE
  - grant_expiry_seconds <= 300
TRANSITIONS:
  IF all_validations_pass THEN next_state = Dispatch_Through_Enforcement_Point
  IF decision_effect == REQUIRE_APPROVAL THEN next_state = Await_Bound_Authorization
  IF decision_effect == DENY THEN next_state = Terminal_Denied
  IF policy_engine_reachable == FALSE THEN next_state = Terminal_Denied
  IF reservation_satisfied_all_scopes == FALSE THEN next_state = Terminal_Partial_Result
  IF validation_failed THEN next_state = Control_Plane_Error_Handling
```

**Two-Phase Action Pattern**: Emit the intended dispatch with its resolved version, canonical arguments, destination, and estimated consumption without executing it; confirm it against the validation block while no resource is committed and no effect has occurred; commit only after validation passes, recording the decision, the reservation, and the grant in the same operation.

**Approval Gate**: Human authorization is required before any dispatch in the externally visible write, financial or security change, destructive, privileged administration, or arbitrary execution side-effect classes; before any authority-scope widening at the management plane; before any budget increase above 25 percent of the identity's declared profile; and before any fleet-wide kill-switch release. Agents halt at these gates rather than proceeding with a recorded warning.

**Context Management Requirements**:

- Hold identity records, authority scopes, budget ledgers, and grants in durable state outside working context, since a run may outlive a single context window and a control-plane decision must survive a restart.
- Expose to model context only the eligible capability set, the reason code, and the bounded normalized result; never the policy body, the full catalog above 30 entries, credential material, or another tenant's identifiers.
- Write a handoff record at every context boundary naming the run identifier, remaining budget on all 4 dimensions, outstanding grants, delegation depth, and terminal-state expectation.
- Meter the control plane's own context and token consumption against its distinct pool rather than treating decision-path cost as free.

### B. Quality Assurance Checkpoints

**Checkpoint 1: Identity and Authority Integrity (After Phase 1)**

- **Automated Check**: Every deployed agent resolves to exactly 1 registered identity; every authority envelope is an enumeration; every exposed capability version carries an owner, provenance, and side-effect class; every delegation scope is a proven subset of its parent.
- **Agent Action on Pass**: Proceed to policy declaration.
- **Agent Action on Failure**: Halt registration and return the specific identity or descriptor defect; no run is admitted under an incomplete identity.
- **Human Review Trigger**: Any request for a new side-effect class, a new data class, an external destination, arbitrary execution, or unsigned provenance.

**Checkpoint 2: Gate Placement and Default-Deny Posture (After Phase 2)**

- **Automated Check**: All 4 named evaluation points produce decisions; the bypass probe reports 0 successful bypasses in 24 hours; a simulated policy-engine outage denies 100 percent of consequential actions; every distributed artifact carries a staleness bound.
- **Agent Action on Pass**: Proceed to budget declaration.
- **Agent Action on Failure**: Halt; an unmediated path or a fail-open behaviour is corrected before any traffic is admitted.
- **Human Review Trigger**: Any proposed restricted mode, or any enforcement point that cannot enforce independent downstream authorization.

**Checkpoint 3: Budget Enforcement (After Phase 3)**

- **Automated Check**: 100 percent of admitted runs carry limits on all 4 dimensions; 0 dispatches proceed without a satisfied reservation; quota breach rate is 0 for write and financial classes; every terminated run carries exactly 1 terminal state.
- **Agent Action on Pass**: Proceed to routing and admission.
- **Agent Action on Failure**: Refuse admission for the affected agent class until the ledger is complete.
- **Human Review Trigger**: Any budget increase above 25 percent of an identity's declared profile, or any request to raise a fleet pool ceiling.

**Checkpoint 4: Routing and Admission Validity (After Phase 4)**

- **Automated Check**: 100 percent of selections lie within the pre-computed eligible set; 0 selections rest on similarity alone; no selection exceeds 2 rounds; 0 expired grants are accepted; unknown side-effect rate is at or below 0.5 percent.
- **Agent Action on Pass**: Proceed to evidence emission.
- **Agent Action on Failure**: Return capability-unavailable and record the filter-rejection reasons; a selection outside the eligible set is never reconciled into an allow.
- **Human Review Trigger**: Capability-unavailable returned for more than 10 percent of admitted runs in one capability family over 24 hours.

**Checkpoint 5: Evidence Completeness and Disclosure (After Phase 5)**

- **Automated Check**: Audit completeness rate at or above 99.5 percent; all 5 correlation identifiers present or explicitly null; 0 boundary violations reaching the evidence store; every event type carries a retention class; restoration verified within 90 days.
- **Agent Action on Pass**: Release the metric report and permit promotion of the configuration.
- **Agent Action on Failure**: Withhold evidence release, purge the violating records, and re-instrument before reopening the store.
- **Human Review Trigger**: Any disclosure breach, any audit gap above 0.5 percent, or any non-repudiation claim without a tested restoration.

**Checkpoint 6: Fleet Containment Readiness (After Phase 6)**

- **Automated Check**: 0 shared dependencies above the 40 percent concentration ceiling without a tested fallback; exactly 1 retry owner per capability family; fleet retry amplification at or below 1.5; kill switches confirmed at every declared scope; registry drift rate at or below 1 percent.
- **Agent Action on Pass**: Permit fleet expansion or an authority increase.
- **Agent Action on Failure**: Freeze fleet size and authority at current levels until containment is demonstrated.
- **Human Review Trigger**: Any kill switch failing to reach full confirmation within 300 seconds, or any correlated failure whose containment action did not fire.

**Checkpoint Documentation Template**:

```
CHECKPOINT_ID:
CHECKPOINT_NAME:
PHASE_BOUNDARY:
VALIDATION_CRITERIA:
MEASURED_VALUE:
PASS_CONDITION:
PASS_ACTION:
FAIL_ACTION:
HUMAN_REVIEW_TRIGGER:
RESPONSIBLE_COMPONENT:
```

### C. Error Handling and Troubleshooting

**Error Type 1: Authority Amplification Attempt**

- **Symptoms**: A request carries a model-supplied tenant, role, scope, approval, idempotency, or budget field; a delegation requests an element absent from its parent scope; an argument repair changes recipient, destination, amount, or data scope; a denied action reappears through a different channel with the same effect.
- **Diagnostic Steps**: Compare the requested scope against the acting identity's registered envelope and the parent delegation record; recompute the canonical argument hash before and after the repair; classify the effect of the substituted channel rather than its capability name.
- **Resolution Protocol**: Option A, strip the model-supplied fields and re-evaluate from the canonical input. Option B, reject the delegation and return the subset violation with the specific excess element named. Option C, treat the repaired proposal as a new intent requiring a fresh decision rather than as a correction to the prior one. Option D, deny and record a security signal where the same effect is attempted through 2 or more channels.
- **Escalation Trigger**: The second amplification attempt within one run skips the appeal path and enters incident response; this class is never resolved by permitting a narrower version of the requested widening.

**Error Type 2: Policy Decision Unavailable or Stale**

- **Symptoms**: The decision service is unreachable, returns a malformed decision, fails bundle signature verification, or serves a bundle older than its declared staleness bound; decisions arrive without a bundle version.
- **Diagnostic Steps**: Distinguish an engine outage from a distribution failure by comparing the enforcement point's loaded bundle hash against the signed desired-state version; check propagation lag against the 300-second bound; confirm whether the failure is regional or global.
- **Resolution Protocol**: Option A, deny every consequential action and continue serving only read-only, non-sensitive operations against a local allowlist for at most 900 seconds. Option B, fail over to a second decision replica in another failure domain and re-evaluate. Option C, activate the capability-scoped kill switch where the stale bundle would otherwise grant authority that has since been revoked.
- **Escalation Trigger**: Restricted mode persisting beyond 900 seconds, or any consequential action permitted during an outage, escalates immediately; failing open is never an available resolution.

**Error Type 3: Unknown Side Effect After Dispatch**

- **Symptoms**: An execution attempt ends without an authoritative outcome; a timeout occurs after the request reached the executor; an acknowledgement is lost after a committed write; the durable record shows a dispatch with no terminal state.
- **Diagnostic Steps**: Query the system of record by idempotency key or external operation identifier before any further attempt; classify the outcome as pre-dispatch failure, definite rejection, retryable failure, permanent failure, or unknown side effect.
- **Resolution Protocol**: Option A, retry only where the system of record proves no effect occurred, reusing the same idempotency key. Option B, where an effect is proved and a later mandatory step failed, execute the registered compensations in declared reverse order with independent verification. Option C, where reconciliation cannot resolve the state, report the run as unknown, quarantine dependent outputs, and escalate with the durable record attached.
- **Escalation Trigger**: Unknown side-effect rate above 0.5 percent for a capability family suspends its write authority; an unknown outcome is never resolved by an unreconciled retry.

**Error Type 4: Fleet-Scale Amplification**

- **Symptoms**: Retry amplification above 2.0 sustained for 120 seconds; attempt volume against one dependency above 3 times its trailing 7-day peak; a step change above 20 percentage points in one failure class; circuit-open rate above 5 percent of eligible requests.
- **Diagnostic Steps**: Attribute the attempt volume to retry owners and confirm whether more than 1 layer is retrying; identify the shared dependency, configuration version, credential issuer, or model endpoint common to the failing set; compare the failing population against the shared-dependency inventory.
- **Resolution Protocol**: Option A, reduce the fleet retry cap to 0 for the affected dependency class and hold until amplification falls below 1.5 for 300 seconds. Option B, shed new admissions for the class and shift to the declared fallback. Option C, restrict the affected identities to read-only where no fallback exists. Option D, remove the duplicate retry layer and re-run the regression suite before restoring the cap.
- **Escalation Trigger**: Amplification not falling below 1.5 within 900 seconds of damping escalates to the dependency owner and freezes fleet expansion; a storm is never resolved by raising capacity alone.

**Error Type 5: Runaway Consumption of a Shared Quota**

- **Symptoms**: One identity consumes above 25 percent of a shared pool while its verified completion rate falls below 50 percent of its trailing 7-day median; other tenants report admission refusals with a quota reason code while the pool shows headroom for none.
- **Diagnostic Steps**: Segment pool consumption by identity, capability family, and destination class over a 300-second window; compare the suspect identity's consumption-per-completion against its own history rather than against the fleet average.
- **Resolution Protocol**: Option A, reduce the identity's allocation to its declared floor and refuse new admissions for it while in-flight grants reach their deadlines. Option B, disable the identity reversibly and quarantine its outputs where consumption stays above the pool share for 900 seconds. Option C, where the cause is a defective capability rather than the identity, quarantine the capability version and leave the identity active on the remainder of its scope.
- **Escalation Trigger**: A second containment against the same identity within 7 days escalates to the identity's owner and blocks its lifecycle promotion; deletion is never used where reversible disablement and forensic preservation are available.

**Error Type 6: Evidence Gap or Disclosure Breach**

- **Symptoms**: Audit completeness below 99.5 percent; a logical call missing an applicable mandatory event; hidden reasoning content, a secret value, or a bearer token found in the evidence store; a broken hash chain; an administrative access with no corresponding event.
- **Diagnostic Steps**: Resolve the affected calls through the correlation index to locate which of the 8 mandatory events is missing; verify the hash chain across the affected window; identify the emitting component that bypassed the pre-emission scan.
- **Resolution Protocol**: Option A, re-instrument the emitting component and backfill from durable state where the record survives outside telemetry. Option B, purge the violating records, rotate any exposed credential, and reopen the store only after a clean scan. Option C, mark the affected window as evidentially incomplete rather than asserting coverage the records do not support.
- **Escalation Trigger**: Any disclosure breach halts evidence release immediately and blocks every non-repudiation claim for the affected window; this class is never resolved by retry or by post-hoc redaction.

**Troubleshooting Decision Tree**:

```
CONTROL PLANE DETECTS A PROBLEM
├─ AUTHORITY DEFECT
│   ├─ Model-supplied identity or budget field → Strip; re-evaluate from canonical input
│   ├─ Delegation scope exceeds parent → Reject; name the excess element
│   ├─ Repair changes intent or destination → Treat as new intent; fresh decision
│   └─ Same effect via second channel → DENY; record security signal; incident response
├─ DECISION DEFECT
│   ├─ Policy engine unreachable → DENY all consequential actions; never fail open
│   ├─ Bundle staler than 300 seconds → Restrict to read-only; fail over to second replica
│   ├─ Decision without bundle version → Reject decision; re-evaluate on pinned engine
│   └─ Revoked authority still granted → Activate capability kill switch; reconcile
├─ BUDGET DEFECT
│   ├─ Reservation unsatisfied at any scope → Refuse dispatch; emit partial result
│   ├─ Exhaustion reached → Stop new grants; emit declared partial result; terminate
│   └─ Estimate error above 50 percent for 3 days → Re-estimate; never raise the budget
├─ EXECUTION DEFECT
│   ├─ Unknown outcome after dispatch → Reconcile by idempotency key before any retry
│   ├─ Effect committed, later step failed → Run registered compensations; verify each
│   └─ No reviewed compensation exists → Preserve evidence; escalate to named owner
├─ FLEET DEFECT
│   ├─ Amplification above 2.0 for 120 seconds → Cap retries at 0 for the class; shed
│   ├─ Step change above 20 points in one class → Shed to fallback; else read-only
│   ├─ Identity above 25 percent of pool → Reduce to floor; refuse new admissions
│   └─ Containment repeated within 7 days → Reversible disable; block promotion
└─ EVIDENCE DEFECT
    ├─ Mandatory event missing → Backfill from durable state; mark window incomplete
    ├─ Hidden reasoning or secret in store → HALT release; purge; rotate; re-instrument
    └─ Broken hash chain → Withdraw non-repudiation claim for the affected window
```

### D. Performance Metrics and Continuous Learning

**Availability and Decision Metrics**:

- **Control-plane availability**: Valid runtime decision requests receiving a non-error decision within the deadline, over valid runtime decision requests, reported separately for management writes, runtime decisions, enforcement, and evidence ingestion (target: at least 99.9 percent for the runtime decision path).
- **Policy decision latency**: The duration below which a stated share of evaluations complete, measured from canonical input availability to decision emission, reported at the 50th and 95th percentile with cache hits and misses separated (target: 95th percentile at or below 50 milliseconds; averages are never reported in place of percentiles).
- **False-allow rate**: Labelled prohibited requests incorrectly allowed or routed to an approval path, over labelled prohibited requests (target: 0 for every critical prohibited outcome; a non-zero value blocks release).
- **False-deny rate**: Labelled authorized requests incorrectly denied, over labelled authorized requests (target: at or below 2 percent; a higher rate triggers policy review rather than a blanket widening).
- **Configuration stale-read rate**: Runtime decisions using configuration older than its declared maximum staleness, over runtime decisions (target: at or below 0.1 percent).

**Enforcement and Containment Metrics**:

- **Registry drift rate**: Active targets whose actual descriptor, policy, route, or lifecycle hash differs from desired state beyond the grace period, over active targets (target: at or below 1 percent).
- **Reconciliation convergence time**: Confirmed-convergence timestamp minus desired-state publication timestamp, reported separately for emergency and ordinary changes (target: at or below 60 seconds for emergency, 900 seconds for ordinary).
- **Kill-switch activation time**: First confirmed enforcement minus authorized activation (target: at or below 60 seconds), with full propagation measured to the last required target confirmation (target: at or below 300 seconds).
- **Retry amplification**: Execution attempts over logical calls executed (target: at or below 1.5; above 2.0 opens containment).
- **Quota breach rate**: Operations whose actual usage exceeds an enforced quota without an authorized reservation, over operations subject to quota (target: 0 for write and financial classes).
- **Delegation constraint-loss rate**: Delegations in which inherited scope, purpose, data, or approval constraints are weakened or omitted, over delegations evaluated (target: 0).

**Evidence and Outcome Metrics**:

- **Audit completeness rate**: Sampled logical calls carrying every applicable mandatory event, over sampled logical calls (target: at least 99.5 percent).
- **Unauthorized disclosure rate**: Evaluated tasks disclosing protected data to an unapproved destination, over evaluated tasks containing protected data (target: 0).
- **Verified task completion rate**: Admitted tasks whose terminal state satisfies all required goals and policy, over admitted tasks (target: reported per capability family, with no single target imposed across families).
- **Cost per verified successful task**: Model, capability, workflow, gateway, policy, observability, and allocated control-plane cost, over verified successful tasks (target: reported rather than bounded, and never reported as token cost alone).

**Evaluation Discipline**: No public benchmark establishes that a control plane is production-safe. Public suites are diagnostic only and are used for the behaviour each actually measures: function-calling suites measure call construction, parallel and serial invocation, abstention, and large-catalog behaviour without establishing authorization or infrastructure safety [27]; interaction benchmarks evaluate domain-policy adherence, final state, and repeated-trial reliability [28]; stateful sandboxes add implicit dependencies and intermediate milestones [29]; and authorization-preservation benchmarks test unauthorized action, over-disclosure, and constraint loss across benign delegation while explicitly excluding injection, collusion, and compromised agents [30]. The release gate is a private policy-accurate environment covering exact allow, deny, require-approval, and constrained-allow cases for every rule, plus cross-tenant access, registration takeover, schema widening, poisoned metadata, approval replay and expiry, delegation scope amplification, duplicate delivery, partition, clock skew, injection through every untrusted surface, evidence tampering, and kill switches at every supported scope.

**Learning and Adaptation Mechanisms**:

- **Regression accumulation**: Every validated failure from fault injection, red-team exercise, or production incident enters a permanent regression set that gates every later release.
- **Threshold recalibration**: Recompute every numeric threshold per deployment against observed distributions; the values stated here are deployment defaults, not measured constants.
- **Differential replay**: Replay recorded canonical inputs under a candidate bundle before enforcement, classify each change, and require a named owner for every broadened allow.
- **Bounded iteration**: Cap ordinary automated tuning at 5 rounds before revisiting architecture, labels, or requirements; a model-generated policy change receives the same review as a human-authored one.

**Human-in-the-Loop Boundaries**: Widening an authority scope, raising a fleet quota ceiling, relaxing the disclosure boundary, releasing a fleet-wide kill switch, granting a policy exception, and promoting a configuration whose advantage appears only under clean conditions are never automated.

***

## IV. Domain-Agnostic Application Guidance

This framework generalises across sectors because it governs authority, resource allocation, and evidence rather than the content of any particular task. Its phases hold wherever more than 1 agent acts under a common policy, actions carry consequences outside the agent, and a later reviewer must reconstruct what happened.

### 4.1 Cross-Domain Application Patterns

**Regulated financial operations**: Almost every action is externally visible or irreversible in practice, so the approval gate binds before most dispatches and the default-deny posture is the operating condition rather than an exception. The authority envelope enumerates permitted destination classes and amount ceilings as first-class fields, and argument-level policy evaluates recipient, account, and amount rather than the capability name alone. The evidence stream is a regulatory deliverable rather than a diagnostic aid, so retention is set by obligation and the hash chain is load-bearing. Budget exhaustion terminates with a declared partial result naming every committed transfer, because a silent truncation in this domain is an unreconciled financial state.

**Clinical and health data handling**: Data classification dominates the policy input, and the same capability is permitted or denied on the relationship between the acting principal and the record rather than on any attribute of the capability itself. Egress is deny-by-default with an exact destination allowlist, and the model tier is prohibited from converting a denied disclosure into an equivalent effect through a message, a log line, or a peer-agent handoff. Cross-tenant negative tests run continuously because a single boundary failure is a reportable event rather than a defect. Retention is bounded downward by privacy obligation as well as upward by audit obligation.

**Industrial and field operations**: Reversibility varies within one run, since a provisional schedule is reversible while a dispatched crew or a committed machine state is not, so thresholds bind per side-effect class rather than per run. Connectivity is intermittent, which makes the staleness bound the central control: an enforcement point unable to prove freshness restricts to read-only rather than acting on a cached grant. Federation is the default topology, with signed desired state distributed to local decision points and emergency denies propagated on the accelerated channel. Compensation is often unavailable, so the guide's prohibition on inventing a compensation at failure time governs the escalation path.

**Software platform engineering**: The capability catalog is large and changes faster than the agents that use it, so progressive disclosure from the eligible set is routine rather than exceptional, and the description hash is monitored because a changed capability description is a changed instruction to the model tier. Arbitrary execution is present, which makes the sandbox broker a mandatory enforcement point and deny-by-default egress non-optional. Retry amplification is the dominant fleet failure mode here because retries are cheap and dependencies are shared, so the single-retry-owner rule carries most of the containment weight.

**Public-sector case handling**: Authority derives from a statutory role rather than from an organisational hierarchy, so relationship evaluation answers most authorization questions and the delegation record must preserve the originating principal unchanged at every depth. Decisions must be explainable to a subject rather than only auditable internally, so reason codes are drawn from a published vocabulary and the structured decision retains the matched rule identifiers in the evidence store even though they never reach model context. Fleet quotas are allocated by case class rather than by tenant, and runaway containment protects the queue for lower-volume case types.

**Research and analysis fleets**: Side effects are rare and reads dominate, which makes budget rather than policy the binding constraint, and the four-dimension ledger the principal control. Correlated failure is the salient fleet risk because many agents share one model endpoint and one index, so the concentration ceiling and the source-class independence test carry more weight than the approval gate. The declared partial result is the normal terminal state rather than an exception, since analysis runs are commonly budget-bound rather than completion-bound.

### 4.2 Scale, Risk, and Topology Adaptation

- **Single-tenant fleets below 10 agents**: Retain identity registration, the policy gate, and the budget ledger; collapse the fleet-scope quota table to a single global pool; run reconciliation on a 300-second cycle rather than continuously. Retain all 6 phases, since the failure modes in Phase 6 appear at fleet sizes well below 10 wherever a shared dependency exists.
- **Multi-tenant fleets above 100 agents**: Partition quotas per tenant with a declared starvation floor, shard the decision path across at least 3 failure domains, and treat the concentration ceiling as the governing constraint on architecture rather than as a monitoring threshold.
- **High-risk or irreversible authority**: Bind the approval gate before every dispatch in the top 4 side-effect classes, require at least 1 independent verification signal that passes the source-class test, and prefer abstention over unverified completion. Restricted mode is unavailable in this tier without exception.
- **Strict decision-latency budgets**: Move the decision point closer to the enforcement point with signed local bundles and shorter staleness bounds, rather than removing evaluation points. Removing a gate removes control; relocating it preserves control and raises distribution cost.
- **Federated and hierarchical deployments**: Set a global baseline of non-overridable constraints, permit domain and tenant layers to narrow authority and add requirements, and prohibit any child layer from weakening a parent deny. Compile the effective policy and retain its lineage so a decision can be attributed to the layer that produced it.
- **Agent-managed control planes**: Where an agent configures the plane it operates within, execute Phases 1, 2, and 6 under a distinct management identity whose authority does not intersect the runtime identity's scope. An agent that can register its own capabilities and evaluate its own policy under one identity has recreated the fused-plane condition this guide prohibits.

***

## V. Limitations and Considerations

**Most thresholds here are deployment defaults**: The numeric bounds in this guide, including the 40 percent concentration ceiling, the 25 percent runaway share, the 1.5 retry amplification target, the 300-second staleness bounds, the 30-entry catalog disclosure threshold, and the delegation depth caps of 3 and 5, were chosen to be operable on first deployment rather than derived from measurement. Only the retry bounds, the reconciliation attempt cap, the selection round cap, the repair cap, and the interactive turn and call ceilings are carried from the prose source. The mitigation is the recalibration requirement in Section III.D, which obliges each deployment to recompute every threshold against its own observed distributions before treating any of them as evidence.

**External claims were transcribed rather than re-derived**: The platform, protocol, and framework claims in this guide are taken from the originating prose source as it cited them. Four were confirmed against the cited page during conversion: the token-exchange RFC, the protocol specification's tool-safety language, the control-plane design-pattern paper, and the authorization-preservation benchmark. The remainder are reproduced as the source carried them. The mitigation is that no threshold in the Operational Framework depends on an unverified external figure; the transcribed claims support context rather than acceptance criteria.

**A control plane governs authority, not correctness**: Every decision in this framework can be correct and the resulting action can still be wrong, because the gate evaluates permission rather than judgement. A fleet can satisfy every checkpoint here while pursuing a badly specified objective. The mitigation is that verified task completion is reported per capability family rather than assumed, and that the human-in-the-loop boundaries in Section III.D reserve objective-level decisions for review.

**Enforcement adds latency to every consequential path**: Four evaluation points, atomic reservation, grant issuance, and pre-emission scanning sit between an intent and its effect, and the cost is paid on every call rather than amortised. The mitigation is the entry gate in Section 1.3, which defers the plane entirely below its threshold, together with the federation guidance that relocates decisions near enforcement points instead of removing them.

**Evidence rich enough to audit is rich enough to leak**: The minimum event schema records identity, destination, argument hashes, and cost across every call, and a store holding that for a whole fleet is a high-value target. The mitigation is the disclosure boundary in Step 5.2, the pre-emission scan that quarantines rather than redacts after the fact, the writer and auditor role separation in Step 5.3, and content references in place of full payloads.

**Fleet failure modes are detected by threshold, and thresholds lag**: Correlated failure, retry storms, and runaway consumption are all identified by a rate crossing a bound over a window, so a fast enough failure completes before its detector fires. The mitigation is that each response is bounded and reversible rather than corrective after the fact: the retry cap reduces to 0 rather than tuning downward, the runaway response reduces allocation before disabling, and kill switches are scoped narrowly so containment does not require a fleet-wide stop.

**Vendor implementations were compressed to capability requirements**: The source surveyed named policy engines, identity platforms, gateways, and workflow engines. This guide states what each component must supply rather than which product supplies it, because a domain-agnostic guide cannot presuppose one vendor and because product maturity moves faster than a guide revision. The mitigation is that Section VII retains the source's product citations, so a reader selecting an implementation can consult them directly and verify current maturity, policy depth, fail behaviour, and bypass resistance rather than relying on a category label.

**No public benchmark establishes production safety**: The evaluation suites named in Section III.D each measure a slice, and none of them establishes that a control plane enforces authorization under adversarial conditions. The mitigation is the private policy-accurate release gate, which is the only artifact this guide treats as a release authority, and the regression accumulation rule that converts every observed failure into a permanent gate.

***

## VI. Conclusion and Summary

A control plane is a governance discipline before it is a set of services. Its value comes from one structural commitment: the layer that decides what is permitted is not the layer that performs the work. Everything else in this guide follows from that separation. Identity is registered rather than assumed so that authority is a property of a record. Policy is evaluated deterministically at named points so that a decision can be replayed. Budgets are reserved rather than reported so that exhaustion terminates cleanly. Evidence is emitted at fixed points so that a reviewer can reconstruct what happened under whose authority at what cost. Containment is bounded so that a fleet degrades in a declared way.

The partition that makes this work is uncomfortable to state plainly and must be stated anyway. The control plane holds no model-tier decision authority at any point. The model tier proposes intents, drafts arguments, ranks within an eligible set the deterministic tier computed, and interprets results inside a scope it was granted. It never decides whether an action is permitted, never sets or amends a budget, never widens a scope, never decides what is safe to log, and never activates or releases a containment control. This is a design requirement, not an omission awaiting a more capable model, because a system in which the executing component can grant itself authority has no enforcement boundary regardless of how well that component reasons.

A team introducing a control plane should establish evidence before enforcement. Instrument the event schema and the correlation identifiers against existing traffic, measure the baseline on cost, latency, failure classes, and dependency concentration, then add identity registration and the policy gate in shadow mode where decisions are recorded but grant nothing. Enable enforcement on read-only paths first, add reversible writes behind the approval gate, and grant irreversible authority only after fault injection, cross-tenant negative tests, and kill-switch drills have run against the configuration that will carry it.

**Key Success Factors**:

- **Plane separation**: The component that decides what is permitted is never the component that executes the work, and an agent cannot grant itself budget or authority mid-run.
- **Registered authority**: Every agent instance holds one registered identity carrying an enumerated authority scope; delegation grants a subset and never a superset.
- **Deterministic gate with default deny**: Policy is evaluated by a pinned engine at named points over canonical input, and an unavailable or stale engine denies rather than fails open.
- **Enforced budgets**: Tokens, tool calls, wall clock, and money are reserved atomically before dispatch at run and fleet scope, and exhaustion produces a declared partial result rather than silence.
- **Evidence within a disclosure boundary**: Decision metadata is recorded at 8 mandatory points with 5 correlation identifiers; hidden reasoning content, secrets, and raw sensitive payloads are not.
- **Bounded fleet containment**: Correlated failure, retry amplification, and runaway consumption each carry a detection signal, a numeric threshold, and a bounded reversible response.

By following this guide, AI agents can operate within a fleet whose authority is enumerated rather than assumed, whose resource limits bind rather than advise, and whose actions remain reconstructible long after the run that produced them has ended.

***

## VII. References and Further Reading

This guide is an operational restructuring of a single prose source. The corpus pointers below identify that source and the sibling guides bearing on particular phases. The external references that follow are transcribed from the originating prose guide as it cited them and were not independently re-verified during conversion, except for the 4 entries marked as verified, whose titles and stated content were confirmed against the cited page during this conversion.

**Corpus pointers**:

- `Production Control Planes for AI Agents` — the originating prose guide from which this operational guide was derived. Source of the plane separation, the seven invocation contracts, the registration and validation loop, the discovery and admission procedures, the policy input and decision shape, the approval and appeal loops, the identity and credential model, the retry, saga, and reconciliation loops, the security assumptions and mandatory controls, the field inventory and metric formulas, the evaluation strategy, and the compact decision procedure. It carries inline citations to platform documentation, protocol specifications, standards, and benchmark papers; the external references listed below are transcribed from those citations.
- `advanced_task_guides/authoring/guide_guidewriting.md` — the normative house-style specification. Source of the archetype, the step slot template, the mandatory Implementation Guidance subsection names, and the conformance envelope this guide was written against.
- `advanced_task_guides/tool-use/guide_ToolUseAndFunctionCalling.md` — the companion guide owning the per-call invocation contract: the tool declaration, the pre-call and post-call validation gates, idempotency and per-class retry policy, and the isolation rule under which a result is data rather than instruction. This guide specifies where that contract is gated, budgeted, logged, and revoked; it does not restate the contract itself.
- `advanced_task_guides/tool-use/guide_ToolRetrieval.md` — the sibling owning retrieval over a capability catalogue too large to expose in full: a canonical registry, a derived and versioned index, an authorization-filtered eligible set computed before any relevance score exists, a bounded exposed set, and recall measured against a labelled request-to-tool set. It bears directly on the selection step in Step 4.1: this plane computes eligibility and holds the authority, and that guide ranks within the set eligibility already returned.
- `advanced_task_guides/tool-use/guide_ModelContextProtocol.md` — the sibling owning third-party server integration: server admission and provenance verification, protocol revision negotiation, pinning of reviewed definitions with a hash-based drift rule, per-server authority scoping, and isolation of server-supplied content as untrusted data. It is the protocol-mediated capability surface referenced in Step 2.2.
- `advanced_task_guides/tool-use/guide_CodeExecution.md` — the sibling owning bounded execution of untrusted generated code: an execution warrant gate, an isolation boundary stated as six explicit denials, default-deny egress under an allowlist, runtime-enforced resource bounds, and a failure taxonomy separating program errors, timeouts, resource kills, policy denials, and infrastructure faults. It specifies the sandbox enforcement point named in Step 2.2.
- `advanced_task_guides/tool-use/guide_AgentSkills.md` — the sibling owning packaged units of instructions plus supporting resources, admitted from approved sources under pinning and review, selected by trigger evaluation, and loaded under a description budget. It applies to procedural packages the registration, lifecycle, and bounded-authority discipline this guide applies to capability versions.
- `advanced_task_guides/tool-use/guide_ComputerUse.md` — the sibling owning the graphical-interface capability class, and the only guide in this category that defines a reversibility class vocabulary. The reversibility class carried on the capability descriptor in Step 1.2 takes its values from that closed R0 to R3 set; this guide names the field and does not define the classes.
- `advanced_task_guides/tool-use/guide_MCPToolGateway.md` — the sibling owning a shared intermediary through which many agents reach many upstream servers under central credential custody and per-principal authorization. Such a gateway is one inline enforcement point of the kind located in Step 2.2, and consumes signed desired state from this plane rather than becoming a second source of organisation-wide truth.
- `advanced_task_guides/tool-use/guide_CodeAsAction.md` — the sibling owning the program action representation, in which one emitted program calls many capabilities through a frozen binding namespace. That namespace is one narrow, task-scoped projection of the authority scope defined here, and the guide adopts the non-amplification invariant, the default-deny posture, the budget ledger, and the execution grant without redefining them.
- `advanced_task_guides/planning/guide_TaskManagementOrchestration.md` — companion guidance on the task lifecycle, state machine, and terminal-state vocabulary, applicable to the run admission and termination steps in Phases 3 and 4.
- `advanced_task_guides/planning/guide_MetaReasoning.md` — companion guidance on bounded control decisions and the disclosure boundary, applicable to the logging rules in Step 5.2.
- `advanced_task_guides/context-management/guide_ContextIsolation.md` — companion guidance on delegation contracts, inherited authority, and the declared partial result, whose terminology this guide adopts for Step 1.3 and Step 3.3.
- `advanced_task_guides/context-management/guide_ContextStateMachines.md` — companion guidance on deterministic control of the exposed tool surface, applicable to the dynamic exposure rules in Step 4.1.
- `advanced_task_guides/memory-management/guide_DistributedMemoryArchitecture.md` — companion guidance on staleness bounds, partition behaviour, and the execution-tier partition, whose terminology this guide adopts for Section 1.4 and Step 2.3.
- `advanced_task_guides/design-architecture/guide_TelemetryDesign.md` — companion guidance on telemetry pipeline architecture, semantic conventions, retention, and governance controls, applicable to the event schema in Step 5.1.
- `advanced_task_guides/design-architecture/guide_MonitoringDesignConstraintAnalysis.md` — companion guidance on monitoring design under constraint, applicable to the fleet detection rules in Phase 6.
- `advanced_task_guides/policy-risk/guide_SystemSpecificRiskAssessment.md` — companion guidance on system boundary definition and risk evaluation, applicable to the risk classification inputs used throughout Phase 2.

**External references**: The numbering below is the numbering used by the inline markers in Sections I, II, and III. Entries carrying no inline marker support material of the prose source that this operational restructuring did not retain as a separately attributable claim.

*Control-plane and data-plane separation*

1. Kubernetes, *Kubernetes components* — https://kubernetes.io/docs/concepts/overview/components/
2. Istio, *Istio architecture* — https://istio.io/latest/docs/ops/deployment/architecture/
3. Kandasamy, *Control Plane as a Tool: A Scalable Design Pattern for Agentic AI Systems* — https://arxiv.org/abs/2505.06817 (title and authorship verified during conversion)

*Policy engines and deterministic authorization*

4. Open Policy Agent, *OPA documentation* — https://www.openpolicyagent.org/docs/latest/
5. Open Policy Agent, *Decision logs* — https://www.openpolicyagent.org/docs/management-decision-logs
6. Cedar, *Cedar documentation* — https://docs.cedarpolicy.com/
7. Casbin, *Supported models* — https://casbin.org/docs/supported-models

*Identity, delegation, and credentials*

8. Jones, Nadalin, Campbell, Bradley, and Mortimore, *RFC 8693: OAuth 2.0 Token Exchange* — https://www.rfc-editor.org/rfc/rfc8693.html (title and delegation semantics verified during conversion)
9. SPIFFE, *SPIFFE overview* — https://spiffe.io/docs/latest/spiffe-about/overview/
10. Microsoft, *Entra agent governance* — https://learn.microsoft.com/en-us/entra/id-governance/agent-id-governance-overview
11. Microsoft, *Foundry agent identity* — https://learn.microsoft.com/en-us/azure/foundry/agents/concepts/agent-identity
12. Google Cloud, *Vertex AI Agent Builder* — https://cloud.google.com/blog/products/ai-machine-learning/more-ways-to-build-and-scale-ai-agents-with-vertex-ai-agent-builder
13. Amazon Web Services, *AgentCore least privilege* — https://docs.aws.amazon.com/wellarchitected/latest/agentic-ai-lens/agentrel02-bp02.html

*Enforcement points, gateways, and interoperation protocols*

14. Envoy, *Envoy MCP Gateway* — https://aigateway.envoyproxy.io/docs/0.5/capabilities/mcp/
15. Kong, *AI MCP Servers* — https://developer.konghq.com/ai-gateway/entities/ai-mcp-server/
16. Cloudflare, *Gateway changelog* — https://developers.cloudflare.com/changelog/product/gateway/
17. Model Context Protocol, *Specification 2026-07-28* — https://modelcontextprotocol.io/specification/2026-07-28 (tool-safety and consent language verified during conversion)
18. Model Context Protocol, *Official MCP Registry* — https://registry.modelcontextprotocol.io/docs
19. A2A, *A2A specification* — https://a2a-protocol.org/latest/specification/

*Durability, overload, and failure containment*

20. Temporal, *Activity definition* — https://docs.temporal.io/activity-definition
21. Google, *Handling overload* — https://sre.google/sre-book/handling-overload/
22. Envoy, *Circuit breaking* — https://www.envoyproxy.io/docs/envoy/latest/intro/arch_overview/upstream/circuit_breaking

*Observability, evidence, and governance obligations*

23. OpenTelemetry, *GenAI attributes* — https://opentelemetry.io/docs/specs/semconv/registry/attributes/gen-ai/
24. National Institute of Standards and Technology, *AI Risk Management Framework* — https://www.nist.gov/itl/ai-risk-management-framework
25. European Union, *EU AI Act* — https://eur-lex.europa.eu/eli/reg/2024/1689/oj
26. AICPA, *Trust Services Criteria* — https://www.aicpa-cima.com/resources/download/2017-trust-services-criteria-with-revised-points-of-focus-2022

*Evaluation suites and their stated boundaries*

27. Patil and colleagues, *BFCL* — https://proceedings.mlr.press/v267/patil25a.html
28. *tau-bench* — https://arxiv.org/abs/2406.12045
29. *ToolSandbox* — https://arxiv.org/abs/2408.04682
30. *MasDrift: Benchmarking Authorization Preservation Across Multi-Agent Architectures* — https://arxiv.org/html/2608.07556v1 (title and benchmark scope verified during conversion)
