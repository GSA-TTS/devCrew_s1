---
created: "2026-11-04T19:48:58Z"
updated: "2026-11-04T19:48:58Z"
---

# Backpressure, cancellation, timeouts, intermediaries and fallback

## 1. Backpressure loop (each producer, queue and consumer boundary)

1. Measure queued bytes, queued events, oldest-event age, consumer drain rate and producer rate.
2. Below the low-water mark, read or request normally.
3. At the high-water mark, stop upstream reads or reduce demand where the API allows.
4. If upstream cannot pause: coalesce replaceable deltas, spill replayable events to durable storage, reduce optional fidelity, or rate-limit the producer.
5. Never coalesce terminal, error, authorization, tool-effect or non-commutative state events.
6. At the hard cap or maximum age: cancel the stream, disconnect the slow consumer, or switch to snapshot-and-cursor recovery, as the contract says.
7. Resume reads only once the queue is below the low-water mark (hysteresis prevents oscillation).
8. Record the incident and tune from measured distributions.

Set soft and hard byte and event caps at the provider adapter, gateway, pub/sub, proxy and client, and reserve a control lane. Keep the backpressure signal across adapters (in the web Streams model, the queuing strategy's high-water mark and `desiredSize`); do not drain a provider stream eagerly into an unbounded list. Accumulating bytes until memory runs out is not backpressure.

## 2. Chunking and coalescing

- Tiny chunks lower perceived latency but add syscalls, framing, rendering, compression, logging and scheduling cost; large chunks raise throughput but worsen first-token and interrupt latency.
- Start from the provider's semantic events. Coalesce display-only text for a short time or byte threshold, flushing at once on punctuation, newline, phase change, tool boundary, safety decision, cancellation, terminal event or maximum delay. Never split a UTF-8 code point. Batch UI updates to a frame cadence rather than rendering every token.
- Audio: cadence and packet size suited to the codec and jitter buffer. Artifacts: fixed bounded chunks with offset and final hash. JSON: chunk boundaries mean nothing unless the application defines complete patch operations.

## 3. Tuning

Baseline at representative concurrency and networks; change one parameter at a time (coalescing delay, byte threshold, high-water mark, connection count, flow-control window, heartbeat, broker batch size); measure time to first useful event, inter-event latency, completion, CPU, memory, bytes, queue age, reconnect success and smoothness, stratified by output length, client speed, transport, region, model and concurrency. Reject a change that improves the median while breaking p95 or p99, memory, safety or cancellation objectives. Do not tune against localhost alone: include mobile loss, high round-trip time, browser backgrounding, a slow renderer and the proxy chain. Never tune away a safety or correctness guard to improve first-token latency.

## 4. Live updates, interrupts and cancellation

- Next-turn injection (default): accept new context during generation, store it, include it in the next model request.
- Cancel and restart: when the update invalidates the current answer, permissions or tool plan. Persist the update, cancel the provider call and tools, mark emitted output superseded, start a new run with a new response ID.
- Provider-native live events: only when the API explicitly supports mid-session input; record whether the update affected the current or the next response.

Interrupt handling: authenticate the sender and resolve the active run; classify (cancel, stop speaking, replace context, add context, change priority, approve, deny); check the current state permits it; persist it with the target run or item ID; signal all children and provider calls; stop new non-essential deltas for the canceled item; reconcile any tool effect already started (socket close does not undo it); emit an interrupt acknowledgement with committed state; wait up to the cancellation objective, then fence late events and escalate runaway work; start a replacement turn only after the new context and state version commit. If cancellation races completion, commit one winner under the expected state version and fence the loser. A tool that completes after cancellation is recorded and reconciled, not injected into the canceled run.

## 5. Heartbeats, timeouts and intermediaries

Configure and test every hop: client, browser, mobile OS, CDN, WAF, load balancer, ingress, service mesh, application server, provider and broker. Any hop whose buffering, timeout or connection-limit behaviour is unknown is an open item.

Set: connection-establishment timeout; time to response headers; time to first application event; inter-event idle timeout; provider or tool phase timeout; heartbeat interval and acknowledgement deadline; maximum connection and stream duration; overall run deadline; drain grace period.

- Send an application heartbeat when a legitimate stream can be silent longer than the shortest idle timeout: an SSE comment line, a WebSocket ping/pong, or coordinated HTTP/2 PING for gRPC. Choose the interval below the shortest idle timeout with margin, but not so frequent that it loads the fleet.
- A heartbeat proves path liveness, not progress: progress deadlines must still fire, and a dead stream is not kept alive forever with heartbeats.
- Disable response buffering on streaming routes (NGINX buffers proxied responses by default; `proxy_buffering off` or an `X-Accel-Buffering: no` response header changes that unless configuration ignores it), and also compression aggregation and middleware buffering. Align load-balancer and proxy idle and stream timeouts (Envoy treats connection idle and active-stream timeouts separately). Verify with timestamped events at the client; a header or configuration claim is not evidence. If the chain still buffers, disable streaming for that route instead of presenting burst delivery as streaming.

Deploy and scale-down: mark the instance unready for new streams; send a drain notice where the protocol supports it; let active streams finish within grace; persist cursors and terminal state outside the instance; cancel or transfer remaining work safely; close with a classified reason; make clients reconnect with jitter. Against reconnect storms: server retry hints, exponential backoff with jitter, admission control and regional circuit breakers; rate-limit broker catch-up and prioritise terminal events and the current snapshot.

## 6. Fallback ladder (define before an outage)

1. Preferred streaming transport.
2. Alternate streaming transport, only if its semantics are tested.
3. Buffered synchronous response for short work.
4. Asynchronous job with polling or callback for long work.
5. Cached or partial result labelled with its age and missing guarantees.
6. Safe failure with a retryable task identifier.

Keep the same event and final-result schema where possible, and tell the client which guarantees changed: no progressive output, no resume, delayed updates, stale snapshot or lower media fidelity. Never downgrade silently from durable replay to best effort. If streaming fails after partial disclosure, keep the partial item provisional, get the final object through a buffered path, compare hashes, and replace or finalise visibly; reconcile any possible effect before retrying.

Every retry names its retryable error classes, maximum attempts, maximum elapsed time, backoff, jitter, idempotency behaviour, changed input, cost cap and terminal action. Never retry an unchanged authorization, schema, policy or effect-ambiguity failure. A provider error after an HTTP success status is a typed stream error and terminal failure; do not rely on HTTP status alone.

## 7. What to observe

One root span per user-visible run; high-volume events as span events or logs, never one span or UI render per token. Child spans for connection, authentication, provider request, first event, tool call, replay, resume, snapshot, backpressure incident, cancellation and terminalization. Log per-event times, sequence, cursor, queue state, safety decision, usage and terminal outcome as metadata, without raw content. Test with a client that can pause reads, disconnect at any event boundary, reconnect, duplicate events and corrupt frames.
