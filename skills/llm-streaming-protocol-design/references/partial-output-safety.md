---
created: "2026-11-04T19:48:58Z"
updated: "2026-11-04T19:48:58Z"
---

# Partial-output safety and long-lived connection security

## 1. Emission gates (classify output before choosing a streaming policy)

| Output class | Gate before emission |
|---|---|
| Low-risk conversational text | Stream through incremental secret, personal-data, abuse and format checks. |
| Factual output that needs citations | Stream only verified clauses, or show provisional UI that cannot be copied or acted on as final, then publish a verified final answer. |
| High-impact medical, legal, financial, security or operational guidance | Buffer semantic units or the full response until the required verification passes. |
| Tool arguments and commands | Never execute before complete parse, schema validation, authorization and approval. |
| Secrets, credentials, personal data, exploit details, restricted context | Block before emission; a later redaction is too late. |

- Partial completions are harder to moderate, and some moderation scores arrive only after the full output. If the safety control cannot decide on a prefix, buffer to a sentence, paragraph, structured field or the full response.
- Use a short holdback buffer so detectors see surrounding characters, and scan both raw deltas and the rolling reconstructed text: secrets and disallowed strings can cross chunk boundaries.
- Encode for the render destination and render text as text, not HTML; mishandled model output can lead to XSS, CSRF, SSRF, privilege escalation or code execution downstream.

## 2. Tool calls

When a call's arguments complete:

1. parse with the declared encoding;
2. validate against the exact tool schema and reject unknown fields;
3. take the tool name from trusted item metadata, not from streamed argument text;
4. authorize the current principal, target, side-effect class and current state;
5. derive and persist an idempotency key;
6. execute through the effect ledger;
7. stream only approved progress and redacted results;
8. commit the result before emitting it as authoritative.

Track each call as started, arguments partial, arguments complete, authorized, executing, result committed, failed or canceled. Never execute an eager prefix, partial JSON or a model-repaired fragment. If partial arguments end invalid, reject the item and do not execute; request regeneration once, with a new attempt ID, only if policy allows. If interleaved calls get mixed up, quarantine all affected calls, reconstruct by item ID and inspect for unintended effects. Raw tool output is untrusted context: never pass it straight to a renderer or the model.

## 3. Correction after emission

Once bytes reach a client, browser extension, proxy, screen reader, log or clipboard, treat them as disclosed; deleting them from the UI is not retraction. If a streamed claim becomes invalid:

1. stop further emission;
2. send a terminal `superseded` or `failed_verification` event;
3. prevent tool use and memory promotion from the invalid prefix;
4. visibly mark or remove the provisional UI content;
5. publish a correction linked to the original event IDs;
6. keep an incident trace and decide whether notification or deletion propagation is needed.

Claims that cannot tolerate this outcome are not emitted provisionally.

## 4. Long-lived connection security

- Authenticate before opening a stream and authorize the exact stream resource. Bind credentials and cursors to tenant, principal, audience, protocol and expiry. Revalidate on policy or privilege change, logout, reconnect, sensitive phase transitions and a configured interval. When authentication expires, stop sensitive emission, refresh through the approved path or close, and reauthorize before resume.
- WebSockets have no built-in authentication: validate `Origin` against an exact allowlist, use CSRF defences when cookies authenticate the handshake, cap message size and rate, close on session expiry or logout.
- SSE: configure CORS narrowly and use credentialed cross-origin EventSource only when required. Keep access tokens out of query strings (URLs enter histories and logs); prefer secure, HttpOnly, SameSite cookies for same-origin sessions, or streaming fetch with authorization headers and CSRF controls.
- Do not refresh authentication by sending a bearer token inside an application event unless the protocol and threat model protect it; prefer a new connection or a secure side-channel refresh.
- Treat every streamed tool result, agent-protocol artifact, broker event, transcript and state patch as untrusted: prompt injection can arrive one delta at a time or be split across chunk boundaries. Keep trust labels, normalise before scanning, and keep policy and tool authorization outside model-editable context.

Resource-exhaustion defences:

- per-principal and per-tenant quotas on connections, streams, bytes, events, reconnects and duration;
- maximum frame, message, decompressed payload, JSON depth, array length and tool-result size;
- slow-read deadlines and bounded outbound buffers, so no client can hold expensive inference by reading one byte at a time;
- fair scheduling across streams and admission control before allocating model or broker work;
- heartbeat and reconnect rate limits, circuit breakers and global kill switches;
- separate limits for authenticated but low-trust clients.
