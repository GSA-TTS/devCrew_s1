---
created: "2026-11-05T00:14:24Z"
updated: "2026-11-05T00:24:31Z"
---

# Control areas for an agent that executes generated code

Each numbered area is one row of the Controls table. Every area gives three fields:

- Recommendation: the default to propose in a new design, and the standard an existing design is measured against.
- Gap when: what in a design makes the row's Status Gap.
- Reason: the threat or failure the control addresses.

Areas 1 to 11 apply to every mode that executes generated code. Areas 12 to 16 apply only to code as action, where bound tools are callable from inside the program.

## 1. Action contract

- Recommendation: before any code is generated, state the intended result, acceptance criteria, required evidence, prohibited effects, maximum authority and budgets. Generated source is data until approved for one runtime, language, dependency set and capability profile. For code as action, also fix the entrypoint, the output envelope, the allowed capabilities and the stop condition, and have the program return a small structured result plus evidence references an independent verifier can check.
- Gap when: the design gives no acceptance criteria or prohibited effects; the model decides on its own what counts as done; the program's last printed line is treated as the result.
- Reason: independent acceptance criteria, not the model's claim, decide whether the requested task is complete.

## 2. Isolation boundary and runtime profile

- Recommendation: choose a named, versioned execution profile before generating code. It fixes language and version, base-image digest, isolation tier, writable paths, mounted inputs, egress class, secret capability, package policy, and CPU, memory, process, disk, time, output and concurrency limits. The agent may request a profile by capability; deterministic policy picks the actual profile and may deny or downgrade it. Pick the boundary by threat:
  - Trusted code over non-sensitive inputs: a non-root container with seccomp, capabilities dropped, read-only mounts, quotas and no egress may be sufficient.
  - Model-generated or user-supplied native code in a multi-tenant service: a separate kernel boundary (a microVM such as Firecracker, or a Kata VM) or a carefully assessed user-space kernel such as gVisor; not namespaces alone.
  - A narrow portable computation that fits WebAssembly: WASI, which starts with no ambient filesystem or network authority; still bound fuel or instruction count, memory, wall time, output and host-call frequency, and validate every host function.
  - Browser-local analysis: Pyodide in a dedicated worker or isolated frame, with no access to DOM, cookies, local storage, origin credentials or unrestricted fetch, a content-security policy and a termination path. This is client-side isolation, not a server security boundary.
  - A restricted interpreter (code as action): allow only the constructs composition needs (literals, variables, bounded collections, pure functions, loops with counters, conditionals, exception handling, bound-tool calls), start with no imports and a minimal builtin set, and still execute it inside a sandbox.
  Layer seccomp, Landlock, AppArmor or SELinux, dropped capabilities, no_new_privs and a non-root user, and never mount the container runtime socket. Keep mutually untrusted tenants out of the same guest unless the chosen technology's threat model supports it. Separate the model worker from the execution plane; the model receives no runtime-administrator credentials. The technology mechanics above are general ones; for a product the user names, confirm the current mechanics in its official documentation (at most two searches) or list them in Open items as to be confirmed.
- Gap when: generated code executes on the model or application host; a container, notebook kernel, browser worker, import restriction or a provider's sandbox label is treated as the whole boundary; one technology is the default with no threat model; the choice rests on cold-start figures without a benchmark of the exact code, host and image; a default Docker profile is treated as a complete threat model.
- Reason: assume generated code attempts sandbox or kernel escape, host and cross-tenant discovery, cryptomining, scanning and abuse of paid APIs.

## 3. Network and DNS egress

- Recommendation: deny all network access by default, DNS included. When a task needs a dependency, data source or API, prefer a brokered tool outside the sandbox that enforces user authorization, response size, redaction, rate limits and destination policy. When direct egress is necessary: an authenticated egress proxy; an exact allowlist of schemes, hostnames, ports and methods; a controlled resolver; blocked private, loopback, link-local, metadata-service and control-plane ranges; validation of every resolution and redirect; byte, request, connection and time budgets; no generic UDP, raw sockets, inbound listeners or arbitrary tunnels; logging of destination class and byte counts without credentials or payloads.
- Gap when: egress is unrestricted; egress is opened so code can install packages; an allowlisted domain accepts attacker-controlled paths or uploads; in-browser execution is said to prevent exfiltration while the page can send network requests.
- Reason: prompt-injection-driven exfiltration through HTTP, DNS, redirects, error reports, package lookups, filenames, timing or oversized model-visible output.

## 4. Secrets and credentials

- Recommendation: no secrets in the execution environment; expose narrow operations as brokered tools with user-bound authorization. If code must use a secret, issue a short-lived, audience-bound credential for one destination and operation, deliver it through a channel the model cannot see, and revoke it at task end. For code as action, the runtime holds only a short-lived capability token for the gateway; an identity broker obtains a user- or workload-scoped downstream credential for each call, and code never selects scopes, audiences, tenant, role or credential source. Revoke every credential the environment could reach on an escape or suspicious egress attempt.
- Gap when: a secret sits in a prompt, source, command argument, inherited environment variable, notebook, log, crash dump, snapshot or artifact; a binding stub holds a downstream credential.
- Reason: secret theft from environment variables, command history, process tables, crash dumps, mounted configuration, cloud metadata or inherited file descriptors.

## 5. Filesystem and artifact export

- Recommendation: mount inputs read-only in a task-specific path, with a small writable working directory and a separate export directory; for pure tool composition, prefer no filesystem. Canonicalize every path after resolving links; block traversal, link escapes, special files, device nodes and setuid bits; bound archive expansion ratio, depth, file count, bytes, path length and inodes. Export only files declared in the result manifest, recording type detected from bytes, size, hash, creating execution and scan result; reject or quarantine unexpected executables, macro-enabled documents, HTML with active content and archives.
- Gap when: the host root, home directories, source-control or cloud credentials, SSH agents, Docker or Kubernetes sockets, unrelated repositories or shared temporary directories are mounted; every file the sandbox created is exported; safety is inferred from a file extension.
- Reason: path escapes, decompression bombs, disk and inode fill, and malicious artifacts reaching users.

## 6. Dependencies

- Recommendation: dependency-free code or a fixed, prebuilt image. Otherwise resolve before code generation from an allowlisted, immutable internal mirror by exact name, version, platform and digest; reject ranges, latest, mutable branches and unpinned URLs; check the approved catalog before the model uses a package; keep install scripts and source builds off unless a reviewed profile allows them; scan direct and transitive dependencies for malware, vulnerabilities, license and provenance; tie an SBOM to the environment digest. The dependency-resolution loop enters only for a missing dependency the accepted task needs and allows at most two automated attempts (one correction of an exact known name or version, then one policy-approved alternative); a new package, source build, unsigned artifact, registry mismatch or unresolved vulnerability exits to human review.
- Gap when: generated code runs a package manager against a public registry; a model-invented package is installed; a package-not-found result leads to a wider search or dropped version constraints; repeated import errors widen network access.
- Reason: slopsquatting on hallucinated names, typosquatting, dependency confusion, install-time scripts and compromised registries.

## 7. State and session lifecycle

- Recommendation: one disposable environment per task and a fresh process per repair; any reuse is explicit. Reuse only when principal, tenant, task, data classification, runtime profile, dependency set and policy version (and, for code as action, the binding manifest) are unchanged, after checking that no unexpected processes, listeners, modified startup files, credentials or undeclared artifacts remain. Never reuse across tenants. Prefer checkpointing approved files and rebuilding a clean runtime over snapshotting live memory, and keep durable state outside the sandbox. If persistent variables are enabled, only explicitly promoted values survive, and credentials, approval tokens, gateway clients, open sockets, live iterators and unbounded objects never persist. Do not persist state for adversarial inputs, cross-user work, side effects with unknown outcomes, regulated data without a retention basis, or reproducibility-critical execution.
- Gap when: a warm kernel or pool is shared across tenants; live memory snapshots are reused without the reuse check; a process exit is trusted to have cleaned up state.
- Reason: persistence through startup files, package caches, long-lived child processes and contaminated warm pools; cross-tenant leakage; snapshots that hold plaintext data and secrets.

## 8. Resource, output and cost limits

- Recommendation: enforce CPU, memory, process and thread, file-descriptor, disk and inode limits, wall and idle timeouts and output caps outside the guest, plus, for code as action, tool-call, page, concurrency, token and money limits; apply admission and concurrency limits; add language-level iteration counters only as defense in depth. Stream bounded standard output and standard error to separate sinks, keep the beginning and end when truncating and record discarded byte counts. Keep kill switches, and make cancellation stop descendants, network connections and child calls.
- Gap when: limits are enforced only inside the guest or interpreter; unlimited output or raw datasets return to the model; there is no reliable cancellation.
- Reason: infinite loops, fork bombs, memory and disk fill, expensive regular expressions, massive output and denial of wallet; a loop of individually valid tool calls can still exhaust an API or a budget.

## 9. Human approvals

- Recommendation: require fresh approval before code may reach network beyond an approved read-only destination, introduce a new dependency, receive a secret or delegated credential, alter production systems, identities, access grants or security controls, send, publish, upload or transfer data, execute an unsigned binary or weaken isolation, or continue after a security warning, unknown side effect or verification conflict. Show the exact purpose, destination, data disclosed, dependency and version, credential scope, side effect, reversibility and expiry, and bind the approval to hashes of source, inputs, dependency lock, profile, destination and intended action; any change requires re-approval. For code as action, approval happens at the gateway for the nested call, the runtime never sees approval credentials, a denial is typed and non-retryable, and at most one re-presentation follows an explicit user-requested correction; the approval loop exits on approval, denial, expiry, cancellation or policy failure.
- Gap when: approving a program is treated as approving every call it might generate; humans are asked to approve opaque or minified code, thousands of generated actions, or a generic request for network access.
- Reason: excessive agency; authorization has to sit outside the model.

## 10. Verification

- Recommendation: verify independently of the model's claim. Check exit status and artifact existence, then type, schema, row counts, units, ranges, missing values and size limits; run declared and hidden tests in a fresh verifier process that generated code cannot modify; use an independent oracle where feasible (a second implementation, a database aggregate, a known formula, a solver, a compiler or type checker); use metamorphic tests when exact labels are missing. For code as action, also reconcile expected and actual nested call counts, tool IDs, pagination and snapshots, check evidence references against gateway records, and verify each write's postcondition against authoritative state. Mark each result verified, partially_verified, unverified, rejected or policy_denied, with named checks.
- Gap when: exit code zero, valid JSON, a plausible chart or a pass@k score is taken as correctness; generated code can change its tests or acceptance criteria; the program can summarize away the evidence needed for validation.
- Reason: misleading success through fabricated output, suppressed errors, altered tests or a plausible artifact that does not satisfy the task.

## 11. Repair and escalation loops

- Recommendation: repair only when the failure is plausibly fixable without changing user intent or broadening authority. Return a minimal diagnostic (failing line or test, bounded error excerpt, relevant schema, remaining budget) with secrets and instruction-like content removed, never the whole transcript and logs. The model may not ask for weaker controls, more imports, more tools or more network. Re-run every preflight check, execute in a fresh process, and use a fresh environment after a policy violation, package change, unexplained crash or suspected injection. Stop after the initial execution plus two repairs for an interactive task; allow up to five total attempts only for a durable software-engineering or read-only analytical task with explicit tests, remaining budget and no security signal; stop when a hashed state (normalized source, failure class, test results) repeats or when two consecutive repairs do not improve a named check. On a sandbox violation, secret access, unexpected egress, persistence attempt, obfuscation or cross-tenant signal, stop execution at once, revoke reachable credentials, quarantine artifacts and route to security; do not ask the model to repair it, resume only after a human-approved remediation with a new execution ID, and never loop between a denial and a model-generated workaround.
- Gap when: retries are unbounded or exceed the limits above; full logs are fed back to the model; a repair can weaken policy, add imports, widen the tool set or change intent; hidden provider regeneration is stacked with unlimited application retries.
- Reason: a repair must not weaken policy, increase authority or silently reinterpret user intent, and a security violation is never handed back to the model to repair.

## 12. Tool bindings

- Recommendation: generate every callable function from a canonical, versioned tool descriptor (ID, namespace, version, owner, input and output schemas, error taxonomy, side-effect class, reversibility, idempotency, required scopes, approval policy, definition digest) and keep a binding manifest that maps each language alias to one immutable version. Use stable, collision-free namespaces and separate reads from writes in namespace and type. Give the narrowest typed signatures and output schemas, and docstrings that state what the function does, when not to use it, permissions, side effects and named errors. A stub holds no credential and only calls the gateway; the namespace exposes no raw HTTP client, credential store, URL fetch, policy method or dynamic import. Bind only the minimum tools for the current stage, and rebuild the runtime when moving to a more powerful stage. Return a handle for large, sensitive or binary payloads and reauthorize every use of it. Use structured concurrency with capped fan-out for asynchronous calls, and pagination with page, item, byte and time caps that ends in a typed partial result at the cap.
- Gap when: every tool is exposed because the language can call it; a generic admin, execute or request function takes arbitrary paths or methods; code parses prose where a typed output schema could exist; child-call failures, truncation or partial pagination are swallowed.
- Reason: a general expression language will probe every reachable object; removing a function is stronger than telling the model not to call it.

## 13. Nested-call mediation

- Recommendation: parse the complete source before execution (never partial streamed code), produce an AST summary of bound-tool call sites, loops, branches and concurrency, and deny when the code references a side effect absent from the declared plan. At runtime, give every call from code its own ID and trace span, and revalidate tool version, schema, authorization, destination, quota, idempotency and approval at a gateway that injects principal and tenant from trusted infrastructure, even when preflight approved the whole program. The gateway denies unknown tools, versions outside the manifest, disallowed destinations, excessive data ranges and exhausted quotas, and denies a tool revoked after the program started.
- Gap when: the interpreter has ambient business authority; policy is checked only at preflight; any call can reach a service without the gateway.
- Reason: preflight cannot predict dynamic arguments and branch outcomes; the binding layer is the authoritative record of what actually ran.

## 14. Writes and side effects

- Recommendation: keep writes, approval-sensitive and irreversible calls direct by default, and bind no writes in read-only profiles. Where a reviewed exception makes a write callable from code, require a preview first (a dry run produced by the downstream system, never simulated by the model), pause at the gateway for approval bound to the exact operation hash, and reauthorize immediately before execution. Give every write an orchestrator-generated idempotency key tied to the intended operation and reused by repaired code; reconcile an unknown write outcome against authoritative state instead of retrying it.
- Gap when: a state-changing, approval-sensitive or irreversible call runs inside an opaque program; a write is retried after a timeout without reconciliation and the same key.
- Reason: duplicate or unapproved effects hidden among many generated calls.

## 15. Tool results and injection

- Recommendation: keep tool results typed with labelled provenance and treat them as data. Code reads declared fields and never passes returned strings to eval, a shell, an executing template engine, a dynamic import or a new model instruction channel. Sanitize error messages before repair prompts. Separate search from publish, read from send and lookup from upload; do not bind general messaging, URL fetch or object-write tools to a runtime that holds sensitive data without an explicit purpose and approval; apply data-loss prevention and destination policy at the gateway.
- Gap when: returned text is evaluated or forwarded as instructions; a send-capable tool is bound beside sensitive reads without approval.
- Reason: hostile tool results that try to redirect the program, and exfiltration through an allowlisted tool that accepts arbitrary text or destinations.

## 16. Discovery and fallback

- Recommendation: use progressive disclosure only when the policy-eligible catalog is too large to send or near-neighbour tools confuse selection, not for a small stable catalog. Retrieve definitions before program generation and freeze the callable set; a running program never hot-binds new authority. The discovery loop enters only for a specific missing capability (never after a policy denial), returns at most ten metadata candidates, ends the current execution, re-runs policy and digest checks outside the runtime and starts a new execution; at most two discovery rounds, stopping on a repeated candidate set. Fall back to direct typed calls when code-action execution repeatedly fails, the task collapses to one or two calls, intermediate results need model judgment, runtime capacity is unavailable or parsing proves unreliable; keep completed idempotent calls, do not replay writes, and allow one mode switch per task, after which a second failure ends or escalates the task.
- Gap when: a program can search for and import new clients while running; code and direct calls alternate without a limit; fallback is used to get around a sandbox, schema or policy denial.
- Reason: authority widening at run time, and oscillation that never converges.
