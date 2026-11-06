# MCP Tool Gateway

**Status**: Beta

**Change logs**:

- [09/08/2026] - Initialization

***

## Executive Summary

An MCP tool gateway constitutes the task family of operating a shared intermediary through which many agents reach many Model Context Protocol servers, instead of each agent connecting to each server directly. This guide provides AI agents with a structured protocol for deciding whether the intermediary is warranted at all, registering upstream servers under central credential custody, propagating the calling principal so that authorization happens per principal rather than under ambient gateway authority, isolating tenants that share the hop, keying caches so that no result crosses an authority boundary, dispatching under pinned definitions with drift enforcement, and degrading predictably when an upstream fails. It specifies a decision gate that rejects the gateway where a direct client would enforce the same controls at lower risk, a six-phase operating framework, an execution-tier partition in which the model tier owns nothing at the gateway, and a metric set covering added-hop latency, credential attenuation, cross-tenant escape, stale-cache service, and audit completeness. It emphasizes structured execution protocols, quality assurance checkpoints, and error handling procedures so that centralisation buys governance rather than a single correlated failure.

***

## I. Foundational Concepts and Definitions

### 1.1 Core Terminology

**Gateway**: A shared intermediary that presents one governed MCP endpoint to many downstream callers and connects to many upstream servers on their behalf. It is simultaneously a server to its callers and a client to its upstreams, and it holds both roles at once for every request it carries.

**Downstream face**: The gateway's server-side surface, which authenticates callers, exposes a policy-filtered catalogue, accepts calls, and returns normalised results.

**Upstream face**: The gateway's client-side surface, which holds credentials for approved servers, dispatches one call to exactly one origin, and supervises the response.

**Calling principal**: The authenticated identity on whose behalf a gateway request is made, carrying user identifier, tenant identifier, agent identity, purpose code, and granted scope set, all bound from trusted infrastructure state rather than from model output. The term is adopted from the companion tool-use guide named in Section VII.

**Identity propagation**: The transmission of the calling principal from the caller to the gateway, preserved across the hop so that the gateway's authorization decision is a function of who is calling rather than of which gateway is running.

**Ambient authority**: Permission held by the gateway itself and exercisable on any request that reaches it, independent of who sent that request. A gateway that authorizes with ambient authority is a confused deputy at fleet scale.

**Confused deputy**: The condition in which an intermediary executes under its own privileges on behalf of a requester who could not have authorized the operation directly. Credential custody creates this condition; per-principal authorization is what removes it.

**Credential custody**: The gateway's holding of upstream credentials so that agents never hold them. Custody is the gateway's principal security benefit and its principal concentration of risk, and the two are inseparable.

**Credential attenuation**: The requirement that an upstream credential minted by the gateway carry no more authority than the intersection of the user grant, the agent grant, the declared task purpose, the gateway policy decision, and the tool's own requirement. Any credential exceeding that intersection is an attenuation violation.

**Token passthrough**: Forwarding a credential presented to the gateway onward to an upstream. The protocol prohibits it: under the revision named in Section 1.3, servers must only accept tokens valid for their own resources and must not accept or transit any other tokens.

**Tenancy isolation**: The property that one caller sharing the gateway cannot observe or reach another caller's servers, tool names, cached results, connections, processes, credentials, or evidence.

**Virtual server**: A named, versioned composition of approved tools drawn from several upstreams, bound to an owner, an audience, an alias map, and a policy bundle, and presented to one class of caller as if it were a single server.

**Caller-specific view**: The set of tool definitions one principal is permitted to see at one moment, computed as the intersection of virtual-server membership, entitlement, lifecycle state, health, risk ceiling, and emergency denials. Tool existence is itself disclosable information.

**Canonical tool identity**: The immutable tuple of gateway namespace, upstream server identifier, upstream tool name, and version to which every exposed alias resolves. Aliases are cosmetic; authority binds to canonical identity.

**Definition hash**: A digest over the complete normalized definition of one tool, comprising description, schemas, annotations, and metadata. The term and the pinning discipline behind it are adopted from the companion protocol guide named in Section VII.

**Side-effect class**: The declared category of consequence a successful invocation produces, drawn from the closed vocabulary of the companion tool-use guide: read-only public, read-only private, reversible write, externally visible write, financial or security change, destructive, and arbitrary execution.

**Authority scope**: The complete set of capabilities, data classes, destinations, side-effect classes, and budgets an identity may exercise, adopted from the companion control-plane guide. At a gateway the scope is computed per principal per upstream, never per gateway.

**Trust class**: The provenance-derived label naming the authority of a unit's source, assigned deterministically from source class and capture channel and never from content. Every upstream result carries one.

**Cache scope**: The declared statement of whether a shared intermediary may cache a result at all. The revision named in Section 1.3 carries this as an explicit field, and a gateway is precisely the shared intermediary the field governs.

**Revocation epoch**: A monotonically increasing counter incremented on any entitlement, policy, catalogue, credential, or kill-switch change, included in every cache key so that a stale entry cannot survive a revocation.

**Degraded-operation contract**: The declared statement of what the gateway still does and what it stops doing when one or more upstreams, or the gateway's own dependencies, are unavailable. The term is adopted from the companion protocol guide.

**Added-hop latency**: The gateway's own contribution to end-to-end duration, measured as downstream response duration minus measured upstream service duration for the same attempt, excluding time spent awaiting human approval.

**Blast radius**: The set of principals, tenants, upstreams, and side-effect classes a single compromise or outage of the gateway can reach.

### 1.2 The Gateway Decision: Why the Intermediary Exists and When It Should Not

A gateway is a design commitment, not a default. It is warranted only where centralisation buys something a direct client cannot, and it is refused where it would buy nothing and cost an availability hop.

**What centralisation buys**: Five benefits justify the hop, and each must be named as an actual requirement before the gateway is built.

- **Policy in one place**: Disclosure and invocation rules are evaluated once against canonical arguments, so a rule change reaches every agent without editing every agent.
- **Credential custody**: Upstream secrets live behind the intermediary, so a compromised agent yields no upstream token.
- **Auditing**: One correlated evidence stream reconstructs who called what, under whose identity, against which definition, with what effect.
- **Caching**: Read results are reused across callers who share an authority boundary, reducing cost and upstream load.
- **A single pinning point**: One approved definition snapshot governs every agent, so drift is detected once rather than per agent.

**What centralisation costs**: Three costs are unavoidable and must be priced before commitment.

- **A new single point of failure**: Every agent's tool access now depends on one system that did not previously exist in the path. The gateway's own availability multiplies against every upstream's.
- **An added hop**: Authentication, policy evaluation, catalogue lookup, queueing, translation, scanning, and serialisation each add latency the direct path did not carry.
- **A concentrated blast radius**: One compromised gateway holds every credential, sees every argument, and reaches every upstream. Custody converts many small exposures into one large one.

**When connecting directly is the better choice**: Use a direct MCP client, governed by the companion protocol guide, and do not build a gateway, where all of the following hold: a single caller or a single team connects to no more than 3 pinned servers; no shared identity, cross-tenant boundary, transport conversion, or central audit obligation exists; the caller's own process can enforce pinning, authorization, and isolation; and no upstream credential would otherwise sit inside a model-reachable process. Under those conditions the gateway adds a failure domain and a latency budget in exchange for governance nobody requires.

**Refuse the gateway outright** in four further cases. Where data residency, latency floors, or isolation requirements forbid centralising the byte path, deploy regional or tenant-local instances receiving signed desired state instead of one global instance. Where the proposal is one organisation-wide instance holding every credential and executing every tool, refuse it: that design maximises blast radius and is the failure the pattern is most often used to create. Where the intent is to make an unvetted upstream acceptable by placing a proxy in front of it, refuse it: mediation does not confer trustworthiness. Where deterministic application code already knows the exact narrow operation to call, refuse it: an ordinary authorized API call is cheaper and carries fewer moving parts.

**Gateway Warrant Decision Table**:

| Observable condition | Direct-client sufficiency | Verdict |
| :-- | :-- | :-- |
| 1 caller, 3 or fewer pinned read-only servers | Client enforces pinning and isolation | Refuse; use a direct client |
| 4 or more agents sharing overlapping upstreams | Per-agent config drift is unmanageable | Build the gateway |
| Upstream credentials would sit in model-reachable processes | Not achievable in-process | Build the gateway |
| 2 or more tenants must not observe each other | Not achievable in-process | Build the gateway; isolate per Phase 4 |
| Central audit or approval obligation is contractual | Client logs are not correlated | Build the gateway |
| Residency or latency forbids a central byte path | Not applicable | Build regional or cell instances |
| Proposal is one global instance holding all credentials | Not applicable | Refuse the topology; partition it |
| Purpose is to legitimise an unvetted upstream | Not applicable | Refuse; vet or exclude the upstream |
| Deterministic code knows the exact operation | Direct authorized API call | Refuse; call the API |

### 1.3 The Boundary Against Client-Side Integration and the Speaking Revision

This guide owns the gateway. The client-side integration machinery is owned by the companion protocol guide named in Section VII, and is not restated here.

**What the companion protocol guide owns**: Server discovery and admission approval; revision and capability negotiation; definition pinning, hashing, and drift classification; per-server authority scoping and the block on cross-server escalation; and the isolation of untrusted server-supplied content across tool definitions, resource content, prompt text, and results. A gateway executes all five, but it executes them as that guide specifies. Agents building a gateway must read that guide first and treat its procedures as the implementation of every step here that touches a single upstream.

**What this guide owns**: The intermediary itself. Whether to have one; how it takes custody of credentials without becoming a confused deputy; how it carries a calling principal across the hop; how it keeps tenants apart while they share pools, caches, indexes, and processes; how it keys a cache so a result never crosses an authority boundary; how it fails without stalling every agent behind it; and what evidence it must leave.

**The speaking revision governs every protocol claim**: A protocol revision removes mechanisms as well as adding them, so no capability may be assumed from an earlier revision. Every protocol statement in this guide is attributed to the `2026-07-28` revision, verified during this conversion against the specification's own changelog, and none of it may be carried into another revision without re-checking.

- **Removed in that revision**: protocol-level sessions and the session header; the initialization handshake; the standalone server-to-client stream, replaced by an opt-in subscription stream; stream resumability and message redelivery; and the liveness method, the log-level method, and the roots list-changed notification. A gateway must not route on protocol session affinity for current traffic, must not synthesize a session identifier, must not use the removed liveness method as a health probe, and must not manufacture resumability an upstream does not provide.
- **Deprecated in that revision**: the roots, sampling, and logging features, and the legacy two-endpoint streaming transport. The specification carries a formal Active, Deprecated, and Removed lifecycle with a minimum twelve-month deprecation window, verified during this conversion. A gateway must not adapt a modern downstream request into a deprecated upstream feature, must not offer a deprecated feature as a gateway service, and must record an expiry date against any integration that depends on one.
- **Added in that revision and load-bearing here**: required method and name request headers, which let a gateway route and meter without inspecting a message body; result cacheability fields carrying a freshness hint and an explicit scope value declaring whether a shared intermediary may cache the result at all; and trace-context propagation conventions, which carry correlation across the hop.

**Legacy upstreams sit behind adapters, never in the current path**: Where an explicitly approved legacy upstream must be reached, isolate it behind a tested per-revision adapter that retains real upstream session state, maps cancellation and errors correctly, and declares every capability it cannot support. An adapter must never present application state or gateway state as a protocol session, and must never weaken a newer revision's security semantics to satisfy an older one.

### 1.4 Execution Tier Partition

Every phase of this framework is assignable to one execution tier. At a gateway the partition is unusually simple, and its simplicity is the design property that makes the intermediary safe to build.

**Deterministic tier**: Owns routing and alias resolution, per-principal authorization, credential custody and injection, definition pinning and drift enforcement, tenancy isolation, cache keying and invalidation, circuit breaking, quota reservation, and the audit log. Each requires exactness, reproducibility, auditability, or a scale that model inference cannot supply, and each is a decision an adversary would want to influence.

**Model tier**: Owns nothing at the gateway. This is stated plainly as a design property rather than as a current-capability observation. The model tier operates on the caller's side of the hop, where it chooses among tools the gateway has already made eligible, constructs arguments, and interprets a released result. No model output selects a route, sets a tenant, mints a credential, satisfies an approval, resolves a drift finding, chooses a cache key, opens or closes a breaker, or operates a kill switch. A gateway that admits model judgement into any of those is not a gateway; it is an unbounded agent wearing one.

**Hybrid tier**: Owns exactly two handoffs, both on the caller's side of the boundary and both with the deterministic tier holding final authority. First, exposure narrowing: the gateway computes the eligible set deterministically, a retrieval component may rank within it, and a selection outside the eligible set is rejected rather than reconciled. Second, argument repair: the gateway returns a structured validation error, the caller's model proposes a correction, and the gateway re-runs every check from the beginning, rejecting any repair that changes intent, target, destination, amount, data scope, or side effect.

**Tier Ownership by Framework Phase**:

| Phase | Deterministic tier owns | Model tier owns | Authority on disagreement |
| :-- | :-- | :-- | :-- |
| 1. Warrant and topology | Decision gate, topology, blast-radius budget | Nothing | Deterministic; the gate is a checklist, not a judgement |
| 2. Registration and custody | Vetting, canonical records, credential references, snapshot publication | Nothing | Deterministic; no model-initiated onboarding |
| 3. Identity and authorization | Principal binding, policy evaluation, credential attenuation | Nothing | Deterministic; model reasoning is never a policy result |
| 4. Tenancy and caching | Partition keys, cache keys, revocation epoch, scope classification | Nothing | Deterministic; a cache key is arithmetic, not judgement |
| 5. Invocation | Alias resolution, drift block, dispatch, retry ownership, result validation | Tool choice and argument construction, on the caller's side | Deterministic; an invalid proposal is rejected |
| 6. Health and audit | Probes, breaker state, degradation, kill switch, evidence emission | Nothing | Deterministic; availability is measured, not judged |

**What the deterministic tier rejects unconditionally**: A request in which a model-controllable field sets tenant, principal, role, virtual server, entitlement, route, credential reference, approval status, idempotency key, quota, or policy input; a downstream credential offered as upstream authority; an exposed alias resolving to more than one canonical tool or to none; a call whose current definition hash differs from its pinned hash; a cache entry whose key omits principal, policy version, definition hash, or revocation epoch; a dispatch under an expired execution grant; and any write dispatched without a durable record persisted before it.

***

## II. Operational Framework: Mediated Multi-Tenant Tool Access Under Centralised Credential Custody

The framework assumes the decision gate in Section 1.2 has returned build. Phases 1 and 2 are performed once per deployment and once per upstream respectively. Phases 3 through 5 execute on every request. Phase 6 runs continuously alongside them and gates every release. Each phase consumes only artifacts earlier phases produced.

### Phase 1: Gateway Warrant and Topology Commitment

**Objective**: Establish that the intermediary is warranted, commit a topology whose blast radius is bounded and stated, and declare the non-bypass invariant before any upstream is registered.

#### Step 1.1: Run the Gateway-Versus-Direct Decision Gate

**Required Actions**:

- Evaluate every row of the warrant decision table in Section 1.2 against the actual deployment, recording the observed condition and the verdict rather than an intention.
- Name at least 1 of the 5 centralisation benefits as a requirement the deployment actually carries, with the party who carries it.
- Price the 3 centralisation costs numerically: the availability the gateway must hold for end-to-end availability to remain acceptable, the added-hop latency budget in milliseconds, and the count of credentials the gateway would concentrate.
- Refuse the gateway and record the refusal where no benefit is a stated requirement, where a direct client governed by the companion protocol guide enforces the same controls, or where the proposal is one global instance holding every credential.
- Record the decision as a dated artifact naming the alternative that was rejected and why.

**Required Outputs**:

- A warrant record carrying one verdict per decision-table row.
- A benefit register naming at least 1 required benefit and its owner.
- A cost estimate stating required gateway availability, added-hop latency budget, and concentrated credential count.

**Quality Checkpoints**:

- At least 1 centralisation benefit is a stated deployment requirement; a gateway justified only by convention is refused.
- Required gateway availability is stated numerically and exceeds the lowest end-to-end availability the deployment will accept.
- The added-hop latency budget is stated in milliseconds and is at most 25 percent of the task latency budget; a larger share halts the design for re-scoping.

***

#### Step 1.2: Select the Deployment Topology and Declare the Blast Radius

**Required Actions**:

- Select exactly 1 topology from centralised cluster, regional instances under global desired state, tenant-dedicated cells, node-local instances, or hierarchical aggregation, and record the constraint that forced the choice.
- Declare the blast radius of a single instance as an explicit count of principals, tenants, upstreams, and the highest side-effect class it may reach.
- Cap the blast radius: no single instance may hold credentials for upstreams spanning more than 1 trust tier above read-only private without tenant-dedicated isolation.
- Declare availability, residency, partition, consistency, and maximum-staleness behaviour for catalogue and policy state, with a numeric propagation deadline.
- Route emergency denials on a channel independent of ordinary catalogue propagation, and state its own deadline separately.
- Cap proxy depth at 2 hops where hierarchical aggregation is unavoidable, and assign exactly 1 policy owner and 1 retry owner per decision across the chain.

**Required Outputs**:

- A topology record naming the selected topology and the forcing constraint.
- A blast-radius declaration with counts per dimension and the highest reachable side-effect class.
- A propagation contract stating ordinary and emergency deadlines in seconds.

**Quality Checkpoints**:

- Exactly 1 topology is selected; a deployment claiming two topologies simultaneously is rejected.
- Emergency denial propagation is at most 60 seconds and is strictly faster than ordinary catalogue propagation.
- No instance's declared blast radius includes a destructive or arbitrary-execution upstream without tenant-dedicated isolation.

***

#### Step 1.3: Declare the Non-Bypass Invariant and Enumerate Every Enforcement Path

**Required Actions**:

- State the invariant that no caller may reach an approved upstream except through the gateway, and enumerate the network, credential, and process controls that make it true rather than intended.
- Enumerate every path that reaches gateway code, including loopback, administrative, health, callback, inspector, compatibility, and evaluation listeners, and confirm each enforces the same authorization checks as the primary path.
- Remove direct upstream network reachability, secret-manager access, and local-process launch capability from every model-hosting worker.
- Separate the runtime plane from the management plane: runtime instances read signed immutable snapshots and hold no permission to publish catalogue, policy, or credential changes.
- Record an enforcement inventory listing each path, its authentication method, its policy evaluation point, and the test that proves it.

**Required Outputs**:

- A non-bypass invariant statement with its supporting controls named.
- An enforcement path inventory with one row per listener.
- A plane-separation record stating which identities may publish and which may only read.

**Quality Checkpoints**:

- Every enumerated path evaluates the same policy as the primary path; an unauthenticated auxiliary listener halts deployment.
- No model-hosting worker holds network reachability to an approved upstream, secret-manager credentials, or process-launch capability.
- No runtime identity holds publication permission on the catalogue, policy bundle, or credential store.

***

### Phase 2: Upstream Registration and Credential Custody

**Objective**: Admit each upstream through isolated vetting, take custody of its credentials as references rather than values, and publish an immutable approved snapshot that every runtime instance serves identically.

#### Step 2.1: Vet the Upstream in Isolation and Create the Canonical Record

**Required Actions**:

- Accept a signed owner request and create an immutable candidate record before any connection is attempted.
- Verify publisher, source, signature or provenance, artifact digest, dependency manifest, vulnerability state, licence, maintenance status, and endpoint or package identity, following the admission procedure of the companion protocol guide.
- Launch the candidate only in an isolated environment with synthetic credentials, canary data, no production secrets, and deny-by-default egress.
- Enumerate every advertised primitive under bounded pagination, snapshot the complete definitions, and compute the definition hash for each.
- Compare declared side effects, required scopes, and destinations against observed process, network, filesystem, and service behaviour, and treat any contradiction as a rejection rather than a note.
- Create the canonical server record and one canonical tool record per tool version, carrying owner, trust tier, tenant boundary, region, supported revisions, enabled primitives, required egress, side-effect class, reversibility, data and destination classes, required scopes, timeout, idempotency behaviour, expected postcondition, approval class, and lifecycle state.
- Cap automated vetting at 2 full runs; ambiguity exits to named human review, and automation may never widen a scope or weaken a test to obtain approval.

**Canonical Record Layers and Their Binding**:

| Layer | Content | What binds to it | Never binds to it |
| :-- | :-- | :-- | :-- |
| Source definition | Exactly what the vetted upstream advertised | Invocation policy, approval, drift comparison | Client-facing display |
| Canonical definition | Normalised internal representation | Policy input, cache key, retrieval index | Caller-visible naming |
| Client projection | Namespaced or rewritten definition exposed to one caller class | Model selection, caller-visible naming | Authority of any kind |

**Required Outputs**:

- An immutable candidate record with provenance and vetting evidence attached.
- A canonical server record and one canonical tool record per approved tool version.
- Three separately computed hashes covering source definition, canonical definition, and client projection.

**Quality Checkpoints**:

- Every approved tool version carries all three hashes and a named owner; a record missing either is not publishable.
- No approval is granted where declared behaviour contradicts observed behaviour in the isolated environment.
- Automated vetting has run at most 2 times before human review; a third automated run is prohibited.

***

#### Step 2.2: Take Custody of Upstream Credentials as References

**Required Actions**:

- Store only a credential reference in the canonical record, never a secret value, and resolve the reference inside the gateway process or an isolated executor at dispatch time.
- Register the upstream's authorization issuer and pin the accepted issuer set per upstream; reject a token minted by any other issuer for that upstream.
- Key persisted client credentials by the issuing authorization server's identifier, never reuse them against a different authorization server, and re-register when the authorization server changes.
- Validate discovered protected-resource metadata URLs, DNS resolution, redirects, and issuer relationships against egress policy before any fetch, so that discovery cannot be turned into a server-side request forgery.
- Declare, per upstream, which credential mode applies: constrained on-behalf-of delegation through token exchange, a per-user upstream grant, or a narrowly scoped workload credential restricted to service-owned operations.
- Prohibit shared service accounts as a substitute for human identity, and record the prohibition as a policy rule rather than a convention.
- Encrypt credential stores per tenant, serialise refresh so concurrent callers cannot race, rotate keys on a stated schedule, and revoke on upstream disablement within the emergency propagation deadline.

**Required Outputs**:

- A credential reference per upstream with its resolution point named.
- A pinned issuer set per upstream and a declared credential mode.
- A rotation and revocation schedule with numeric intervals and deadlines.

**Quality Checkpoints**:

- No secret value appears in a catalogue record, a log, a trace, an error, a prompt, or a workflow history; any occurrence halts publication.
- Every upstream has exactly 1 declared credential mode and at least 1 pinned issuer.
- Credential revocation on upstream disablement completes within the emergency propagation deadline declared in Step 1.2.

***

#### Step 2.3: Publish the Approved Catalogue Snapshot Atomically

**Required Actions**:

- Compose catalogues from approved snapshots only, never from live unaudited upstream responses.
- Record per snapshot the discovery time, protocol revision, declared capabilities, deterministic order hash, complete definitions, list version, policy status, and freshness deadline.
- Build retrieval indexes, alias maps, and cache namespaces from the candidate snapshot before the pointer moves, never after.
- Run catalogue integrity, namespace collision, policy, entitlement, retrieval, compatibility, and canary-call tests against the candidate, and publish only when all pass.
- Switch the active catalogue pointer atomically, retaining the prior snapshot for rollback, and purge affected list, retrieval, authorization, and result caches in the same operation.
- Verify with a signed probe that every instance in every region serves the intended manifest hash, retrying failed targets with bounded backoff for at most 5 controller attempts in one cycle.
- Exit converged only where desired and actual state match; exit degraded with every difference quarantined, disabled, or assigned to a named owner, and route a repeated mismatch hash to incident review rather than looping.

**Required Outputs**:

- A signed immutable catalogue snapshot with a manifest hash.
- A convergence record naming each region and the hash it confirmed serving.
- A rollback pointer to the immediately prior snapshot.

**Quality Checkpoints**:

- The active pointer moves atomically; no instance ever serves a partially built catalogue.
- Every region confirms the intended manifest hash within the ordinary propagation deadline, or the release is rolled back.
- A hot reload changes a pointer to prevalidated state only; in-place mutation of an active definition is prohibited without exception.

***

### Phase 3: Principal Propagation and Per-Principal Authorization

**Objective**: Carry the calling principal across the hop intact and make every disclosure and invocation decision a function of that principal, so that credential custody does not convert the gateway into a confused deputy.

#### Step 3.1: Bind the Calling Principal from Trusted State

**Required Actions**:

- Authenticate the downstream client, the deployed agent workload, and the human user as three separable facts, and record which of the three were established rather than assumed.
- Bind pseudonymous user identifier, tenant identifier, agent identity and version, workload identity reference, actor, subject, delegation chain, purpose code, environment, region, and original authorization time from trusted infrastructure state.
- Reject any request in which a model-controllable field carries an identity, tenant, role, purpose, entitlement, or delegation value; these fields are injected by the gateway after validation, never accepted from the caller's payload.
- Validate the presented credential's signature, issuer, audience, expiry, not-before time, tenant, scope set, and confirmation claims before any catalogue work, and reject a credential whose audience is not the gateway itself.
- Halt and return a stable reason where a consequential request lacks an established user identity, an established tenant, or a declared purpose; at most 1 focused clarification may be requested.
- Record the delegation chain depth and reject a chain exceeding the declared maximum, since each hop is an opportunity to lose actor or subject.

**Required Outputs**:

- A bound principal record carrying every identity dimension and its establishment method.
- A credential validation record naming issuer, audience, scope set, and expiry.
- A delegation chain record with its depth.

**Quality Checkpoints**:

- Every identity dimension carries a stated establishment method; a dimension marked assumed halts the request.
- The presented credential's audience is the gateway; a credential minted for another resource is rejected rather than forwarded.
- Delegation depth does not exceed the declared maximum, which is at most 3 for interactive work.

***

#### Step 3.2: Authorize Disclosure Before Any Name Is Revealed

**Required Actions**:

- Pin the active catalogue version, policy version, entitlement snapshot, virtual server identifier, and alias-map version for the whole request, and record the pinned tuple.
- Compute the eligible set as a hard intersection of virtual-server membership, tenant, principal entitlement, agent allowlist, purpose, environment, region, protocol compatibility, lifecycle state, health, risk ceiling, data class, approval availability, quota, and emergency denials.
- Treat the intersection as a set operation, never as a ranking feature; a semantic relevance score is never an input to eligibility.
- Return only authorized names and counts, since the existence of a tool is itself disclosable information about another tenant's estate.
- Recompute the eligible set per request rather than binding it to a connection, because list contents vary by per-request authorization under the revision named in Section 1.3.
- Where the eligible set exceeds the direct-exposure threshold, expose a bounded subset through the retrieval discipline of the companion retrieval guide, drawing candidates only from the eligible set and never from the global catalogue.
- Exit with an explicit capability-unavailable result where the eligible set is empty; never widen the search to manufacture a candidate.

**Required Outputs**:

- A pinned version tuple recorded against the request.
- An eligible set with exclusion counts grouped by bounded reason code.
- An ordered exposed set with its set hash and each entry's projection hash.

**Quality Checkpoints**:

- Every exposed name is authorized for the bound principal; a single unauthorized name in a list response is a cross-tenant disclosure.
- Eligibility is computed before any retrieval or ranking runs; a retrieval result that precedes eligibility is discarded.
- An empty eligible set exits as capability-unavailable rather than as a broader search.

***

#### Step 3.3: Mint Upstream Authority as an Intersection, Never a Passthrough

**Required Actions**:

- Evaluate whether this principal may invoke this canonical tool with these canonical arguments, before any upstream credential is requested.
- Obtain a separate upstream credential whose audience is the exact upstream resource, using the resource-indicator parameter in both the authorization request and the token request, and identifying the upstream by its canonical URI.
- Compute the credential's authority as the intersection of the user grant, the agent grant, the declared task purpose, the gateway policy decision, and the tool's declared requirement, and reject issuance where the resulting credential would exceed that intersection on audience, scope, tenant, actor, subject, or lifetime.
- Never forward the downstream credential upstream: the protocol requires that a server accept only tokens valid for its own resources and prohibits accepting or transiting any other token, so a passthrough is both a protocol violation and the confused-deputy failure itself.
- Use constrained on-behalf-of token exchange where the identity provider and upstream trust model support it, and enforce attenuation at both the authorization server and the gateway, since the exchange mechanism permits but does not guarantee narrowing.
- Bind per-client consent to the tuple of user, downstream client, upstream resource, scope set, purpose, and expiry, and never let a prior browser consent silently authorize a newly registered client.
- Attach the credential outside model-visible content, and on an upstream authorization failure return a stable reason without exposing the credential, the scope set, or the issuer's error detail.
- Handle an insufficient-scope challenge by computing the union of previously requested scopes and the challenged scopes, re-authorizing once, and treating a second failure as permanent rather than retrying.

**Credential Custody Failure Modes and Their Controls**:

| Failure mode | Observable symptom | Control that prevents it |
| :-- | :-- | :-- |
| Token passthrough | Upstream sees the downstream audience | Reject any dispatch whose credential audience is the gateway |
| Ambient authority | Two principals produce identical upstream credentials | Bind principal into every credential request and log the binding |
| Scope amplification | Granted scope exceeds the computed intersection | Compare granted against intersection before dispatch; deny on excess |
| Actor or subject loss | Upstream logs show only the gateway workload | Require actor and subject in every exchanged credential |
| Consent reuse | A new client inherits an earlier client's grant | Key consent by downstream client identifier and expiry |
| Impersonation by service account | Human action attributed to a shared workload | Prohibit workload credentials for user-initiated side effects |

**Required Outputs**:

- A policy decision record with decision identifier, bundle and rule versions, effect, reason codes, obligations, and expiry.
- An upstream credential reference bound to audience, scopes, actor, subject, tenant, purpose, and lifetime.
- An attenuation record comparing granted authority against the computed intersection.

**Quality Checkpoints**:

- No dispatch carries a credential whose audience is the gateway; the credential attenuation violation target is 0.
- Every issued upstream credential names an actor and a subject; a credential naming only the gateway workload is rejected for user-initiated work.
- Approval, where required, binds the exact operation and is revalidated immediately before dispatch; an approval that predates a definition change is void.

***

### Phase 4: Tenancy Isolation and Cache Policy

**Objective**: Keep tenants that share the intermediary from observing or reaching one another through any shared resource, and key every cache so that a stored result can never be served across an authority boundary.

#### Step 4.1: Partition Every Shared Resource by Tenant

**Required Actions**:

- Enumerate every resource the gateway shares across callers: connection pools, supervised processes, protocol adapters, credential and token stores, state records, approval records, idempotency keys, retrieval indexes, queues, rate-limit buckets, caches, traces, logs, metrics, and evidence exports.
- Assign each enumerated resource a partition key naming the isolation dimension it enforces, and mark any resource with no partition key as a defect to be fixed before traffic, not a risk to be accepted.
- Key connection pools by upstream endpoint origin, verified transport identity, protocol revision, transport, tenant isolation class, and non-secret authorization class, and attach the per-request credential outside the pool.
- Refuse to multiplex personalised subscriptions, application handles, or supervised local processes across principals unless the upstream explicitly supports multi-tenant operation and negative tests prove isolation.
- Run supervised local upstreams as per-tenant or per-principal isolated processes by default, sharing a process only where the upstream is designed for shared multi-user operation.
- Drain pools on any change to endpoint resolution, transport identity, route, upstream version, protocol revision, policy, or tenant boundary.
- Prohibit identifier reuse across tenants for every correlation key the gateway mints, so that an identifier collision cannot join two tenants' evidence.

**Shared-Resource Partition Requirements**:

| Shared resource | Minimum partition key | Consequence of an unpartitioned instance |
| :-- | :-- | :-- |
| Connection pool | Upstream identity, revision, tenant isolation class | A tenant's connection carries another tenant's request |
| Supervised local process | Tenant, or principal for personalised state | Host-resident state leaks between tenants |
| Token and credential store | Tenant, with per-tenant encryption | One compromise exposes every tenant's upstream authority |
| Approval and idempotency records | Tenant and principal | A replayed approval authorizes another tenant's write |
| Retrieval index | Eligible-set digest bound to the principal | Search reveals the existence of another tenant's tools |
| Result cache | Principal or declared shareability class | A cached read crosses an authority boundary |
| Traces, logs, evidence | Tenant, with access control on read | Cross-tenant disclosure through observability |

**Required Outputs**:

- A shared-resource inventory with a partition key per row.
- A pool configuration record naming every key component and the drain triggers.
- A process isolation record stating which upstreams run per tenant and which are shared, with the evidence for each shared decision.

**Quality Checkpoints**:

- Every enumerated shared resource carries a partition key; a resource with none blocks deployment rather than proceeding with a note.
- No supervised local upstream is shared across tenants without a passing negative isolation test recorded against that upstream version.
- The cross-tenant escape rate measured against adversarial fixtures is 0; any non-zero value halts release.

***

#### Step 4.2: Key Every Cache by Principal and Version

**Required Actions**:

- Maintain caches as separate stores by purpose rather than as one store with mixed contents, covering catalogue snapshots, eligibility views, upstream tool lists, retrieval results, credential metadata, and read results.
- Include in every read-result cache key the tenant, the principal or an explicitly declared shareability class, the canonical tool identity, the source definition hash, the canonical arguments, the policy version, the data version, the output projection, the freshness bound, and the revocation epoch.
- Include in every eligibility-view cache key the tenant, the principal or authorization-context hash, the agent, the purpose, the policy version, the entitlement snapshot, the catalogue version, the risk ceiling, the region, and the revocation epoch.
- Never store a reusable credential value in a general cache; cache only credential metadata keyed by issuer, subject, actor, client, audience, scope set, tenant, and revocation epoch.
- Increment the revocation epoch on any entitlement, policy, catalogue, definition, credential, approval, destination, scanner, or kill-switch change, and treat every entry carrying an earlier epoch as absent.
- Prefer versioned keys with short freshness bounds over long-lived entries with invalidation messaging, since a missed invalidation serves stale authority while a versioned miss merely costs a fetch.
- Ensure that no cache hit can bypass a current kill switch, a current policy decision, or a current definition check; the hit supplies content, never authorization.

**Required Outputs**:

- A cache inventory naming each store, its complete key composition, and its freshness bound.
- A revocation epoch definition listing every event that increments it.
- A key-completeness test suite asserting that omitting any key component produces a rejected entry.

**Quality Checkpoints**:

- Every read-result key contains principal or a declared shareability class, definition hash, policy version, and revocation epoch; a key missing any of the four is rejected at write time.
- No cache hit is served without a current authorization evaluation; the stale-cache rate target is 0.
- Credential values do not appear in any cache; only metadata is stored.

***

#### Step 4.3: Classify Cacheability and Honour the Declared Cache Scope

**Required Actions**:

- Classify every tool version as cacheable or non-cacheable at registration time, and record the classification on the canonical record rather than deciding it at request time.
- Cache only deterministic or explicitly cacheable reads whose authorization and freshness semantics are stable; never cache a write, an approval decision, a credential value, a volatile read without a data-version key, or a personalised result under a shared key.
- Honour the result cacheability fields the revision named in Section 1.3 defines: treat the freshness hint as an upper bound rather than a target, and treat the scope value as binding, so that a result marked private to its requester is never stored in any store a second principal can read.
- Treat an absent scope value on a legacy upstream as private, since a shared intermediary that guesses public on missing metadata converts a silence into a disclosure.
- Declare a shareability class explicitly where a read genuinely is common to all principals in a tenant, name the evidence that establishes it, and re-verify that evidence on every definition change.
- Bypass the cache entirely for any tool whose side-effect class is above read-only private, and record the bypass as a property of the class rather than as a per-request decision.
- Purge affected caches within the emergency propagation deadline on revocation, quarantine, or kill-switch activation, and verify the purge with a signed probe rather than assuming it.

**Required Outputs**:

- A cacheability classification on every canonical tool record.
- A shareability declaration with supporting evidence for each read cached across principals.
- A purge verification record per revocation event naming each store confirmed clear.

**Quality Checkpoints**:

- No tool above the read-only private side-effect class is cached; a cached write is a release-blocking defect.
- A result whose declared scope is private to its requester is never stored where a second principal can read it, and a missing scope value is treated as private.
- Cache purge on revocation completes and is probe-verified within the emergency propagation deadline declared in Step 1.2.

***

### Phase 5: Invocation Under Pinning, Drift Enforcement, and Single-Owner Retry

**Objective**: Resolve one exposed alias to exactly one approved capability, dispatch it under a narrow credential and a single retry owner, and release a result only after the deterministic tier has validated it.

#### Step 5.1: Resolve the Exposed Alias to Exactly One Canonical Capability

**Required Actions**:

- Resolve the exposed alias through the reversible alias map to exactly one canonical tool identity, source definition hash, upstream server identity, upstream tool name, protocol revision, adapter version, and route.
- Reject an alias that is unknown, ambiguous, stale, disabled, unexposed to this principal, or resolving to more than one canonical entry; last-registered-wins resolution is prohibited.
- Never route by fuzzy name, description similarity, or embedding score at invocation time; a similarity score is a ranking input on the caller's side and is never a route.
- Compare the upstream's currently advertised definition hash against the pinned hash and block the invocation on any difference, routing the difference to the drift classification of the companion protocol guide rather than judging it here.
- Normalise names for comparison, reject control and invisible characters, and detect homoglyph, case-folded, and separator-ambiguity collisions, retaining distinct namespaces or rejecting the newer registration where two tools collide.
- Prohibit any tool from presenting itself as another server, as required, as a system component, as the gateway, or as a security override, and treat such a claim as a poisoning finding rather than as metadata.
- Preserve a renamed tool's old alias only as a time-bounded pointer to the same immutable tool version, and never redirect an alias to a semantically different tool.

**Required Outputs**:

- A resolution record binding exposed alias to canonical identity, upstream identity, revision, adapter, and route.
- A hash comparison result stating pinned hash, observed hash, and verdict.
- A collision and impersonation scan result for the alias map version in force.

**Quality Checkpoints**:

- Exactly 1 canonical entry resolves from the exposed alias; 0 or 2 or more halts the request.
- The observed definition hash equals the pinned hash; a mismatch blocks invocation and is never overridden by an assessment that the change appears cosmetic.
- The collision prevention rate measured against labelled confusable fixtures is 100 percent before publication.

***

#### Step 5.2: Validate, Authorize, and Dispatch Under a Single Retry Owner

**Required Actions**:

- Parse the complete arguments and canonicalise types, text normalisation, paths, resource identifiers, units, timestamps, filters, and destinations before any policy evaluation.
- Validate the input schema, semantic constraints, tenant resource scope, data policy, side-effect preconditions, and current state, then inject trusted fields after validation rather than before.
- Run the bounded validation-repair loop of the companion tool-use guide, stopping after 2 repairs or 1 repeated canonical proposal hash, and exiting denied rather than repairing an unauthorized request into a different allowed action.
- Persist the logical operation, canonical argument hash, idempotency key, approval reference, and execution grant to durable storage before dispatching any write.
- Reserve quota and cost atomically before dispatch, allocate one absolute deadline across the whole request, and pass only the remaining budget to the upstream.
- Select a healthy upstream instance permitted by region, tenant, data class, and current circuit state, and acquire a correctly partitioned connection or process.
- Assign retry ownership to exactly 1 layer and disable or budget retries in every other layer, so that client, gateway, adapter, workflow, and upstream retries cannot multiply.
- Classify every failed attempt before responding, and treat authorization denial, policy denial, and malformed argument as permanent rather than transient; a credential failure exits to refresh or reauthorization, never to a blind network retry.
- Bound retries at 2 after the first attempt for interactive work and 4 for durable background work, using exponential backoff with full jitter, and lower those bounds for costly or high-impact tools.
- Leave the retry loop entirely on an unknown outcome, query the authoritative system by idempotency key or external operation identifier, and retry only where no effect is proven.

**Required Outputs**:

- A canonical argument record with its hash and the validation outcomes.
- A durable pre-dispatch record for every write, written before the first attempt.
- An attempt record per delivery, carrying attempt identifier, classification, backoff, and terminal state.

**Quality Checkpoints**:

- Retry amplification, computed as attempts divided by logical calls dispatched, is at most 1.5 in steady state; a higher value indicates stacked retry owners and halts release.
- No write is dispatched without a durable record persisted before it; the unknown side-effect rate is reported separately and never resolved by another attempt.
- Every failed attempt carries a classification from the closed error vocabulary; an unclassified failure is never retried.

***

#### Step 5.3: Validate the Result and Verify Consequential Postconditions

**Required Actions**:

- Validate response correlation, result or error shape, output schema, size, content types, tenant, origin, freshness, and provenance before the result leaves the gateway.
- Treat every element of the response as untrusted data, including text, structured content, resources, links, logs, error strings, metadata, and attachments, and apply the isolation discipline of the companion protocol guide.
- Scan for instruction-shaped content, tool-selection manipulation, secret material, personal data, malicious links, and executable payloads, and record detector identity and version with the verdict.
- Apply policy obligations, data-loss controls, redaction, truncation, and projection, preserving schema shape or returning an explicit blocked-field structure rather than silently deleting fields.
- Quarantine the result where a required scanner is unavailable or where a high-risk result is ambiguous, and never release a quarantined result on a detector's absence.
- Verify consequential postconditions against authoritative state rather than inferring success from a protocol-level or transport-level success response.
- Return a bounded normalised result carrying canonical origin, logical call identifier, terminal status, provenance, trust class, and any redaction or partial-result indicator.
- Report the terminal outcome as one of completed, partial, denied, failed, cancelled, quarantined, or unknown, and never collapse the seven into a success flag.

**Required Outputs**:

- A validated result record with schema outcome, provenance, and trust class.
- A scan record naming each detector, its version, and its verdict.
- A postcondition verification record for every call above the read-only private side-effect class.

**Quality Checkpoints**:

- Every consequential call carries a postcondition verification against authoritative state; a protocol success alone is never accepted as completion.
- No result is released while a required scanner is unavailable; the release path fails closed.
- The terminal outcome is drawn from the closed seven-value vocabulary; a free-text status is rejected.

***

### Phase 6: Failure Isolation, Degradation, and the Audit Record

**Objective**: Prevent one upstream's failure from becoming every agent's stall, declare what the gateway still does when a dependency is gone, and leave evidence sufficient to reconstruct any route and effect.

#### Step 6.1: Enforce Per-Upstream Timeouts and Circuit Breaking

**Required Actions**:

- Set one absolute deadline per request and allocate it across admission, catalogue resolution, retrieval, policy evaluation, credential acquisition, queueing, connection acquisition, upstream execution, scanning, verification, and response, passing only the remaining budget onward.
- Maintain circuit state per upstream server and, where one server carries tools of differing cost, per tool, so that one failing capability does not open the breaker for an unrelated one.
- Open the breaker on a rolling failure rate above 50 percent over a window of at least 20 attempts, on a latency percentile exceeding the declared budget by more than 100 percent, or on any security threshold breach, and fail fast during cooldown.
- Permit at most 3 half-open probes per cooldown period and close only after the configured verified-success threshold, never on transport success accompanied by invalid output.
- Maintain a bulkhead per upstream bounding concurrent calls, queue depth, and in-flight bytes, so that one slow upstream cannot exhaust the gateway's own capacity.
- Probe upstream health with the cheapest safe operation the speaking revision defines, verifying endpoint resolution, egress class, transport identity, and route before protocol traffic; the removed liveness method of earlier revisions is unavailable and must not be used.
- Bound health probing at 3 attempts per cycle with exponential backoff and full jitter, and stop rather than probing indefinitely; the next controller cycle retries after cooldown.
- Exit a health cycle in exactly one of ready, degraded, incompatible, denied, quarantined, or unavailable, and quarantine on any unapproved identity, revision, capability, or definition change rather than reconnecting.

**Required Outputs**:

- A deadline allocation record naming each stage and its share.
- A circuit and bulkhead configuration per upstream with thresholds and cooldowns.
- A health cycle record with its terminal state and the evidence for it.

**Quality Checkpoints**:

- Every stage of the request path carries an allocated share of one absolute deadline; an unbounded stage halts deployment.
- Circuit state is maintained per upstream at minimum; a single global breaker is rejected because it converts one failure into total unavailability.
- No health probe uses a method the speaking revision removed; a probe against a removed method is a configuration defect.

***

#### Step 6.2: Operate the Degraded-Operation Contract and the Kill Switch

**Required Actions**:

- Declare, before traffic, exactly what the gateway continues to do and what it stops doing when an upstream, the policy engine, the identity provider, the credential store, the catalogue store, or a required scanner is unavailable.
- Fail closed where identity, policy, approval, credential resolution, definition integrity, tenancy isolation, or high-risk result scanning is unavailable; state the closure as a rule rather than as a fallback.
- Permit a documented fail-open path only for tools whose side-effect class is read-only public or read-only private, and only under a pinned local allowlist, a bounded stale snapshot, no newly issued credentials, a duration of at most 15 minutes, an explicit alert, and mandatory later reconciliation.
- Remove an unavailable upstream's tools from newly computed views or mark them explicitly unavailable, and never substitute a semantically different tool for a missing one; a substitute must independently satisfy identity, policy, data, effect, and verification requirements.
- Report gateway availability and end-to-end tool availability as separate figures, since the gateway can be reachable while every path through it is not.
- Maintain kill switches scoped by gateway release, region, tenant, agent, virtual server, upstream, tool, version, credential, destination, side-effect class, and data class, operated on a path independent of the model and of the ordinary deployment pipeline.
- On activation, stop new disclosure and dispatch, open the relevant circuits, stop issuing and revoke affected credentials, cancel safe in-flight work, quarantine uncertain outputs, purge affected caches, preserve forensic state, and begin reconciliation.
- Test every kill-switch scope at least quarterly and after any topology change, measuring activation time and full propagation time separately.

**Required Outputs**:

- A degraded-operation contract stating the behaviour per unavailable dependency.
- A kill-switch inventory with one entry per scope and its tested activation time.
- A drill record per quarter naming each scope exercised and the measured times.

**Quality Checkpoints**:

- Every dependency has a declared unavailability behaviour; an undeclared dependency defaults to fail closed rather than to improvisation.
- No fail-open path exists for a write, sensitive data, cross-tenant access, security administration, or a definition drift condition.
- Kill-switch activation reaches first confirmed enforcement within 60 seconds and full propagation within the emergency deadline declared in Step 1.2.

***

#### Step 6.3: Emit the Correlated Audit Record and Compute the Metric Set

**Required Actions**:

- Emit one append-only event per registration, review, catalogue publication, policy decision, approval, credential issuance or exchange, quota reservation, dispatch, attempt, result scan, release, verification, drift finding, disablement, kill-switch action, and administrative access.
- Correlate events on a stable identifier set: one trace per interactive path, one durable task identifier surviving approval waits and failover, one request identifier deduplicating ingress, one logical call identifier surviving every retry, and a unique attempt identifier per delivery under one execution identifier.
- Bind every event to the source definition hash, catalogue version, policy version, entitlement snapshot, alias-map version, adapter version, and gateway release, so that the complete route is reconstructible from evidence alone.
- Enforce the disclosure boundary of the companion control-plane guide: record decision metadata, hashes, classifications, rule identifiers, and controlled references, and never record credential values, authorization codes, secrets, complete sensitive arguments, unrestricted results, or hidden reasoning content.
- Keep high-cardinality values in traces and logs rather than in metric labels, bounding metric dimensions to environment, region, release, tenant tier, protocol revision, transport, upstream class, tool class, policy effect, risk class, cache state, circuit state, and outcome.
- Use append-only storage with synchronised time, hash chaining or immutable retention where evidence must resist alteration, separated writer and auditor roles, signed exports, encryption, and a tested restoration procedure.
- Compute the metric set over a declared window and cohort, counting downstream requests, logical calls, and execution attempts as three separate populations.
- Sample logical calls for audit completeness on a recurring schedule and treat a missing correlated event as a defect rather than as a sampling artifact.

**Gateway Metric Definitions and Release Targets**:

| Metric | Definition | Target |
| :-- | :-- | :-- |
| Added-hop latency | Downstream response duration minus measured upstream duration for one attempt, approval time excluded | At most the Step 1.1 budget at the 95th percentile |
| Credential attenuation violation rate | Issued upstream credentials exceeding the computed intersection, over credentials evaluated | 0 |
| Cross-tenant escape rate | Evaluated calls exposing another tenant's tool, credential, state, cache entry, process, or result, over adversarial calls | 0 |
| Stale-cache rate | Cached responses violating current freshness, authorization, definition, or revocation policy, over cached responses served | 0 |
| Definition drift block rate | Invocations blocked on a hash mismatch, over invocations attempted against pinned tools | Reported; any non-zero value opens reconciliation |
| Retry amplification | Upstream execution attempts over logical calls dispatched | At most 1.5 |
| Unknown side-effect rate | Write calls ending without an authoritative outcome, over write calls dispatched | At most 0.5 percent |
| Kill-switch activation time | First confirmed enforcement minus authorized activation | At most 60 seconds |
| Audit completeness rate | Sampled logical calls carrying every required correlated event, over sampled logical calls | At least 99 percent |
| Gateway availability | Valid downstream requests answered within the gateway objective, over valid downstream requests | The Step 1.1 required figure |

**Required Outputs**:

- An event schema listing every required field per event type and its retention class.
- A correlation specification stating which identifier joins which events.
- A metric report computed over the declared window with one row per metric and its measured value.

**Quality Checkpoints**:

- Every sampled logical call reconstructs its complete route from evidence alone; audit completeness at or below 99 percent blocks release.
- No credential value, secret, complete sensitive argument, or hidden reasoning trace appears in any emitted event; a single occurrence halts evidence release and triggers re-instrumentation.
- Every metric in the table carries a measured value over a declared window; an estimated value is not a measurement and does not satisfy a release gate.

***

## III. Implementation Guidance for AI Agents

AI agents operating or provisioning an MCP tool gateway must follow systematic protocols ensuring that every routed call preserves identity, authority, provenance, version, and failure boundaries, and that no model output crosses into a deterministic decision. The following guidance translates the framework above into agent-executable instruction.

### A. Structured Execution Protocol

**Control Plane Components**:

1. **Warrant Agent**: Evaluates the decision gate in Section 1.2, prices the three costs, and returns build, refuse, or partition. It may refuse the gateway outright and its refusal is not overridable by a component downstream of it.
2. **Registration Agent**: Runs isolated vetting, creates canonical server and tool records, computes all three definition hashes, and publishes catalogue snapshots atomically. It never connects a candidate to production credentials.
3. **Identity Agent**: Binds the calling principal from trusted state, validates the presented credential, computes the authority intersection, and mints or exchanges upstream credentials. It alone touches credential values, and it exposes only references to every other component.
4. **Policy Agent**: Evaluates disclosure and invocation policy over canonical input and returns a structured decision. It holds no catalogue write permission and no credential access, so a policy compromise cannot mint authority.
5. **Dispatch Agent**: Resolves aliases, enforces the pinning comparison, acquires partitioned connections, dispatches, owns retry, and validates results. It is the only retry owner in the system.
6. **Isolation Agent**: Owns partition keys, cache keys, the revocation epoch, and purge verification. It may reject a cache write whose key is incomplete and may veto a release on an unpartitioned shared resource.
7. **Evidence Agent**: Writes the append-only log, enforces the disclosure boundary, computes the metric set, and may withhold an evidence export where a boundary breach is detected.

**The Model Holds No Role Here**: None of the seven components is a model-tier component. Where an agent implementation uses a model to summarise a vetting finding, draft an owner notification, or explain a denial to a caller, that output is advisory text attached to a decision the deterministic tier already made, and it is never the decision itself. An implementation that routes, authorizes, mints, purges, or releases on model output has removed the property that makes the intermediary safe.

**Workflow Execution Pattern**:

```
STATE: Gateway_Request_Dispatch
INPUTS:
  1. Bound principal record from Step 3.1
  2. Pinned version tuple and exposed set hash from Step 3.2
  3. Policy decision and upstream credential reference from Step 3.3
  4. Resolution record and hash comparison from Step 5.1
ACTIONS:
  1. Canonicalize arguments and inject trusted fields after validation
  2. Persist the durable pre-dispatch record for any write
  3. Reserve quota atomically and allocate the remaining deadline
  4. Acquire the partitioned connection and dispatch one attempt
VALIDATION:
  - resolved_canonical_entries == 1
  - observed_definition_hash == pinned_definition_hash
  - upstream_credential_audience != gateway_audience
  - granted_authority SUBSET_OF computed_intersection
  - model_supplied_trusted_fields == 0
  - durable_record_persisted == TRUE IF side_effect_class > read_only_private
  - remaining_deadline_ms > 0
TRANSITIONS:
  IF all_validations_pass THEN next_state = Await_Upstream_Result
  IF hash_mismatch THEN next_state = Quarantine_And_Reconcile
  IF credential_check_failed THEN next_state = Halt_Confused_Deputy
  IF validation_failed THEN next_state = Gateway_Error_Handling
```

**Two-Phase Action Pattern**: Emit the complete dispatch intent with its resolved canonical identity, its credential intersection, and its reserved quota without executing it; confirm it against the validation block while no upstream connection is held and no credential is attached; commit only after validation passes, writing the durable record and the dispatch event in the same operation.

**Approval Gate**: Human authorisation is required before any dispatch whose side-effect class is destructive, financial or security change, externally visible write, or arbitrary execution; before any upstream registration that broadens an existing authority scope; before any topology change altering the declared blast radius; and before any fail-open activation. The approval binds principal, downstream client, canonical tool, source definition hash, canonical arguments, destination, disclosed data, credential scopes, expected effect, policy version, and expiry, and is revalidated immediately before dispatch. An approver's modification creates a new proposal with a new operation hash rather than mutating the approved artifact. At most 1 clarification and 1 revised approval request are permitted for one intent; a second denial, an expiry, a repeated operation hash, or any security signal exits to a named owner.

**Context Management Requirements**:

- Hold the pinned version tuple, principal record, policy decision, and budget ledger in durable state, since an approval wait may outlive any single process.
- Write a handoff record naming pinned versions, remaining budget, in-flight operation identifiers, and approval state at every process or region boundary, and re-verify the tuple after the handoff rather than inheriting it.
- Bound the gateway's own added context: expose the smallest complete tool set rather than the full approved surface, and count exposure bytes against the caller's budget rather than treating them as free.

### B. Quality Assurance Checkpoints

**Checkpoint 1: Warrant and Topology Integrity (After Phase 1)**

- **Automated Check**: At least 1 centralisation benefit is a stated requirement; exactly 1 topology is selected; required gateway availability and added-hop budget are numeric; every enumerated enforcement path evaluates the primary policy; no model-hosting worker holds upstream reachability or secret access.
- **Agent Action on Pass**: Proceed to upstream registration.
- **Agent Action on Failure**: Halt and return the specific warrant or topology defect; no upstream is registered against an unjustified gateway.
- **Human Review Trigger**: A declared blast radius spanning more than 1 trust tier, or a proposal for a single global instance.

**Checkpoint 2: Registration and Custody Integrity (After Phase 2)**

- **Automated Check**: Every approved tool version carries three hashes, an owner, and a side-effect class; every upstream carries exactly 1 credential mode and at least 1 pinned issuer; no secret value appears in any record; the active pointer moved atomically and every region confirmed the manifest hash.
- **Agent Action on Pass**: Open the gateway to traffic for the newly published cohort.
- **Agent Action on Failure**: Roll back to the prior snapshot and quarantine the failing candidate; a partially converged catalogue is never served.
- **Human Review Trigger**: Any contradiction between declared and observed upstream behaviour, or a second failed automated vetting run.

**Checkpoint 3: Identity and Authorization Integrity (Per Request, After Phase 3)**

- **Automated Check**: Every identity dimension carries an establishment method; the presented credential's audience is the gateway; delegation depth is within bound; the eligible set was computed before any ranking; every issued upstream credential names actor and subject and falls within the computed intersection.
- **Agent Action on Pass**: Proceed to invocation.
- **Agent Action on Failure**: Deny with a stable reason code and record the denial; an authorization failure is never repaired by argument variation.
- **Human Review Trigger**: Any credential issued outside the computed intersection, or any unauthorized name appearing in a list response.

**Checkpoint 4: Isolation and Cache Integrity (Continuous, After Phase 4)**

- **Automated Check**: Every shared resource carries a partition key; every read-result key carries principal or declared shareability, definition hash, policy version, and revocation epoch; no tool above read-only private is cached; purge on revocation is probe-verified within the emergency deadline.
- **Agent Action on Pass**: Permit cache serving for the classified cohort.
- **Agent Action on Failure**: Disable the affected cache store entirely rather than serving under an incomplete key.
- **Human Review Trigger**: Any non-zero cross-tenant escape or stale-cache measurement.

**Checkpoint 5: Invocation Integrity (Per Request, After Phase 5)**

- **Automated Check**: Exactly 1 canonical entry resolved; observed hash equals pinned hash; retry amplification within bound; every write preceded by a durable record; every consequential result postcondition-verified; terminal outcome drawn from the closed vocabulary.
- **Agent Action on Pass**: Release the normalised result to the caller.
- **Agent Action on Failure**: Quarantine the result and return the terminal outcome that actually occurred, including unknown where the effect is unestablished.
- **Human Review Trigger**: An unknown side-effect rate above 0.5 percent, or any definition hash mismatch on an approved tool.

**Checkpoint 6: Availability and Evidence Integrity (After Phase 6)**

- **Automated Check**: Every request stage carries a deadline share; circuit state is per upstream; every dependency has a declared unavailability behaviour; kill-switch activation measured within 60 seconds; audit completeness at least 99 percent; no disclosure breach in the sampled window.
- **Agent Action on Pass**: Release the metric report and permit promotion of the configuration.
- **Agent Action on Failure**: Withhold promotion and name the missing evidence; a configuration is never promoted on clean-condition results alone.
- **Human Review Trigger**: Any disclosure breach, any failed kill-switch drill, or an end-to-end availability shortfall against the Step 1.1 figure.

**Checkpoint Documentation Template**:

```
CHECKPOINT_ID:
CHECKPOINT_NAME:
PHASE_BOUNDARY:
PINNED_VERSION_TUPLE:
VALIDATION_CRITERIA:
MEASURED_VALUE:
PASS_CONDITION:
PASS_ACTION:
FAIL_ACTION:
HUMAN_REVIEW_TRIGGER:
RESPONSIBLE_COMPONENT:
```

### C. Error Handling and Troubleshooting

**Error Type 1: Confused Deputy at the Credential Boundary**

- **Symptoms**: Upstream logs attribute an action to the gateway workload rather than to a user; two distinct principals produce identical upstream credentials; an upstream accepts a credential whose audience names the gateway; granted scopes exceed the computed intersection.
- **Diagnostic Steps**: Trace the credential from downstream validation through exchange to dispatch, comparing audience, actor, subject, tenant, scope set, and lifetime at each hop against the intersection recorded in Step 3.3; confirm whether the exchange narrowed the authority or merely reissued it.
- **Resolution Protocol**: Option A, replace the shared workload credential with constrained on-behalf-of exchange and enforce attenuation at both the authorization server and the gateway. Option B, where exchange is unavailable, switch the upstream to per-user grants and restrict the workload credential to service-owned operations only. Option C, disable the affected upstream and route its traffic to a direct client under the companion protocol guide until the identity path is corrected.
- **Escalation Trigger**: Any credential issued outside the computed intersection halts issuance for that upstream immediately; this class is never resolved by retry, and a second occurrence after correction escalates to the named identity owner.

**Error Type 2: Cross-Tenant Leakage Through a Shared Resource**

- **Symptoms**: A tool name, cached result, connection, process, index entry, approval record, or trace appears under a tenant that is not entitled to it; an adversarial fixture returns another tenant's content; identifier collision joins two tenants' evidence.
- **Diagnostic Steps**: Enumerate the shared-resource inventory from Step 4.1 and locate every row whose partition key omits the dimension that leaked; determine whether the leak is a missing key, a key computed after the lookup, or an identifier reused across tenants.
- **Resolution Protocol**: Option A, add the missing dimension to the partition key and invalidate every entry written under the previous key. Option B, disable the shared resource and fall back to per-tenant instances until the key is corrected. Option C, where the upstream itself is the shared component, move it to per-tenant supervised processes.
- **Escalation Trigger**: Any confirmed cross-tenant exposure activates the tenant-scoped kill switch immediately and escalates to the named security owner; the release is blocked until the adversarial fixture returns 0.

**Error Type 3: Definition Drift on an Approved Tool**

- **Symptoms**: The observed definition hash differs from the pinned hash at disclosure, approval, dispatch, retry, or scheduled refresh; an upstream deployment coincides with a change in advertised scopes, destinations, or side effects; a description changes without a version change.
- **Diagnostic Steps**: Compute the semantic difference in addition to the hash difference, and classify it as approved additive, approved removal, cosmetic projection, compatible schema change, authority broadening, semantic change, suspicious drift, or unreachable, using the classification of the companion protocol guide.
- **Resolution Protocol**: Option A, for an approved additive or cosmetic change, rebuild an immutable candidate catalogue and republish through Step 2.3. Option B, for any material change to definition, scope, destination, effect, identity, or provenance, quarantine the tool and re-enter isolated vetting; existing approval does not transfer. Option C, where the upstream cannot explain the change, disable it and revoke its credentials.
- **Escalation Trigger**: A hash mismatch blocks the invocation on first occurrence and is never overridden; a second unexplained mismatch on one upstream within 30 days retires that upstream pending owner attestation.

**Error Type 4: The Gateway Becomes the Stall Point**

- **Symptoms**: Added-hop latency exceeds its budget at the 95th percentile; queue depth grows while upstream utilisation is flat; one upstream's slowness raises latency for unrelated tools; end-to-end availability falls while gateway availability holds.
- **Diagnostic Steps**: Decompose added-hop latency into authentication, policy evaluation, catalogue lookup, queueing, connection acquisition, translation, scanning, redaction, and serialisation, and identify which stage grew; confirm whether bulkheads are per upstream or shared.
- **Resolution Protocol**: Option A, isolate the offending upstream behind its own bulkhead and breaker so its saturation cannot consume shared capacity. Option B, colocate policy data, precompile schemas, route on the method and name headers rather than body inspection, warm connection pools, and reduce the exposed tool set. Option C, shed load tenant-fairly before overload collapses useful work, and report the shed calls rather than absorbing them silently.
- **Escalation Trigger**: Added-hop latency above 200 percent of its Step 1.1 budget at the 95th percentile for 15 consecutive minutes opens a capacity incident; optimising away identity, policy, approval, integrity, scanning, or audit is prohibited as a remedy.

**Error Type 5: Stale Authority Served From Cache or Snapshot**

- **Symptoms**: A revoked principal receives a cached result; a disabled tool remains visible in a list; an emergency denial does not reach every region; a failover restores a snapshot predating a revocation.
- **Diagnostic Steps**: Compare the revocation epoch on the served entry against the current epoch, and trace which of entitlement, policy, catalogue, definition, credential, approval, or kill-switch changes failed to increment it; verify convergence per region with a signed probe.
- **Resolution Protocol**: Option A, add the missing event to the epoch increment list and purge every store. Option B, shorten the freshness bound and switch the affected store to versioned keys so a missed invalidation degrades to a miss rather than to stale authority. Option C, disable caching for the affected class entirely until convergence is demonstrated across every region.
- **Escalation Trigger**: Any stale-cache measurement above 0 blocks release; a stale entry that served a side effect above read-only private escalates immediately to incident review and is never closed by purging alone.

**Error Type 6: Protocol Adaptation Weakens a Newer Revision**

- **Symptoms**: A modern downstream request is satisfied through a deprecated upstream feature; an adapter synthesizes a session identifier, a resumability guarantee, or a structured output the upstream did not provide; a downgrade below the configured security floor occurs to obtain a connection; a probe targets a removed method.
- **Diagnostic Steps**: Establish the speaking revision on both faces independently, then compare the capability set the downstream face advertises against what the upstream adapter can actually deliver, method by method.
- **Resolution Protocol**: Option A, declare the unsupported capability to the downstream caller rather than synthesizing it, and bind the declared fallback recorded at registration. Option B, isolate the legacy upstream behind a per-revision adapter with its own tests and its own lifecycle expiry date. Option C, retire the upstream where the semantics cannot be preserved; translation that has not been tested method by method is not equivalence.
- **Escalation Trigger**: Any downgrade below the configured security floor halts the connection and escalates; a synthesized guarantee is treated as a correctness defect and blocks release regardless of test results elsewhere.

**Troubleshooting Decision Tree**:

```
GATEWAY REQUEST FAILS OR BEHAVES UNEXPECTEDLY
├─ AUTHORITY DEFECT
│   ├─ Credential audience is the gateway → HALT; never forward; mint per principal
│   ├─ Granted scope exceeds intersection → Deny issuance; escalate to identity owner
│   └─ Actor or subject absent upstream → Block user-initiated work; switch to exchange
├─ ISOLATION DEFECT
│   ├─ Shared resource lacks a partition key → Disable the resource; add the key
│   ├─ Cache key omits principal or epoch → Reject the write; purge the store
│   └─ Unauthorized name in a list response → Tenant kill switch; block release
├─ INTEGRITY DEFECT
│   ├─ Observed hash differs from pinned hash → Block dispatch; quarantine; re-vet
│   ├─ Alias resolves to 0 or 2 or more entries → Reject; never fuzzy-match a route
│   └─ Tool claims system or gateway status → Poisoning finding; suspend the upstream
├─ AVAILABILITY DEFECT
│   ├─ One upstream saturates shared capacity → Per-upstream bulkhead and breaker
│   ├─ Added-hop latency above budget → Decompose by stage; never remove a control
│   └─ Dependency down with no declared behaviour → Fail closed; declare the behaviour
└─ REVISION DEFECT
    ├─ Probe targets a removed method → Replace with the current cheapest safe operation
    ├─ Adapter synthesizes an absent guarantee → Declare unsupported; bind the fallback
    └─ Downgrade below the security floor → HALT the connection; escalate
```

### D. Performance Metrics and Continuous Learning

**Security and Isolation Metrics**:

- **Credential attenuation violation rate**: Issued upstream credentials exceeding the computed intersection on audience, scope, tenant, actor, subject, or lifetime (target: 0; any occurrence halts issuance for that upstream).
- **Cross-tenant escape rate**: Adversarial calls exposing another tenant's tool, credential, state, cache entry, process, or result (target: 0; a non-zero value blocks release).
- **False-allow rate**: Labelled prohibited requests allowed or given an approval path contrary to policy (target: 0 for the critical cohort).
- **False-deny rate**: Labelled authorized requests incorrectly denied (target: at most 2 percent; a higher rate drives callers toward bypass).
- **Definition drift block rate**: Invocations blocked on a hash mismatch, over invocations against pinned tools (target: reported, not minimised; any non-zero value opens reconciliation).
- **Collision prevention rate**: Labelled collisions and confusables blocked before publication (target: 100 percent).

**Reliability and Cost Metrics**:

- **Gateway availability and end-to-end tool availability**: Reported as two separate figures, since the first can hold while the second fails (targets: the Step 1.1 required figure, and the deployment's stated task objective).
- **Added-hop latency**: Reported at the 50th, 95th, and 99th percentiles by cache state, policy path, scanner path, and region, never as an average of percentiles (target: within the Step 1.1 budget at the 95th percentile).
- **Retry amplification**: Upstream attempts over logical calls dispatched (target: at most 1.5; above 2.0 indicates stacked retry owners).
- **Unknown side-effect rate**: Write calls ending without an authoritative outcome (target: at most 0.5 percent).
- **Stale-cache rate**: Cached responses violating current freshness, authorization, definition, or revocation policy (target: 0).
- **Cost per verified successful task per tenant**: Total attributed model, context, gateway, policy, identity, network, sandbox, upstream, scanning, storage, and observability cost over verified successful tenant tasks (target: below the direct-client baseline at matched governance).

**Evidence and Response Metrics**:

- **Audit completeness rate**: Sampled logical calls carrying every required correlated event (target: at least 99 percent).
- **Catalogue convergence time**: Confirmed all-target convergence minus desired publication, reported separately for ordinary and emergency changes (targets: the Step 1.2 deadlines).
- **Kill-switch activation and full propagation time**: First confirmed enforcement, and last required confirmation across gateways, credentials, caches, and routes (targets: 60 seconds and the emergency deadline).

**Learning and Adaptation Mechanisms**:

- **Failure promotion**: Add every confirmed bypass, leak, drift, or stale-authority finding to a permanent regression fixture set, and rotate adversarial fixtures so that a passing suite does not become a memorised one.
- **Threshold recalibration**: Recompute latency budgets, retry bounds, breaker thresholds, and freshness bounds per upstream class against observed outcomes rather than reusing a fleet-wide default, and record the observation window behind each revision.
- **Warrant re-evaluation**: Re-run the Section 1.2 decision gate whenever caller count, tenant count, upstream count, or the highest reachable side-effect class changes materially, since a gateway warranted at one scale may be an unjustified concentration at another.
- **Staged release discipline**: Promote through synthetic traffic, shadow mode, read-only canary, reversible writes under approval, and separately approved higher authority, changing 1 major variable at a time and capping ordinary tuning at 5 iterations before revisiting architecture.

***

## IV. Domain-Agnostic Application Guidance

This framework generalises across sectors because it governs an intermediary's obligations rather than the content of any capability behind it. Its phases hold wherever several principals reach several capability providers through one mediated hop, credentials are held on their behalf, and the hop's failure would be felt by all of them.

### 4.1 Cross-Domain Application Patterns

**Regulated financial operations**: The warrant gate returns build because credential custody and correlated audit are contractual obligations rather than conveniences. Every upstream carrying a financial or security change side-effect class runs behind tenant-dedicated isolation, and no such tool is cacheable at any scope. Credential attenuation is the binding control: a workload credential may never stand in for a human principal, because the audit record must attribute a transfer to a person. The approval gate binds before every externally visible write, and the evidence stream is a deliverable to an examiner rather than a diagnostic aid.

**Clinical and health information systems**: Residency and minimum-necessary disclosure force regional or cell topology rather than one central instance, and the byte path stays local while desired state is distributed. Tool existence is itself sensitive, so caller-specific views must not reveal that a specialist service is integrated at all. Every read result inherits a private cache scope by default, and shareability across principals is declared only where a record is genuinely institution-wide. Redaction preserves schema shape, because a silently deleted field invites an unsafe inference from whatever consumes the result.

**Industrial and operational control**: Reversibility varies sharply within one estate: a sensor read is reversible and a setpoint change is not. Circuit breaking is per upstream and per tool rather than per server, because one expensive actuator failing must not withdraw the read-only telemetry an operator needs to diagnose it. The degraded-operation contract is the central artifact: it states which observations remain available when the control path is closed, and it fails closed for every write without exception. Deadlines are absolute and short, and load shedding is preferred to queueing because a stale command is worse than a refused one.

**Software engineering platforms**: Many agents share many providers, so per-agent configuration drift is the condition that justifies the gateway. Definition pinning carries most of the security weight here, because an upstream that changes a description can redirect what dozens of agents choose to call. Retrieval sits inside the eligible set and never outside it, since a repository an agent may not read must not surface in a search. Retry ownership is the common operational defect: platform clients, the gateway, and provider software each retry by default, and the amplification metric is what exposes it.

**Public-sector and cross-organisational service delivery**: Multiple organisations act as tenants of one intermediary they do not each control, so isolation must be demonstrable to a party outside the operator. Evidence integrity outranks evidence volume: append-only storage, separated writer and auditor roles, signed exports, and tested restoration matter more than field breadth. The warrant gate is re-run whenever a new organisation joins, because the blast radius grows with each one and a topology adequate for two tenants may be inadequate for ten.

### 4.2 Scale, Risk, and Tenancy Adaptation

- **Single-tenant, read-only estates**: Collapse Phase 4 to cache keying alone, retain Phases 1 through 3 and 5 through 6 in full, and permit shared connection pools. Added-hop latency above 10 percent of the task budget indicates the warrant gate should have returned refuse.
- **Multi-tenant estates with reversible writes**: Retain every phase. Mandate per-tenant credential encryption, per-tenant approval and idempotency records, and per-tenant adversarial fixtures in the release gate. Cache only read-only private results and only under a principal-bearing key.
- **Estates reaching destructive or arbitrary-execution capability**: Use tenant-dedicated cells, bind the approval gate before every dispatch in those classes, prohibit caching entirely, and require 2 independent human approvers for any authority broadening. Accept lower utilisation as the price of a bounded blast radius.
- **Latency-constrained deployments**: Shorten deadlines and warm pools rather than removing controls, route on the method and name headers rather than body inspection, and reduce the exposed tool set. Where the latency floor cannot accommodate policy evaluation, the warrant gate returns refuse and a direct client under the companion protocol guide is used instead.
- **Very large catalogues**: Where the eligible set routinely exceeds the direct-exposure threshold, add retrieval inside the eligible boundary under the companion retrieval guide, and report exposure reduction alongside selection quality so that a smaller prompt is not mistaken for a better one.
- **Federated or hierarchical estates**: Cap proxy depth at 2, preserve canonical origin through every hop, assign exactly 1 policy owner and 1 retry owner per decision, and prohibit token passthrough at every hop rather than only at the edge.

***

## V. Limitations and Considerations

**The gateway is a new single point of failure**: Introducing the intermediary makes every agent's tool access depend on a system that did not previously exist in the path, and its availability multiplies against every upstream's. The mitigation is the cost pricing in Step 1.1, which requires gateway availability to be stated numerically and to exceed the lowest acceptable end-to-end figure, together with the per-upstream bulkheads and breakers in Step 6.1 and the degraded-operation contract in Step 6.2.

**Credential custody concentrates what it protects**: Holding upstream credentials so that agents do not is the gateway's principal benefit and its principal risk, and no configuration removes the second while keeping the first. The mitigation is blast-radius capping in Step 1.2, per-tenant encryption and pinned issuers in Step 2.2, the attenuation intersection in Step 3.3, and the plane separation in Step 1.3 that denies runtime identities any publication permission.

**Per-principal authorization depends on identity the gateway did not establish**: The gateway authorizes against a principal that upstream infrastructure asserted, and a compromised or misconfigured caller-side identity path produces a correctly enforced decision about the wrong subject. The mitigation is the establishment-method requirement in Step 3.1, which halts a request carrying any identity dimension marked assumed, and the prohibition on accepting identity fields from a caller payload.

**Isolation is demonstrated by fixtures, not by design**: A partition key that looks correct in a configuration file proves nothing about the code path that reads it, and shared-resource leaks are found by adversarial testing rather than by review. The mitigation is the mandatory zero cross-tenant escape measurement in Checkpoint 4, which blocks release on any non-zero value, and the requirement that a shared supervised process carry a passing negative isolation test recorded against its version.

**Cacheability classification rests on upstream metadata**: The result cacheability fields the current revision defines are declared by the upstream, and an upstream that mislabels a personalised result as publicly cacheable would invite a shared intermediary to store it. The mitigation is the private-by-default rule in Step 4.3 for absent scope values, the side-effect class bypass above read-only private, and the principal-bearing cache key that makes a mislabelled entry unservable to a second principal even if it is stored.

**Protocol currency is a moving target**: Every protocol statement here is attributed to the `2026-07-28` revision and verified during conversion against the specification's own changelog; a later revision may remove a mechanism this guide relies on, exactly as that revision removed sessions, the initialization handshake, stream resumability, the liveness method, the log-level method, and the roots list-changed notification. The mitigation is the revision-attribution rule in Section 1.3 and the deprecation expiry recording it requires, which force a re-check rather than an assumption at each revision boundary.

**Numeric thresholds are deployment defaults, not measured findings**: The retry bound of 2 for interactive work, the breaker threshold of 50 percent over 20 attempts, the delegation depth of 3, the added-hop budget of 25 percent, the 60-second kill-switch activation, the 15-minute fail-open ceiling, and the 99 percent audit completeness floor were chosen to be operable on first deployment rather than derived from a measured property of gateways. The mitigation is the threshold recalibration requirement in Section III.D, obliging each deployment to recompute them per upstream class against observed outcomes and to record the observation window behind each revision.

**Vendor and vulnerability claims are transcribed, not re-verified**: The originating prose source surveyed named gateway products and cited specific vulnerability records against particular versions of them. Those citations are retained in Section VII as the source carried them, but the product survey was compressed out of the method because a domain-agnostic guide may not presuppose a named implementation, and neither the product capability claims nor the vulnerability identifiers were independently re-verified during this conversion. The mitigation is to treat Section VII's implementation entries as a starting point for procurement diligence rather than as current findings, and to confirm the exact release, transport, revision support, authorization model, and advisory status directly with each vendor before selection.

**Complete mediation is asserted more often than it is proven**: A gateway enforces nothing on a path that does not traverse it, and auxiliary listeners for loopback, administration, health, callbacks, inspection, and compatibility are the paths most often left unauthenticated. The mitigation is the enforcement path inventory in Step 1.3, which requires each listener to be enumerated with its authentication method, its policy evaluation point, and the test that proves it, and which halts deployment on any unauthenticated auxiliary listener.

**Structural conformance is not sound governance**: A gateway can satisfy every checkpoint here and still mediate a poorly chosen set of upstreams for a poorly justified purpose. The framework detects malformed mediation, not misdirected policy, and no checkpoint substitutes for human review of what the estate is for.

***

## VI. Conclusion and Summary

An MCP tool gateway is a governance decision before it is a piece of infrastructure. Its value comes from a small number of properties that a direct client cannot supply at fleet scale: one place where policy is evaluated, one place where upstream credentials live, one place where definitions are pinned, and one correlated evidence stream. Its cost is equally concrete: a new failure domain in every agent's path, an added hop in every request, and a concentration of credentials that converts many small exposures into one large one. A team that names the benefit it actually needs and prices the cost it is actually accepting will build a gateway worth having; a team that builds one because the pattern exists will have added a stall point and a blast radius in exchange for nothing.

The single property that separates a safe gateway from a dangerous one is where authority comes from. A gateway that holds credentials and authorizes against itself is a confused deputy operating at the scale of its entire estate, and no amount of logging, rate limiting, or scanning repairs that. A gateway that carries the calling principal across the hop, computes upstream authority as an intersection bounded by that principal's grant, and mints a narrow audience-bound credential for exactly one call has converted custody from a liability into the control it was meant to be. Everything else in this framework exists to keep that property true under load, under failure, under tenancy, and under a protocol revision that will change again.

**Key Success Factors**:

- **The warrant precedes the build**: The gateway is justified by a named requirement and a priced cost, and the decision gate is re-run whenever caller count, tenant count, or the highest reachable side-effect class changes.
- **Authority is per principal, never ambient**: Identity crosses the hop intact, upstream credentials are the intersection of user grant, agent grant, purpose, policy, and tool requirement, and a downstream credential is never forwarded upstream.
- **Isolation is keyed and tested**: Every shared pool, process, index, cache, and evidence store carries a partition key, and the cross-tenant escape measurement against adversarial fixtures is zero before release.
- **A cache hit supplies content, never authorization**: Every key carries principal or a declared shareability class, definition hash, policy version, and revocation epoch, and nothing above the read-only private side-effect class is cached at all.
- **The intermediary must not become the stall**: Deadlines are absolute and allocated, breakers and bulkheads are per upstream, degradation is declared before traffic, and no control is ever removed to recover latency.
- **The model tier owns nothing at the gateway**: Routing, authorization, credential custody, pinning, tenancy, cache keying, breakers, and the audit log are deterministic without exception, and an implementation that admits model judgement into any of them has given up the property that made the hop worth building.

By following this guide, AI agents can operate a shared tool intermediary that concentrates governance rather than risk, that fails predictably instead of silently, and that leaves evidence sufficient to reconstruct any route and any effect it carried.

***

## VII. References and Further Reading

This guide is an operational restructuring of a single prose source on production MCP tool gateways. The corpus pointers below identify that source and the sibling guides bearing on particular phases. The external references that follow are transcribed from the originating prose guide as it cited them; except where an entry is marked verified, they were not independently re-verified in the course of this conversion, and their titles and locations are reproduced rather than checked. Two entries were retrieved and confirmed during conversion and are marked accordingly; no reference below was added from any other source, and no bare label carried by the source has been expanded into a fuller title.

**Corpus pointers**:

- `Production MCP Tool Gateways for AI Agents` — the originating prose guide from which this operational guide was derived. Source of the two-face and six-plane model, the seven request bindings, the canonical record layers, the virtual server and caller-specific view design, the namespacing and alias discipline, the onboarding, health, drift, filtering, policy, approval, validation-repair and retry loops, the identity and token-exchange treatment, the cache inventory, the observability field inventory and metric formulas, the evaluation and release loop, and the readiness checklist. Its external citations are transcribed below.
- `advanced_task_guides/authoring/guide_guidewriting.md` — the normative house-style specification. Source of the archetype, the step slot template, the mandatory Implementation Guidance subsection names, and the conformance envelope this guide was written against.
- `advanced_task_guides/tool-use/guide_ModelContextProtocol.md` — the companion protocol guide and the boundary partner of this one. It owns the client-side integration machinery this guide deliberately does not restate: server admission and provenance verification, revision and capability negotiation with the declared-fallback rule, definition pinning and drift classification, per-server authority scoping, and the isolation of untrusted server-supplied content. Agents building a gateway must read it first and execute its procedures wherever a step here touches one upstream.
- `advanced_task_guides/tool-use/guide_ToolUseAndFunctionCalling.md` — the companion tool-use guide. Source of the side-effect class vocabulary, the calling-principal and confused-deputy definitions, the outcome and error class vocabularies, the idempotency and reconciliation discipline, the bounded validation-repair loop, and the trust class and isolation mechanism adopted in Phase 5.
- `advanced_task_guides/tool-use/guide_AgentControlPlane.md` — the companion control-plane guide covering fleet-wide governance across capability types. Source of the authority scope, execution grant, budget ledger, default-deny posture, disclosure boundary, and reconciliation terminology used here. The gateway is one inline enforcement point under that broader authority and should consume signed desired state from it rather than becoming a second source of organisation-wide truth.
- `advanced_task_guides/tool-use/guide_ToolRetrieval.md` — companion guidance on retrieval algorithms, index construction, and recall measurement, applicable wherever Step 3.2 exposes a bounded subset of a large eligible set. The gateway owns eligibility and enforcement; that guide owns ranking, and a ranking score is never an authorization.
- `advanced_task_guides/tool-use/guide_CodeExecution.md` — companion guidance on bounded execution of untrusted generated code, applicable to the sandboxing and egress requirements for supervised local upstreams in Step 4.1 and to any deployment permitting programmatic multi-tool workflows behind the gateway.
- `advanced_task_guides/tool-use/guide_CodeAsAction.md` — companion guidance on the programmatic multi-tool workflows named above, in which the model emits one program calling many capabilities through a frozen binding namespace rather than one flat call per step. Every operation such a program issues arrives at this hop as an individually keyed logical call, so the gateway sees no program and enforces per operation exactly as it does for a flat caller. A typed policy denial returned here is terminal for that program rather than a prompt for a variant.
- `advanced_task_guides/tool-use/guide_AgentSkills.md` — companion guidance on governed capability libraries under progressive disclosure and bounded authority, applicable to the exposure economics in Step 3.2 where catalogue size rather than authorization is the binding constraint.
- `advanced_task_guides/tool-use/guide_ComputerUse.md` — companion guidance on an agent capability class whose side effects are externally visible and difficult to reverse, applicable when such a capability is registered as an upstream and requires the tenant-dedicated treatment described in Section 4.2.

**External references**: Entries 3 and 5 were retrieved and confirmed during this conversion, and the protocol statements attributed to the `2026-07-28` revision in Sections 1.3, 4.3 and V rest on them. Every other entry is transcribed from the originating prose guide as that guide carried it, including short labels, which are reproduced rather than expanded.

*Protocol specification and authorization standards*

1. Model Context Protocol, *MCP 2026-07-28 announcement* — https://blog.modelcontextprotocol.io/posts/2026-07-28/
2. Model Context Protocol, *versioning specification* — https://modelcontextprotocol.io/specification/2026-07-28/basic/versioning
3. Model Context Protocol, *MCP 2026-07-28 changelog* — https://modelcontextprotocol.io/specification/2026-07-28/changelog (verified during conversion; source of the removal, deprecation, feature-lifecycle, request-header and result-cacheability statements in Section 1.3)
4. Model Context Protocol, *MCP tools specification* — https://modelcontextprotocol.io/specification/2026-07-28/server/tools
5. Model Context Protocol, *MCP authorization* — https://modelcontextprotocol.io/specification/2026-07-28/basic/authorization (verified during conversion; source of the audience-validation and token-transit prohibitions in Step 3.3)
6. Model Context Protocol, *MCP security best practices* — https://modelcontextprotocol.io/docs/2026-07-28/tutorials/security/security_best_practices
7. IETF, *RFC 8707* — https://www.rfc-editor.org/rfc/rfc8707.html
8. IETF, *RFC 8693* — https://www.rfc-editor.org/rfc/rfc8693.html
9. IETF, *RFC 9728* — https://www.rfc-editor.org/rfc/rfc9728.html

*Security guidance and vulnerability records*

10. OWASP, *MCP Security Cheat Sheet* — https://cheatsheetseries.owasp.org/cheatsheets/MCP_Security_Cheat_Sheet.html
11. OWASP, *LLM Top 10* — https://genai.owasp.org/llm-top-10/
12. GitHub Advisory Database, *CVE-2025-49596* — https://github.com/advisories/GHSA-7f8r-222p-6f5g
13. NVD, *CVE-2025-6514* — https://nvd.nist.gov/vuln/detail/CVE-2025-6514
14. NVD, *CVE-2025-64443* — https://nvd.nist.gov/vuln/detail/CVE-2025-64443
15. NVD, *CVE-2026-14471* — https://nvd.nist.gov/vuln/detail/CVE-2026-14471
16. NVD, *CVE-2026-53818* — https://nvd.nist.gov/vuln/detail/CVE-2026-53818
17. NVD, *CVE-2026-77822* — https://nvd.nist.gov/vuln/detail/CVE-2026-77822

*Observability conventions*

18. OpenTelemetry, *MCP attributes* — https://opentelemetry.io/docs/specs/semconv/registry/attributes/mcp/
19. OpenTelemetry, *GenAI attributes* — https://opentelemetry.io/docs/specs/semconv/registry/attributes/gen-ai/

*Gateway implementations surveyed by the prose source*

The prose source surveyed these implementations by name and version. The survey was compressed out of the method in this conversion, because a domain-agnostic guide may not presuppose a named product, and neither the capability claims nor the version-specific security findings were re-verified here. Treat these as starting points for procurement diligence rather than as current findings.

20. IBM, *ContextForge* — https://github.com/IBM/mcp-context-forge
21. IBM, *ContextForge documentation* — https://ibm.github.io/mcp-context-forge/
22. IBM, *ContextForge releases* — https://github.com/IBM/mcp-context-forge/releases
23. Docker, *Docker MCP Gateway* — https://docs.docker.com/ai/mcp-catalog-and-toolkit/mcp-gateway/
24. Docker, *Docker MCP Gateway repository* — https://github.com/docker/mcp-gateway
25. Docker, *Docker MCP Catalog* — https://docs.docker.com/ai/mcp-catalog-and-toolkit/catalog/
26. Microsoft, *Azure API Management MCP support* — https://learn.microsoft.com/en-us/azure/api-management/mcp-server-overview
27. Microsoft, *Azure existing-server limitations* — https://learn.microsoft.com/en-us/azure/api-management/expose-existing-mcp-server
28. Microsoft, *Azure API Center* — https://learn.microsoft.com/en-us/azure/api-center/register-discover-mcp-server
29. Microsoft, *Azure MCP Center* — https://github.com/Azure/mcp-center
30. Amazon Web Services, *Amazon Bedrock AgentCore Gateway* — https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/gateway.html
31. Amazon Web Services, *AgentCore MCP targets* — https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/gateway-targets-mcp.html
32. Amazon Web Services, *AgentCore semantic tool search* — https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/gateway-using-mcp-semantic-search.html
33. Cloudflare, *Cloudflare MCP server portals* — https://developers.cloudflare.com/cloudflare-one/access-controls/ai-controls/mcp-portals/
34. Cloudflare, *Cloudflare MCP governance* — https://developers.cloudflare.com/agents/model-context-protocol/protocol/governance/
35. Kong, *Kong MCP Traffic Gateway* — https://developer.konghq.com/ai-gateway/mcp/
36. Kong, *Kong MCP OAuth* — https://developer.konghq.com/plugins/ai-mcp-oauth2/
37. Envoy, *Envoy AI Gateway MCP support* — https://aigateway.envoyproxy.io/docs/0.5/capabilities/mcp/
38. agentgateway, *agentgateway* — https://agentgateway.dev/docs/standalone/main/mcp/
39. agentgateway, *agentgateway multiplexing* — https://agentgateway.dev/docs/local/latest/tutorials/multiplex/
40. Lasso Security, *Lasso MCP Gateway* — https://github.com/lasso-security/mcp-gateway
41. LiteLLM, *LiteLLM MCP Gateway* — https://docs.litellm.ai/docs/mcp

*Evaluation suites and tool-use research*

42. *MCP-Universe* — https://arxiv.org/abs/2508.14704
43. *MCP-RADAR* — https://arxiv.org/abs/2505.16700
44. *MCPAgentBench* — https://arxiv.org/abs/2512.24565
45. *MCPMark* — https://github.com/eval-sys/mcpmark
46. *MCPTox* — https://arxiv.org/abs/2508.14925
47. *BFCL* — https://proceedings.mlr.press/v267/patil25a.html
48. *ToolSandbox* — https://arxiv.org/abs/2408.04682
49. *τ-bench* — https://arxiv.org/abs/2406.12045

*Adjacent execution pattern*

50. Anthropic, *code execution with MCP* — https://www.anthropic.com/engineering/code-execution-with-mcp
