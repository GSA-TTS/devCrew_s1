---
created: "2026-11-05T00:17:47Z"
updated: "2026-11-05T00:17:47Z"
---

# MCP threats and controls

Threat table columns: Threat, Control, Status, Evidence. Each row below gives the Threat and the controls to look for or recommend.

## Core rows (every deployment)

| Threat | Control |
|---|---|
| Tool poisoning: descriptions, schemas, prompts, annotations or results hide instructions that steer selection, leak data or call other tools | Treat all upstream metadata as untrusted; normalize and bound fields; reject instructions about policy, secrets, other tools, system prompts or unrelated destinations; keep metadata out of system instructions. |
| Rug pull and definition drift: an approved definition changes after review | Hash complete definitions at onboarding, publication, disclosure, approval, dispatch, retry and refresh; use semantic diffs as well as hashes; a mismatch blocks invocation; do not accept an upstream's claim that a change is cosmetic. |
| Cross-server shadowing: one server's names or descriptions impersonate or influence another's tool | Namespace by verified origin; block collisions, homoglyphs and reserved names (required, system, gateway, security override); do not let low-trust metadata influence high-impact tools across servers. |
| Indirect prompt injection in resources, results, logs, errors and links | Treat that content as hostile data; validate output schema and provenance before model exposure; scan output for injection, links and secrets (scanners are signals, not authority); quarantine high-risk results on detector failure. |
| Malicious or typosquatted server, package, image or update | Allowlist server identity, publisher, digest and endpoint; verify signature or provenance, SBOM and vulnerability state; resolve package commands in an isolated build and promote a digest-pinned artifact; never let a model choose package name, version, flags or environment. |
| Credential theft by a local process or remote server | Sandbox local servers non-root with minimal read-only mounts; strip inherited environment, descriptors, home directories, SSH agents, cloud credentials and sockets; tokens never in prompts, arguments, results or logs. |
| Command injection and remote code execution | No generic shell, SQL or URL-fetch tool where a narrow one suffices; strict input schemas; sandbox with process and resource limits; test every alternate, loopback, admin, health and callback path. |
| Confused deputy and token passthrough | Separate downstream and upstream authentication; audience-bound upstream credentials no broader than the user and agent grants; per-client consent for a static upstream OAuth client; actor and subject kept distinct. |
| SSRF and redirect abuse via OAuth metadata, resource links, endpoints or redirects | Validate DNS, IP ranges, redirects, ports and HTTPS before fetching; route remote egress through a validating proxy; block private ranges and cloud metadata. |
| Excessive agency from broad tools, scopes, auto-approval or opaque code orchestration | Least-privilege scopes; split read from write and preview from commit; exact fresh approval for high-impact actions; code-mediated MCP only for read-heavy work with every call still mediated. |
| Resource abuse: unbounded pagination, progress floods, large results, nested MRTR, expensive tools | Page, item, byte, stream, MRTR, time, token, cost and concurrency budgets; bounded loops; quotas, circuit breakers and bulkheads. |
| Cross-tenant leakage through pools, caches, processes, tokens, logs, subscriptions or state handles | Partition credentials, caches, handles, pools, indexes and logs by tenant; key caches by identity, protocol, definition, tenant and authorization; no local server process shared across mutually untrusted tenants unless built and tested for it. |

## Gateway rows (add when the decision is a gateway)

| Threat | Control |
|---|---|
| Bypass and forgery: a client, model or compromised agent skips the gateway, forges identity, selects hidden tools or replays approvals | Complete mediation (model workers cannot reach upstreams, launch local servers or read gateway secrets); deny-by-default disclosure and invocation policy; approvals bound to an operation hash and re-checked after approval. |
| Control-plane compromise: a management account, registry, policy bundle, secret manager, gateway image or build pipeline affects many agents | Runtime separated from management; signed immutable snapshots; dual control for authority broadening; append-only attributable audit. |
| Stale authority: failover, stale snapshots, clock skew or region partition restores revoked authority | Synchronous revocation; emergency denies on a fast independent channel; caches never bypass kill switches; scoped kill switches that also revoke credentials and invalidate caches. |
