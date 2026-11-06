---
created: "2026-11-04T19:48:58Z"
updated: "2026-11-04T19:48:58Z"
---

# Whether to stream, and which transport

## 1. When not to stream

An SDK flag that enables streaming is not a reason to stream. Choose a buffered response when any of these holds:

- the complete result is small and normally arrives within the interaction budget;
- the whole output must pass moderation, legal review, schema validation, signature verification or cross-field constraints before anyone sees it;
- exact snapshot consistency matters more than progressive availability;
- the consumer cannot use partial results, or would render them as final;
- a later correction cannot safely compensate for an early statement;
- the network or client cannot hold long-lived connections reliably;
- the work is cheap and idempotent and restarts faster than resume machinery could recover it;
- the operation is an irreversible tool effect, not user-visible narrative progress;
- batching materially cuts cost or improves quality and the added queue delay stays within the service objective;
- the streaming infrastructure, telemetry and failure tests are not yet in place.

Other delivery modes:

- Status polling or asynchronous job completion: work lasts minutes or hours and updates are sparse.
- Webhooks: the client need not hold a connection and can expose a secure callback.
- Broker consumer: the receiver is a backend processing system, not an interactive client.

Decide per output kind, not for the whole application: separate user-visible text, structured output, tool calls, state, artifacts and media, and give each one of buffered, progressive preview, committed event or no delivery. If the only gain is animation and the safety or operational cost is material, choose buffered delivery. Start from a non-streaming baseline and keep streaming only where it improves the first safe, useful output.

## 2. Transports

Compare candidates on directionality, browser support, binary media, flow control, reconnect, intermediaries, operational maturity and scale, then prototype the simplest one that fits through the real proxy chain.

### Plain HTTP response streaming (chunked transfer)
- Use for one request and one ordered response when the client controls parsing and browser EventSource behaviour is not needed; suits newline-delimited records, binary chunks and SDKs built on streaming fetch.
- Never treat HTTP/1.1 chunk boundaries as application events: intermediaries may decode and reframe them, and under HTTP/2 and HTTP/3 chunked transfer coding is not the framing. Delimit records inside the byte stream with a length, a delimiter or a self-describing event format.
- Not when automatic browser reconnection, named events or a standard resume header is required.

### Server-Sent Events (SSE)
- Use for server-to-client text events over ordinary HTTP when the browser sends commands through separate HTTP requests. Records are UTF-8 `text/event-stream` with `event`, `data`, `id` and `retry` fields; a blank line ends an event, several `data` lines concatenate, and comment lines can serve as keepalives.
- Use named events, not one overloaded `message` event. Give resumable events stable `id` values and treat browser reconnect as at-least-once delivery: the browser keeps the last event ID, waits the reconnection delay and sends `Last-Event-ID`.
- EventSource is not a replay log: the server must map the ID to retained events and enforce stream, tenant and authorization scope.
- Native EventSource cannot set custom request headers freely; if bearer headers or a POST body are needed, use a streaming fetch client or an authenticated same-origin session with suitable controls. Do not rely on cookies without CSRF and origin controls.
- Over HTTP/1.1 browsers allow only a few EventSource connections per origin (six); multiplex logical channels inside one connection or use HTTP/2.
- Not for high-rate bidirectional input, unordered unreliable media, or client-to-server flow control on the same channel. Put cancel, interrupt, approval and context updates on a separate command endpoint, correlated by stream and run ID.

### WebSockets
- Use when the application needs low-latency full duplex: live user interrupts, collaborative state, frequent client events, bidirectional tool control, or messages started by either side on one connection.
- WebSocket supplies frames only: define heartbeats, reconnect, authentication refresh, sequencing and replay yourself.
- The classic browser WebSocket interface has no stream backpressure, so a client that receives faster than it processes accumulates memory. WebSocketStream adds backpressure but is experimental; depend on it only after a compatibility decision.
- Not for one-way token display when SSE or streaming fetch is enough. Keep critical state out of the connection object; reconnect to a logical stream through a durable cursor, not to a particular worker.

### WebTransport over HTTP/3
- Use for browser applications that need several independent reliable streams plus optional unreliable datagrams, such as low-latency multimodal systems where one lost packet must not stall unrelated streams.
- Not for ordinary text streaming without a measured, material benefit; browser, proxy and observability support is less universal. Datagrams may be dropped or reordered: never carry authoritative state transitions, tool approvals or the only copy of context in them.

### gRPC streaming
- Use server streaming for typed backend-to-backend output, client streaming for batched incremental input, bidirectional streaming for peer-like services, when both ends share schemas, HTTP/2, deadlines, cancellation and code generation.
- gRPC applies flow control and waits when the receiver lacks capacity; manual flow control can deadlock if both sides write heavily without reading. Read and write concurrently, bound message sizes, propagate deadlines and cancellation.
- Not directly to browsers unless gRPC-Web or a gateway supports every streaming mode needed. Coordinate keepalive with the service owner: excessive pings draw `GOAWAY` with `too_many_pings`; avoid sub-minute client intervals without an agreement.

### HTTP/2 or HTTP/3
- HTTP/2: broad compatibility, one TLS connection, stream multiplexing, mature operations; all streams share one TCP connection, so they share packet-loss recovery.
- HTTP/3: mobile or lossy networks, fast connection setup, and no cross-stream blocking from packet loss, when that materially improves measured tail latency.
- Do not migrate for average latency alone; measure handshake, first event, reconnect, p95 and p99 completion, CPU, memory and proxy compatibility on representative networks. Ordering, replay and deduplication are still needed on both.

### WebRTC (voice and live multimodal)
- Use for browser or mobile voice and live multimodal interaction where media transport, jitter handling, echo control and low-latency duplex are central: media tracks for audio or video, a data channel for control events. Mint short-lived client credentials on a trusted backend; never put long-lived provider keys in a client.
- Not for ordinary server-rendered text. Treat signaling, ICE, TURN, media and control as separate failure domains; a control event that commits state must be reliable, ordered, acknowledged and idempotent.
- Keep separate lanes for input audio, speech detection, transcription, model text, output audio, tool calls and control, each with sequence, media timestamp, item ID and cancellation behaviour. Keep a bounded jitter buffer, drop obsolete best-effort audio frames instead of growing latency, put tool actions and state commits on a reliable ordered lane, propagate barge-in immediately, and distinguish generated audio from played audio so unheard output leaves the model-visible conversation after an interruption.

## 3. Choosing in practice

- One-way text to a browser, commands as separate requests: SSE, or streaming fetch when headers or a POST body are needed.
- Frequent client events, interrupts or collaborative state on one connection: WebSockets, with application-level sequencing, heartbeats and replay.
- Typed service-to-service output: gRPC streaming.
- Voice and live media: WebRTC.
- Sparse updates over long work: asynchronous job with polling or a webhook.
