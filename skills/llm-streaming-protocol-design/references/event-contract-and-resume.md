---
created: "2026-11-04T19:48:58Z"
updated: "2026-11-04T19:48:58Z"
---

# Event contract, ordering, delivery and resume

## 1. Invariants for every stream

1. The transport is not the protocol: TCP, QUIC, HTTP, SSE, WebSocket, gRPC and WebRTC carry an application event contract and supply no domain ordering, idempotency or authorization.
2. Partial is a distinct state: a delta is not a complete message, valid JSON object, verified claim, committed state change or executable tool call.
3. One ordering scope has one monotonic sequence; independent lanes each get their own sequence and a declared merge rule.
4. Every stream has one explicit terminal outcome: completed, failed, canceled, expired or superseded. A closed socket without a terminal event is ambiguous.
5. A cursor resumes only the exact logical stream and authorization scope it was issued for.
6. Where replay exists, redelivery is assumed and consumers deduplicate. Exactly once is not claimed across an external effect unless the destination enforces the same idempotency key.
7. Authoritative state commits before it is advertised as committed; optimistic progress events are labelled provisional.
8. Cancellation is end to end: proxy, gateway, provider call, tools, workers, broker subscription and state machine, within a measured deadline.
9. Every queue has a byte and event cap, a high-water action and an overflow terminal behaviour.
10. Already emitted bytes are disclosed; a later error cannot retract them.
11. Long-lived streams revalidate or terminate on credential expiry, revocation, logout, tenant change and policy change.
12. Applying accepted deltas in the declared order to the declared base reproduces the final object or a detectable error.
13. Unknown event types are ignored only when the negotiated version allows it; unknown security, state or tool events never execute.
14. Durations use a monotonic clock; wall time is for correlation.
15. No stream is unbounded: duration, bytes, events, reconnects, idle time, tools, media, cost and retained replay all have limits.

## 2. Envelope fields

Each application event carries, where applicable: `stream_id`, `event_id`, event `type`, schema and protocol version, ordering key, sequence, producer, server-receive and emit times, run, turn, message, item and parent IDs, tenant and pseudonymous principal, trace and span IDs, producer and model or tool version, payload media type, payload byte count and protected hash, provisional or committed state, replay flag, cursor or offset, sensitivity and trust class, and terminal or error metadata.

Keep transport identifiers (an SSE `id`, a broker offset, a provider response ID) distinct from the application event ID; they may correlate but are not interchangeable. Never put secrets, raw personal data, bearer tokens or meaningful user names in IDs or URLs.

Illustration of one content delta (field names only; values are placeholders):

```json
{"stream_id": "s-…", "event_id": "e-…", "type": "content.text.delta",
 "schema_version": "1", "ordering_key": "message:m-…", "sequence": 42,
 "item_id": "m-…", "state": "provisional", "replay": false,
 "emit_time": "…", "trace_id": "…", "payload": {"delta": "…"}}
```

## 3. Event families and assembly

- Lifecycle: stream started, phase or step started and completed, stream completed, failed, canceled, expired.
- Content: item started, text delta, audio delta, image or artifact reference, citation delta, item completed.
- Tools: tool call started, argument delta, arguments completed, execution started, progress, result, failed.
- State: snapshot, versioned patch, commit acknowledgement, conflict, invalidation.
- Control: heartbeat, rate-limit update, warning, interrupt acknowledgement, resume acknowledgement, drain notice.
- Usage: provisional token or byte count, and final provider-reconciled usage.

Every start, delta and end of one family share the same item ID and carry an index or sequence. The end event carries the final hash, length and validation result. Reject a delta before its start, a second start for an active item, a sequence regression, or an end whose reconstructed hash differs.

## 4. Provider adapters

Map provider events into the common envelope while keeping the original event type, response and item IDs, content index, provider sequence, finish reason, usage and a raw-event reference. Do not flatten everything into text. The adapter validates the provider schema and API version, locates the stream, item and content lane, enforces sequence and start-delta-end rules, appends only the delta field (never a repeated snapshot), holds executable or high-risk content behind its gate, translates completion, failure, incomplete and cancellation distinctly, reconciles the assembled object and usage with the provider's final object, and keeps unknown forward-compatible events in metadata without acting on them.

- OpenAI Responses API: typed SSE events such as `response.created`, `response.output_text.delta`, `response.output_text.done`, `response.completed`, `error`, and for function calls `response.function_call_arguments.delta` and `.done`. Key assembly by response ID, output item ID, output index and content-part index; `output_text.done` is not whole-response success, wait for the response terminal event. Stream reasoning content only if the application approves it.
- Anthropic Messages API: `message_start`, then per indexed block `content_block_start`, repeated `content_block_delta`, `content_block_stop`, then `message_delta` and `message_stop`, with `ping` and `error` possible between. Tool-use `input_json_delta` values are partial JSON strings: concatenate and parse at `content_block_stop`. Fine-grained tool streaming can yield invalid JSON; use it only for preview, and prefer buffered validated arguments for consequential tools.
- Google Gemini: `streamGenerateContent` (SSE with `alt=sse` over REST). Treat candidate and part index as an assembly lane; a chunk with safety feedback, finish reason or usage metadata is not a text delta. Do not assume other providers' event names apply.
- Take billing usage from the provider's final usage, not from locally counted display fragments.

## 5. Structured output and tool arguments

Choose one policy per structured output:

- Buffer then validate: accumulate, parse once at the end, validate the full schema, then publish or execute. Use for tool arguments, policy objects, financial or security actions and any cross-field invariant.
- Parse prefixes for preview: an incremental parser that separates complete values, incomplete values and invalid prefixes; publish only fields whose meaning is stable, labelled provisional.
- Stream patches: complete, individually valid operations (such as JSON Patch) against a versioned base; validate path allowlists, expected base version and postconditions before each commit.

Incomplete JSON is expected mid-stream: do not call an ordinary parser repeatedly and read failure as a broken stream, do not repair partial JSON with a model and execute it, and do not treat a string or array as stable before it closes. At the end, compare the reconstructed object's canonical hash with the provider's final object. Route interleaved tool-call deltas by item or call ID, never by arrival order.

## 6. Delivery contract (declare one per event family)

- Best effort: loss is acceptable and a later snapshot repairs the view.
- At most once: no replay; a gap becomes an error or forces a full refresh.
- At least once: replay may duplicate; consumers deduplicate by event ID.
- Effectively once within a closed system: transactional source offsets and outputs prevent duplicate committed records inside a stated boundary.
- Exactly once external effect: only when the destination atomically enforces the idempotency key, or a transaction spans source position and effect.

No blanket claim for the whole system: a UI heartbeat may be best effort while an email send is at least once with reconciliation. Resume needs durable cursors and replayable data; do not claim resume if one process holds the only replay buffer.

## 7. Reconnect-and-resume loop

1. Mark the connection lost; record the last parsed, validated and durably applied event ID and sequence. Never advance the cursor for bytes merely received.
2. Cancel or pause dependent local work that cannot tolerate a gap.
3. Classify the close: clean terminal, client cancellation, authentication or policy failure, idle timeout, server drain, transient network failure, protocol error, unknown.
4. Do not reconnect after explicit cancellation, terminal completion, policy denial, invalid credentials, unrecoverable protocol mismatch or an exhausted retry budget.
5. For retryable loss, back off exponentially with jitter, honour provider retry hints and an overall deadline, and cap attempts and concurrent reconnects.
6. Reauthenticate and reauthorize; never put a long-lived token in the cursor.
7. Send the last committed cursor only if the protocol supports it, bound to stream, tenant, principal, protocol version and expiry.
8. Require the server to acknowledge the resolved resume position. If the cursor is too old, unknown, ahead or foreign, fetch a current snapshot or restart under the fallback policy; never search for a nearby cursor.
9. For each replayed or live event: validate schema and scope, discard an already committed event ID, detect sequence gaps, apply once to the local view, and commit the new cursor atomically with the view update.
10. Stop when a valid terminal event commits, the user cancels, or the deadline, cost or attempt budget ends.

Without replay, reconnect restores only future updates: show the gap and fetch a snapshot or the final resource. Never stitch streams silently across an unknown interval. A silent mid-stream close is ambiguous: never mark the result complete from socket end alone.

## 8. Ordering and multiplexing

Give each logical item an ordering key (run, task, message, tool call, artifact, media track) and sequence within it; avoid a global total order unless the application needs it. When multiplexing, put the channel or item ID on every event, keep per-channel sequence and flow-control accounting, decide whether lifecycle events form a control lane, never let a large artifact starve cancellation, heartbeat or terminal events, schedule with bounded fairness and priority for control, and detect gaps per channel. On a sequence gap, pause the dependent view, request replay, then fall back to a snapshot; do not apply later non-commutative patches over a gap. Buffer out-of-order events only within a small bounded reorder window.

## 9. Agent interoperability protocols

- MCP Streamable HTTP: pin the specification revision. The 2025 revisions (2025-03-26, 2025-06-18, 2025-11-25) allow a server session ID, SSE event IDs as per-stream cursors and `Last-Event-ID` replay of the disconnected stream. The 2026-07-28 revision removes protocol sessions, the standalone GET stream, resumability and `Last-Event-ID` redelivery: a broken response stream loses the in-flight request, which the client reissues with a new request ID while reusing a domain idempotency key; cross-call state uses explicit handles. Never mix revisions silently; an adapter exposes the weaker guarantee and does not label emulated resume as native.
- A2A task streaming: check that the Agent Card advertises streaming. Keep task ID, context ID, event kind, artifact ID, append or final semantics, task state and terminal flag. Resubscription may not backfill missed events: on disconnect, query authoritative task state first, resubscribe if active, fetch the final task and artifacts if terminal, and never restart a terminal task to repair a display stream.
- AG-UI: keep thread, run, parent run, message and tool-call IDs; enforce start-content-end order; apply `STATE_DELTA` only as a patch against the declared state version, rejecting unauthorized paths and conflicts, and recover a missed patch with `STATE_SNAPSHOT`. Do not send chain-of-thought, secrets, raw tool results or backend-only state through `RAW` or `CUSTOM` events. A UI event never grants tool authority or writes canonical state.
