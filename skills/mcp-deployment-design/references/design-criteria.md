---
created: "2026-11-05T00:17:40Z"
updated: "2026-11-05T00:25:30Z"
---

# MCP deployment design criteria

## 1. Fit: MCP, direct client or gateway

Use MCP when at least one holds:
- Several hosts or agents need one protocol to discover and invoke the same capabilities.
- A server must expose tools, resources or prompts without coupling to one model provider.
- A local capability should run as a separately supervised process outside the model host.
- A remote service needs a standard, versioned agent-facing interface with capability discovery.
- Independent teams own the host and the server.
- A gateway must aggregate, filter, authorize and observe capabilities from many backends.

Do not use MCP when:
- One application already has a stable local function and interoperability adds only overhead (use plain function calling or the framework's native tools).
- A plain REST, gRPC, database or message API is consumed only by deterministic code (an OpenAPI wrapper of narrow, reviewed operations may fit; never expose a whole OpenAPI surface automatically).
- Server origin, package integrity, transport security or ownership cannot be verified.
- The only available server demands broad credentials, arbitrary filesystem access, unrestricted egress or global admin authority.
- A side effect cannot be authorized, previewed, reconciled or audited.
- A server exposes a huge, mutable catalog with no filtering or change control.
- An independent agent should own planning and a durable task lifecycle (use an agent-to-agent delegation protocol such as A2A).

Use a gateway when at least one holds:
- Several agents, clients, teams or tenants need a stable MCP endpoint over independently deployed servers.
- Central authentication, per-tool authorization, argument policy, approvals, quotas, DLP, egress control or audit must apply consistently.
- Upstreams use mixed transports, versions, credentials or operating standards.
- Definitions must be curated, namespaced, renamed, pinned, withdrawn or exposed differently by principal and task.
- The eligible catalog is too large to expose fully.
- Operators need one place to watch health, open breakers, attribute cost, revoke access and quarantine poisoned definitions.
- Agents must never hold upstream secrets or broad third-party tokens.
- Remote clients cannot safely launch local stdio servers.
- Multi-tenant, compliance or incident-response needs demand complete mediation and correlated evidence.

Use a direct MCP client instead when a single user connects to one or two trusted, pinned, read-only local servers, no central governance, shared identity, transport conversion or audit is needed, and an in-process client can enforce the same controls. Keep server identity, definition hashes and typed validation so a later gateway needs no redesign.

Do not use a gateway to hide an unbounded autonomous agent behind one tool, to make an unsafe server trustworthy, to replace downstream authorization, or to turn semantic similarity into permission. Do not build one global gateway that holds every credential and executes every tool.

## 2. Gateway topology

| Topology | Use when |
|---|---|
| Centralized cluster | One trust domain and region; simplicity and consistent policy outweigh correlated-outage risk. Deploy across failure zones with external stores and per-upstream bulkheads. |
| Regional gateways with global desired state | Latency, availability or data residency needs local data paths. Keep token exchange, secrets, audit and result data in allowed regions; emergency denies travel on a faster independent channel. |
| Tenant-dedicated gateways or cells | High-assurance isolation, very large tenants, or mutually untrusted credential sets. Separate keys, processes, pools, caches, queues, indexes and evidence. Costs lower utilization and more operations. |
| Sidecar or node-local gateways | Local stdio servers, low latency or host-level egress control matter. Do not give a sidecar cluster-wide secrets. |
| Hierarchical gateways | Only when regional or domain aggregation is unavoidable. Preserve canonical origin through every hop, cap proxy depth, one policy and retry owner per decision, no token passthrough. |

Separate the gateway runtime from management APIs: runtime instances read signed immutable snapshots and cannot publish catalog or policy changes; management writers hold no runtime upstream credentials. The model never operates emergency controls.

## 3. Protocol revisions and transports (as of September 2026)

Version identifiers are dates (YYYY-MM-DD) and change on backward-incompatible changes. Pin supported revisions in code and tests; do not compare date strings to infer features.

- 2024-11-05: two-endpoint HTTP+SSE transport, early stateful model.
- 2025-03-26: Streamable HTTP replaces HTTP+SSE; tool annotations added.
- 2025-06-18: JSON-RPC batching removed; structured tool output, resource links and elicitation added; protocol-version header required for HTTP; MCP server as OAuth resource server with RFC 8707 resource indicators.
- 2025-11-25: refined authorization and client registration; keeps stateful initialization.
- 2026-07-28: stateless core; no protocol sessions or Mcp-Session-Id; no initialization handshake or standalone GET stream; mandatory server/discover; version and capabilities in each request's metadata; Multi Round-Trip Requests (MRTR) replace server-initiated client requests; subscriptions/listen replaces old subscription flows; Mcp-Method and Mcp-Name headers let a gateway route and meter without body inspection.

Rules:
- Current servers: call server/discover first, pick the newest mutually supported, policy-approved revision, and send it in every request. If the server rejects the version, retry once with the highest allowed intersection. Never downgrade below the configured security floor.
- Legacy servers: initialize, then notifications/initialized, before ordinary requests. Isolate legacy behaviour behind a compatibility adapter; do not mix session IDs and server-initiated requests with stateless assumptions in one path.
- A gateway may expose a modern downstream facade over a legacy upstream adapter, but must keep upstream session state, map cancellation and errors, declare unsupported capabilities, and not invent list determinism, resumption, idempotency, structured output or authorization semantics.
- Routing: stateless round-robin for current traffic; for legacy session upstreams, a session-aware pool or shard keyed by tenant, principal, upstream and real session ID. Do not force modern traffic into a global sticky-session store.
- stdio: for local, single-host use of a pinned server process the host launches on purpose. Supervise it; never launch a registry-supplied command string without package verification and sandboxing.
- Streamable HTTP: for remote, horizontally scaled services, behind TLS, authentication, request-size and rate limits, health checks and graceful drain.
- Legacy HTTP+SSE: only for an existing server that cannot yet migrate, behind an adapter with a retirement date. Do not build new deployments on it.
- Choose local or remote by trust and operations, not latency alone.
- Pin SDK major versions.

## 4. Server inventory and risk classes

Server table columns: Server, Transport, Revision, Risk class, Namespace.

Risk classes: public read, private read, reversible write, external communication, financial or security change, destructive action, arbitrary execution, untrusted content source.

Each server record holds an immutable server ID unrelated to display name, owner, publisher, package or image digest, endpoint origin, transports and revisions, enabled primitives, required egress, authorization issuer, trust tier, tenant boundary, lifecycle state and kill-switch scope. An owner or data handling the user did not give reads not stated and goes to Open items; that alone does not exclude the server from the design (a no-use condition of section 1 excludes a server only when the material shows the condition holds), but the server is not provisioned until its ownership and data handling are confirmed.

## 5. Catalog and exposure

- Namespace every tool by verified server identity. The route key holds gateway namespace, upstream server ID, upstream tool ID and version. Keep a reversible alias map; never route by fuzzy name, embedding similarity or last-registered-wins.
- Normalize Unicode; reject control and invisible characters, homoglyphs, case-folded collisions and names that impersonate gateway meta-tools. On collision keep distinct namespaces or reject the newer registration.
- Keep three definitions, each hashed: source (what the upstream advertised), canonical (normalized, used for policy) and client projection (what one client class sees). Policy binds to canonical identity and source hash. A rename or rewrite never changes authority and never hides side effects, scopes, limits or negative-use guidance.
- Hash complete definitions (description, schema, annotations, metadata). A changed hash triggers review even when the server version is unchanged; a material change of scope, destination, effect, identity or provenance quarantines the tool and re-enters vetting, and earlier approval does not transfer.
- Compose catalogs from approved snapshots and publish each catalog version atomically; keep the prior snapshot for rollback.
- Virtual servers or per-client views: the effective view is the intersection of membership, tenant and principal, agent allowlist, purpose, environment, region, protocol compatibility, health, lifecycle, entitlement, data class, risk ceiling, approval availability, quota and emergency denies. Return only authorized names and counts. Do not let a model choose its view.
- Exposure: pass all definitions directly only when the catalog is small, stable, policy-homogeneous and harmless to selection quality and cost; otherwise filter deterministically by policy first, then retrieve, and expose ordinarily 5 to 10 tools. Retrieval score is never authorization. Do not defer a tool every task needs or hide a mandatory safety tool.
- Retrieval loop bounds: a direct client broadens once and exits unavailable after two retrieval rounds; a gateway stops after two rewrites or three retrieval rounds.
- Vetting a new server, version, owner or definition: isolated environment with no production secrets and deny-by-default egress; enumerate every primitive; compare declared annotations, scopes and destinations with observed behaviour; allow one owner evidence revision; cap automated vetting at two full runs; route ambiguity to a human and never widen permissions to pass tests.
- Tool annotations (readOnlyHint, destructiveHint and the like) are advisory, not policy facts.

## 6. Identity and tokens

- For HTTP, the MCP server is an OAuth resource server; a separate authorization server issues tokens. Use Protected Resource Metadata (RFC 9728), authorization-server discovery, authorization code with PKCE, exact redirect URIs, random state and the RFC 8707 resource indicator.
- Validate discovered metadata URLs, issuer relationships, HTTPS and redirects against SSRF policy before fetching; pin accepted issuers per upstream.
- Prefer preregistration or Client ID Metadata Documents; use Dynamic Client Registration only with policy, quotas and lifecycle controls.
- The server validates signature, issuer, audience, expiry, not-before, scopes and tenant on every request.
- No token passthrough: never forward a downstream token upstream or accept a token meant for another resource. The gateway validates the downstream token, decides policy, then obtains a separate upstream credential whose audience is the exact upstream and whose authority is no broader than the intersection of user grant, agent grant, task purpose, gateway policy and tool requirement.
- Use OAuth 2.0 Token Exchange (RFC 8693) where the identity provider supports constrained on-behalf-of delegation; it does not guarantee attenuation, so enforce scope, audience, tenant, actor, subject, delegation depth and lifetime. Without it, use a per-user upstream grant, or a narrow workload credential only for service-owned operations.
- Per-user identity when visibility, side effects, audit ownership or consent depends on the human; workload identity only for service-owned tasks. When both apply, record actor and subject separately. Never impersonate a human with a shared service account or use one global admin token.
- A proxy using one static upstream OAuth client needs per-client consent bound to user, downstream client, upstream resource, scopes, purpose and expiry.
- Tokens stay out of prompts, arguments, results, URLs, logs and model memory; encrypt token stores per tenant, serialize refresh, revoke on disablement. Catalog records hold credential references only.
- Tenant and user come from validated identity, never from model arguments.

## 7. Policy and approvals

- Apply policy twice: to disclosure and again to invocation.
- Per-tool policy for stable capability access; per-argument policy for recipients, account or tenant IDs, paths, URLs, queries, amounts, batch size, export format, destinations and permission changes. Downstream services still authorize their own resources.
- Decision effects: allow, deny, require approval, or allow with constraints. Approval satisfies a precondition; it cannot override a denial.
- Fresh human approval before: sending or disclosing data to a new destination; spending money, ordering, signing or changing a price; deleting, overwriting or bulk-moving data; changing identities, permissions, security controls, production infrastructure or network policy; giving a server a new scope, secret, root, mount, egress destination or sampling capability; installing an unreviewed server or accepting a changed definition hash; continuing after a security signal or retrying an unknown write.
- Bind approval to principal, client, agent, canonical tool, source definition hash, arguments, destination, data released, scopes, expected effect, policy version and expiry; re-check everything just before dispatch. Do not ask a human to approve an opaque server, all tools at once or thousands of actions.
- Writes carry an idempotency key, are reconciled when the outcome is unknown, and are never retried blindly.

## 8. Readiness questions

Deployment is ready only when every applicable answer is yes. If any answer is no, keep the affected server, tool, tenant, region, transport, revision, data class or write capability disabled or read-only until the control exists.

- Is every server necessary, owned, allowlisted, pinned and independently revocable, with provenance and vulnerability state verified?
- Are supported revisions, the security floor and legacy adapter boundaries explicit and tested?
- Are only needed primitives enabled (tools, resources, prompts, sampling, roots, elicitation, MRTR, subscriptions)?
- Are complete definitions hashed, namespaced, reviewed and blocked on drift, with collisions and confusables rejected?
- Is every execution path mediated, including loopback, inspector, callback, health and admin listeners?
- Are downstream and upstream tokens distinct, audience-bound, short-lived, revocable and absent from model context?
- Are token passthrough, confused deputy, SSRF and cross-tenant leakage tested?
- Are local and untrusted servers sandboxed with minimal mounts, no host secrets and deny-by-default egress?
- Are consequential actions bound to exact, fresh approval, and writes idempotent or reconcilable?
- Are pools, caches, handles, indexes and logs partitioned by tenant?
- Are discovery, pagination, retrieval, repair, approval, retry and reconnection loops bounded?
- Are kill switches, token revocation, cache invalidation and rollback tested?
- Launch order: pinned read-only servers for an allowlisted cohort first; add private data, client primitives and writes in separate gates.
