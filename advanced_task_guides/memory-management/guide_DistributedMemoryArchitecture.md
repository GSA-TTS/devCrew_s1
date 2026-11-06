# Distributed Agent Memory

**Status**: Beta

**Change logs**:

- [09/08/2026] - Initialization

***

## Executive Summary

Distributed agent memory constitutes the task family of designing, declaring, and operating one logical memory that is stored or served across failure domains, processes, partitions, replicas, regions, or specialised systems, where no single component holds the whole state. This guide provides AI agents with a structured protocol for making the consistency contract explicit rather than emergent: what an agent is guaranteed to read after another agent writes, what it is not, and what the system does when that guarantee cannot be met. It specifies a distribution gate that refuses distribution absent a measured requirement, a six-phase framework covering topology and consistency declaration, partitioning and placement, the write path with replication and conflict detection, the read path with numeric staleness bounds, conflict resolution and semantic merge, and partition handling with reconciliation. It fixes the execution-tier partition that governs the method: replication, quorum arithmetic, version-vector comparison, partition detection, and conflict detection are deterministic and are never delegated to a model, while semantic merge of two conflicting natural-language memory values is the model tier's only load-bearing role and remains subordinate to deterministic authority. It emphasizes structured execution protocols, quality assurance checkpoints, and error handling procedures so that a memory population converges by design rather than by accident.

***

## I. Foundational Concepts and Definitions

### 1.1 Core Terminology

**Distributed agent memory**: One logical memory whose storage or service spans more than one failure domain, such that no single process, replica, shard, or region holds the whole state and a partial failure leaves part of the memory reachable and part of it not.

**Canonical record**: The single authoritative representation of a memory item, holding its identity, current version, provenance, authorization label, and deletion state. Every other representation is a derivative.

**Derivative**: A representation regenerable from the canonical record and the change log, such as a vector entry, a lexical index document, a summary, a cache entry, or an analytics copy. A derivative is never truth.

**Consistency model**: The declared statement of what a read may return relative to prior writes. A system that never declares one still has one, and it is normally the weakest behaviour its components permit, discovered in production.

**Session guarantee**: A per-session property weaker than global ordering but sufficient for an agent operating over its own history. The four in use are read-your-writes, monotonic reads, monotonic writes, and writes-follow-reads.

**Consistency token**: An integrity-protected value carrying tenant, subject, canonical version, partition-map epoch, and log position, issued on write and presented on subsequent reads so that routing can enforce a session guarantee.

**Staleness budget**: The maximum age, in milliseconds or seconds, that a read of a named memory class may carry before the response is either rejected or labelled degraded. A budget without a labelling rule is not a budget.

**Partition key**: The attribute determining which logical partition holds a record. It is selected from access paths and failure boundaries, not from hashing convenience.

**Partition-map epoch**: A monotonically increasing integer identifying the current mapping of logical partitions to physical owners, carried in every request so that a stale route is rejected rather than written.

**Quorum arithmetic**: The relationship among replication factor, write acknowledgement count, and read response count that determines whether a read set and a write set are required to overlap. Overlap is encouraged where read plus write counts exceed the replication factor, and this is a necessary condition rather than a correctness proof.

**Version vector**: Per-replica counters attached to a record that establish whether one version descends from another or the two are concurrent. Concurrency detection is a mechanical comparison and never an inference from wall-clock time.

**Last-writer-wins**: A resolution rule that keeps the version bearing the higher timestamp and discards the other. It loses data by construction, and any deployment choosing it must name that loss.

**Conflict**: Two versions of one record that are concurrent under version-vector comparison, meaning neither descends from the other. Conflict is detected deterministically; whether the conflict is semantically material is a separate question.

**Semantic merge**: The production of a single reconciled value from two concurrent natural-language versions where no mechanical rule determines the answer. It is proposed by a model and admitted by a deterministic component.

**Split-brain**: A state in which two partitions of one replication group both accept writes, producing two histories that must later be reconciled. Fencing tokens and quorum requirements exist to prevent it; reconciliation exists because prevention sometimes fails.

**Fencing token**: A monotonically increasing value issued with leadership or a lease, presented on every protected write. Resources reject any token lower than the highest they have observed, which stops a paused former owner from resuming.

**Outbox**: A row written in the same local transaction as the canonical mutation, relayed to downstream consumers so that derivative updates never depend on a dual write from request code.

**Reconciliation**: A continuous deterministic sweep comparing canonical versions against derivative versions, re-enqueueing missing work, quarantining impossible regressions, and measuring orphan age.

**Read-your-own-writes violation**: An event in which an agent commits a write, then issues a read that does not observe it. It is the most common distributed-memory failure in agent populations because a load balancer routing to a lagging replica produces it silently.

### 1.2 The Consistency Declaration

The single discipline this guide imposes is that distributed memory questions have known answers in distributed systems, and an agent population does not get to invent new ones. Every operation class must carry a declared model before any agent writes through it.

**The declaration obligation**: For each memory class and each operation on it, the deployment must state the model, the session guarantees, the staleness budget, and the behaviour when the budget cannot be satisfied. An undeclared operation is a defect and must halt release, not proceed with a warning.

**The model ladder**: Linearizable operations appear instantaneous between invocation and response and respect real-time order. Serializable transactions admit one equivalent serial order without a real-time claim. Causal consistency preserves happens-before relationships while allowing concurrent operations to appear in different orders across observers. Session consistency supplies the four session guarantees to one session without a global claim. Bounded staleness supplies a numeric maximum age. Eventual consistency promises convergence after writes stop and says nothing about what a read returns before then.

**The assignment rule**: Authorization state, ownership, deletion state, uniqueness, and any checkpoint gating an irreversible action take linearizable or serializable treatment with a staleness budget of 0 milliseconds. An agent's own recent writes take session consistency at minimum. Discovery, ranking, recommendation, and analytics take bounded staleness with a stated number. No memory class takes eventual consistency without both a stale-result marker on the response and a repair objective.

**The partition-tolerance tradeoff, stated operationally**: During a network partition a replication group either preserves single-copy consistency and refuses some requests, or continues answering and admits divergence. There is no third behaviour. Outside a partition the same group still trades consistency against latency, which is why a healthy cross-region quorum still adds a round trip. The deployment must therefore record, per memory class, which of the two partition behaviours applies, because the choice is made either deliberately at design time or accidentally at incident time.

**The consensus bound**: Deterministic consensus cannot guarantee termination in a fully asynchronous system with even one crash failure, so production protocols progress by adding timing assumptions, failure detectors, randomised behaviour, or operator intervention. A majority-commit protocol cannot write safely when no majority can communicate. Consensus is therefore a safety mechanism with an availability cost, not an availability layer.

**The token mechanism**: Session guarantees are enforced by carrying a consistency token, not by hoping a replica has caught up. On write, the canonical store returns the commit log position; the token records it. On read, the router either selects a replica whose observed log position is at least the token's required position, or falls back to the leader, or returns an explicit failure. Silent downgrade to a lagging replica is prohibited, and any downgrade that does occur must be recorded with a reason code.

### 1.3 The Execution Tier Partition

Every activity in this method belongs to exactly one execution tier. The partition is not advisory: it determines which failures are possible and which are excluded by construction.

**Deterministic tier**: Replication and acknowledgement counting, quorum arithmetic, version-vector and logical-clock comparison, timestamp handling, partition and quorum-loss detection, fencing-token issue and rejection, conflict detection, idempotency-key deduplication, staleness computation, consistency-token validation and routing, partition-map epoch enforcement, outbox relay, reconciliation sweeps, tombstone propagation, and every count reported in a metric. These require exactness, reproducibility, and auditability that model inference cannot supply. A model must never be asked to decide whether two versions are concurrent, whether a quorum was achieved, whether a partition exists, or which replica is current. Any design that routes such a question to a model has replaced a decidable computation with a probabilistic one and must be rejected at review.

**Model tier**: Semantic merge of two concurrent natural-language memory values where no mechanical rule determines the answer, drafting of the human-readable conflict summary attached to an escalation, and classification of a detected conflict's subject matter into a policy category. These require open-vocabulary judgement over natural language. The model tier proposes; it never commits.

**Hybrid tier**: Conflict adjudication in full. A deterministic component detects the conflict, retrieves both parent versions with their causal metadata and provenance, and decides by policy whether the conflict is eligible for automated merge. Where it is, a model proposes a merged value. A deterministic component then validates the proposal against schema, length, provenance-coverage, and prohibited-content rules, writes the merged value as a new version linked to both parents, and preserves both parents unmodified. Where the deterministic component rejects the proposal, the conflict escalates. The deterministic component holds authority in every disagreement without exception.

**Tier assignment of the framework phases**:

| Phase | Owning tier | Model tier involvement |
| :-- | :-- | :-- |
| Phase 1: Topology and consistency declaration | Deterministic | None |
| Phase 2: Partitioning and placement | Deterministic | None |
| Phase 3: Write path, replication, conflict detection | Deterministic | None |
| Phase 4: Read path and staleness bounds | Deterministic | None |
| Phase 5: Conflict resolution and semantic merge | Hybrid | Proposes a merged value only |
| Phase 6: Partition handling and reconciliation | Deterministic | Drafts escalation summaries only |

**What the deterministic tier rejects**: A write bearing a partition-map epoch lower than current; a write bearing a fencing token lower than the highest observed; a read whose consistency token requires a log position no reachable replica has applied, where the fallback path is also unavailable; a merge proposal that drops provenance for either parent, that alters a field outside the conflicting field set, or that fails schema validation; and any response that would carry a staleness above its class budget without a degraded label.

### 1.4 The Distribution Gate

Distribution buys scale, geographic locality, tenancy isolation, fault containment, and independent ownership. It also introduces partial failure, replica lag, ambiguous outcomes, reordering, duplicate delivery, conflict, cross-region cost, operational load, and additional deletion surfaces. The gate exists because the second list is paid unconditionally and the first is earned only against a measured requirement.

**Gate conditions for distributing**: Open the gate where at least one holds and is measured rather than anticipated. Throughput, corpus size, or index growth exceeds one node's safe limits after query and schema optimisation. Regulatory residency requires named tenants or fields to remain in a jurisdiction. Interactive latency requires data close to agents in more than one region. Blast radius must be isolated among tenants, workloads, or sensitivity classes to meet a stated reliability or governance objective. Memory is inherently heterogeneous, so that transactional claims need constraints, vectors need approximate-nearest-neighbour search, text needs lexical ranking, large artifacts need object storage, and ordered propagation needs a log. Region-loss continuity is required and the requirement supplies explicit recovery-point and recovery-time objectives.

**Gate conditions for refusing**: Refuse distribution where the only argument is that the agent population is itself distributed, that a vendor offers a cluster, or that hypothetical future scale should be anticipated. Refuse a second writable region before single-region backup restore, load shedding, tenant isolation, reconciliation, and observability are proven. Refuse splitting canonical and derived state across specialised systems where one partitioned transactional deployment with full-text search, object references, and vector support meets the stated service objective.

**The default architecture**: One region, one canonical transactional store, one object store, and optional derived indexes. Read replicas are added only after read pressure is measured. Shards are added only after capacity or isolation pressure is measured. A second region is added only after user latency is measured or a region-loss requirement is documented. Each additional system creates storage amplification, change-propagation, schema-rollout, authorization, backup, deletion, and incident surface, and each must therefore justify itself against the simpler design it replaces.

**Numeric gate rules**: Distribute a memory class only where the simpler design has been measured and fails its objective by more than 20 percent on at least one dimension, or where a residency or isolation obligation is contractual. Where measured headroom on the single-node design exceeds 40 percent at projected twelve-month load, refuse distribution and record the measurement. Where a specialised store fails to beat the general-store baseline by at least 25 percent on the quality, latency, or cost dimension it was introduced for, remove it at the next review.

**Boundary against neighbouring task families**: This guide covers the storage and systems layer only. Which agent knows what, and how work is routed to the agent holding relevant expertise, is transactive memory and a separate task family; this guide specifies only the storage contract such a directory must satisfy, namely a staleness budget of no more than 5 seconds with lease-backed health checks preventing routes to expired owners. Memory tiering across working, episodic, and semantic layers is a separate task family; tiering determines what is stored where in a hierarchy and does not determine replication or consistency, which remain this guide's subject.

***

## II. Operational Framework: Declared-Consistency Memory Across Failure Domains

The framework assumes the distribution gate in Section 1.4 has returned a measured requirement. Phases 1 and 2 execute once per memory class and re-execute on topology change. Phases 3 through 5 execute per operation. Phase 6 runs continuously and also on partition detection. Every phase belongs to the deterministic tier except Phase 5, which is hybrid.

### Phase 1: Topology and Consistency-Model Declaration

**Objective**: Fix the distribution requirement, the consistency model for every operation class, and the session-guarantee mechanism before any agent writes through the memory, so that the contract is declared rather than discovered in production.

#### Step 1.1: Inventory Memory Classes and Prove the Distribution Requirement

**Required Actions**:

- Enumerate every memory representation in the system, naming for each its canonical source, its derivatives, its tenant and residency scope, its write path, its read path, its deletion path, its current volume, its peak rate, and its business impact.
- Assign exactly one accountable owner to each representation, and dissolve any grouping named as shared or miscellaneous memory into owned entries.
- Measure the simpler single-region design against each class objective, recording capacity headroom, latency by user region, failure-domain requirements, residency obligations, and isolation obligations.
- Record the distribution decision per class alongside the measurement that justified it, and record refusals with equal specificity.
- Reject any distribution proposal supported only by projected rather than measured load.

**Required Outputs**:

- A memory-class inventory with owner, canonical source, derivative list, and scope per entry.
- A measurement record per class comparing the simpler design against the class objective.
- A distribution decision record naming, per class, distribute or refuse, with the governing measurement.

**Quality Checkpoints**:

- Every representation in the inventory carries exactly one accountable owner; unowned representations halt the phase.
- Every distribute decision cites a measurement showing the simpler design failing its objective by more than 20 percent on a named dimension.
- No class carries a distribution decision whose only support is anticipated growth.

***

#### Step 1.2: Declare the Consistency Model Per Operation Class

**Required Actions**:

- Assign each operation on each memory class exactly one model from linearizable, serializable, causal, session, bounded-stale, or eventual.
- Assign linearizable or serializable treatment with a 0 millisecond staleness budget to authorization state, ownership, deletion state, uniqueness constraints, and any checkpoint gating an irreversible action.
- Assign a numeric staleness budget in milliseconds or seconds to every operation not taking a linearizable or serializable model.
- State, per class, the partition behaviour: refuse writes and preserve single-copy consistency, or continue accepting writes and admit divergence requiring reconciliation.
- Record the model, the budget, and the partition behaviour in the API contract so that every response reports both requested and effective consistency.

**Consistency Assignment Defaults by Memory Class**:

| Memory class | Declared model | Staleness budget | Partition behaviour |
| :-- | :-- | :-- | :-- |
| Authorization, ownership, deletion state | Linearizable | 0 ms | Refuse writes |
| Side-effect checkpoints | Linearizable compare-and-set | 0 ms | Refuse writes, pause action |
| Working state within one task | Session | 0 ms for own writes | Refuse writes |
| Episodes, own session | Session with durable append | 0 ms for own writes | Refuse writes |
| Episodes, cross-session retrieval | Bounded stale | 5 s | Continue, labelled |
| Semantic claim status transitions | Serializable | 0 ms | Refuse writes |
| Semantic claim discovery | Bounded stale | 60 s | Continue, labelled |
| Vector index, interactive retrieval | Bounded stale | 60 s | Continue, labelled |
| Vector index, background discovery | Bounded stale | 300 s | Continue, labelled |
| Blob bytes | Bounded stale | 900 s cross-region | Continue, labelled |
| Blob metadata and tombstones | Session or stronger | 0 ms | Refuse |
| Cache, low-risk content | Bounded stale | 30 s | Continue, labelled |
| Cache, authorization or consent state | Not cacheable | 0 ms | Refuse |

**Required Outputs**:

- A per-operation consistency declaration naming model, staleness budget, and partition behaviour.
- An API contract revision through which every response reports requested and effective consistency.
- A defect list of operations for which no model could be assigned.

**Quality Checkpoints**:

- Every operation class carries exactly one declared model; an operation with no declaration halts release.
- Every non-linearizable operation carries a numeric staleness budget expressed in milliseconds or seconds.
- No class assigned eventual consistency lacks both a stale-result marker on the response and a named repair objective.

***

#### Step 1.3: Declare Session Guarantees and Specify the Consistency Token

**Required Actions**:

- State, per memory class, which of read-your-writes, monotonic reads, monotonic writes, and writes-follow-reads are guaranteed, and state explicitly which are not.
- Define the consistency token to carry tenant, subject, canonical version, partition-map epoch, and commit log position, and protect it against modification in transit.
- Require the canonical store to return the commit log position on every acknowledged write, and require the caller to attach the token to every subsequent read in the same session.
- Specify the read-routing rule in three ordered outcomes: select a replica whose observed log position is at least the token's required position; otherwise route to the leader; otherwise return an explicit failure naming the unmet guarantee.
- Prohibit silent downgrade, requiring any downgrade to be returned to the caller and logged with a reason code.

**Required Outputs**:

- A session-guarantee declaration per memory class naming guaranteed and unguaranteed properties.
- A consistency-token specification with its field set and its integrity protection.
- A read-routing rule with its three ordered outcomes.

**Quality Checkpoints**:

- Read-your-writes is guaranteed for every class an agent writes and then reads within one task; classes without it are named explicitly as not guaranteeing it.
- The routing rule terminates in an explicit failure rather than in a best-effort read.
- No path returns a response whose effective consistency differs from the requested consistency without a returned and logged reason code.

***

### Phase 2: Partitioning, Placement, and Boundary Enforcement

**Objective**: Fix where each record lives, which boundary contains it, and how ownership moves, so that routing is decidable and a misplaced write is rejected rather than accepted.

#### Step 2.1: Select the Partition Key From Measured Access Paths

**Required Actions**:

- Derive candidate partition keys from observed access paths and failure boundaries rather than from hashing convenience.
- Replay production-shaped keys against each candidate and measure request rate, bytes, index growth, and p99 latency per resulting logical partition.
- Reject any candidate producing a partition above 70 percent of tested sustained capacity, and reject any single globally popular identifier, default-tenant value, or current-date bucket as a sole key.
- Prefer a composite key combining residency region, tenant, project, and a stable hash suffix only where measurement shows a simpler key produces unacceptable skew.
- Record the split threshold, the merge threshold, and the per-tenant share above which a tenant is moved to its own partition.

**Partition Key Selection Properties**:

| Candidate key | Isolation property | Dominant failure mode | Measured rejection trigger |
| :-- | :-- | :-- | :-- |
| Tenant identifier | Strong tenant isolation and locality | One large tenant creates a hot partition | Any tenant above 30 percent of a partition's capacity |
| User identifier | Spreads load within a tenant | Complicates project-wide transactions | Cross-partition transaction rate above 5 percent of writes |
| Project identifier | Co-locates collaborating agents | Skew where projects differ by orders of magnitude | Top project above 40 percent of partition bytes |
| Entity or topic identifier | Co-locates graph neighbourhoods | Popular entities become hotspots | Top entity above 10 percent of partition request rate |
| Time bucket | Accelerates append-heavy episodes | Newest bucket is hot; long-range retrieval scatters | Newest bucket above 60 percent of write rate |
| Composite with hash suffix | Bounded skew under measured load | Range scans require fan-out | Fan-out above 8 partitions for a common query |

**Required Outputs**:

- A selected partition key per memory class with the skew measurement supporting it.
- A skew report naming the hottest logical partition and its share of tested capacity.
- A split, merge, and tenant-promotion threshold set expressed numerically.

**Quality Checkpoints**:

- The worst expected logical partition remains below 70 percent of tested sustained capacity while one replica is lost.
- No memory class uses a single globally popular identifier or a current-date bucket as its sole partition key.
- Every threshold in the record is a number rather than a qualitative description.

***

#### Step 2.2: Bind Placement to Residency and Isolation Invariants

**Required Actions**:

- Resolve the residency region for every record from a trusted tenant policy service, never from a caller-supplied header or an agent-supplied argument.
- Pin canonical bytes, derived indexes, change logs, backups, and encryption keys to the jurisdictions the policy permits, and block replication and recovery destinations that would violate it.
- Select the isolation model per tenant population: a shared store with mandatory tenant keys and enforced row-level policy for many small tenants on a uniform schema; a schema boundary for moderate isolation at manageable tenant counts; a dedicated store or cluster for contractual isolation, custom residency, or high-value tenants.
- Verify enforcement below the layer that constructs queries, testing through the real application role, and forbid owner or superuser credentials on any request path because such roles commonly bypass row-level policy.
- Co-locate each canonical record with its version, provenance, authorization label, deletion state, and outbox row, and require every derivative to carry canonical identity, canonical version, content hash, model or analyzer version, schema version, tenant, residency region, and generation identity.

**Required Outputs**:

- A placement policy per tenant class naming permitted jurisdictions for each artifact type.
- An isolation model selection per tenant population with its enforcement point.
- A derivative metadata contract listing the mandatory co-versioning fields.

**Quality Checkpoints**:

- Every placement decision resolves from policy rather than from request input, and actual replica location is compared against policy continuously.
- Isolation is enforced below query construction; a test using an adversarial tenant identifier through the real application role returns denial.
- Physical co-location of derivatives is optional, but every derivative carries the full co-versioning field set.

***

#### Step 2.3: Define the Reshard Protocol and Partition-Map Epoch

**Required Actions**:

- Carry a partition-map epoch in every request, and require owners to reject any write whose epoch is lower than current rather than accepting it into a former owner.
- Execute resharding as an ordered protocol: copy a snapshot, stream the delta, validate counts and content hashes, briefly quiesce or fence writers, atomically advance the epoch, retain the previous owner read-only, and delete the old copy only after the declared recovery window.
- Bound the quiesce window to 5 seconds and abort the epoch advance where it would exceed that, returning to delta streaming.
- Retain the previous owner read-only for at least 24 hours or one full backup cycle, whichever is longer, so that rollback remains possible.
- Verify count and hash equality between source and destination before advancing the epoch, and treat any mismatch as a blocking defect.

**Required Outputs**:

- A partition-map epoch specification with its rejection rule for stale routes.
- A reshard runbook with its seven ordered stages and their validation gates.
- A rollback retention policy naming the read-only window in hours.

**Quality Checkpoints**:

- A write bearing a stale epoch is rejected with an explicit error rather than written to a former owner.
- The epoch advance occurs only after count and hash validation succeed on the destination.
- Rebalance time remains within the class repair objective; a rebalance projected to exceed it halts and is re-planned at smaller granularity.

***

### Phase 3: Write Path, Replication, and Conflict Detection

**Objective**: Commit every mutation through one canonical boundary, replicate it under declared quorum arithmetic, and detect concurrency mechanically, so that a conflict is a recorded event rather than a silent overwrite.

#### Step 3.1: Commit Canonically With an Outbox and an Idempotency Key

**Required Actions**:

- Designate the transactional store as the sole commit boundary, and write the canonical mutation and its outbox row in the same local transaction.
- Prohibit dual writes from request code to canonical and derived stores; derivative updates are driven only by outbox relay or change capture.
- Attach an idempotency key to every mutation, composed of tenant, operation identity, and logical mutation kind, and deduplicate on that composite rather than on a content hash alone, because two intentional identical observations are distinct records.
- Partition change events by the smallest key requiring order, normally tenant plus canonical identity or tenant plus project, and record that ordering holds per partition and not globally.
- Require every consumer to be idempotent, and define exactly-once effect as deduplication plus a conditional state transition at the sink keyed by operation identity and canonical version.

**Required Outputs**:

- A canonical commit specification naming the single transactional boundary.
- An idempotency key composition rule and its deduplication scope.
- An ordering key assignment per event stream with its stated ordering scope.

**Quality Checkpoints**:

- No request path writes directly to a derived store; every derivative mutation traces to an outbox row.
- Replaying any event stream twice produces no duplicate materialisation at any sink.
- Every event carries an ordering key, and no design claims global ordering from a per-partition guarantee.

***

#### Step 3.2: Configure Replication Topology and Quorum Arithmetic

**Required Actions**:

- Select the replication topology per memory class: leader-follower for a single write order and simple conflict avoidance; leaderless quorum where write availability across replicas outweighs the cost of reconciliation; multi-leader only where local write latency is a stated requirement and ownership partitioning confines each record to one home region.
- State the replication factor, the write acknowledgement count, and the read response count numerically per class, and record whether read and write sets are required to overlap.
- Record explicitly that overlap of read and write sets is a necessary condition rather than a correctness proof, because sloppy quorums, failed repair, and clock behaviour defeat the arithmetic alone.
- Record whether follower replication is synchronous or asynchronous, and where asynchronous, state the acknowledged-write loss window that a primary failure can expose.
- Confine each record to one home region wherever the topology permits, since unrestricted same-key writes across regions convert every business rule into a conflict-resolution rule.

**Quorum and Replication Declaration Fields**:

```
MEMORY_CLASS:
TOPOLOGY:            leader_follower | leaderless_quorum | multi_leader
REPLICATION_FACTOR:  N
WRITE_ACK_COUNT:     W
READ_RESPONSE_COUNT: R
OVERLAP_REQUIRED:    TRUE IF R + W > N
FOLLOWER_MODE:       synchronous | asynchronous
ACK_LOSS_WINDOW_MS:  numeric, 0 where synchronous
HOME_REGION_RULE:    per_record | per_tenant | none
MINORITY_BEHAVIOUR:  refuse_writes | accept_and_reconcile
```

**Required Outputs**:

- A replication declaration per memory class carrying every field of the declaration block.
- A stated acknowledged-write loss window per asynchronously replicated class.
- A home-region assignment rule for every class permitting writes in more than one region.

**Quality Checkpoints**:

- Replication factor, write acknowledgement count, and read response count are numbers rather than product default names.
- Every asynchronously replicated class states a non-zero loss window and names the operations forbidden to depend on it.
- No class permits unrestricted same-key writes in two regions without a declared conflict policy in Phase 5.

***

#### Step 3.3: Detect Concurrency With Version Vectors and Reject Unsafe Ordering

**Required Actions**:

- Attach a version vector or equivalent causal metadata to every canonical record, and compare vectors on write to determine whether the incoming version descends from the stored version or is concurrent with it.
- Record the comparison outcome as one of three values: descends, is descended from, or concurrent, and treat only the third as a conflict.
- Store causal parents, logical clock value, and writer region alongside every version so that the comparison is reproducible after the fact.
- Prohibit inference of semantic precedence from wall-clock recency, and disable timestamp-based resolution entirely whenever time-synchronisation telemetry reports offset above 250 milliseconds across replicas.
- Where last-writer-wins is chosen for a field, name it in the declaration as a data-losing rule, restrict it to genuinely replaceable hints such as a recomputable access time, and prohibit it for truth, consent, ownership, deletion state, and any field gating an action.

**Required Outputs**:

- A causal metadata schema attached to every canonical record.
- A per-field resolution rule set naming any field governed by last-writer-wins and the data loss it accepts.
- A conflict event record emitted for every concurrent pair detected.

**Quality Checkpoints**:

- Concurrency is determined by vector comparison in every case; no path determines it from timestamps.
- No field carrying truth, consent, ownership, deletion state, or action authorization is governed by last-writer-wins.
- Every detected conflict emits an event carrying both parent version identities before any resolution is attempted.

***

### Phase 4: Read Path, Staleness Bounds, and Declared Degradation

**Objective**: Serve every read against its declared model, measure the staleness it actually carried, and label or refuse any response that exceeds its budget, so that an agent never treats stale memory as current.

#### Step 4.1: Route Reads Against the Consistency Token

**Required Actions**:

- Require the consistency token on every read in a session that has written the same memory class, and reject a session-consistent read presented without one.
- Compare the token's required log position against each candidate replica's observed log position, and admit only replicas at or beyond it.
- Route to the leader where no follower satisfies the token, and return an explicit failure where the leader is also unreachable, naming the unmet guarantee rather than serving a lagging replica.
- Return observed version, source replica, and replica lag in milliseconds on every read of a replicated class, so that the caller can evaluate the response rather than trusting it.
- Cap hedged reads at 5 percent of read volume, issue them only for idempotent reads after a delay near the historical p95, and never hedge a write.

**Required Outputs**:

- A read-routing implementation enforcing the three ordered outcomes from Step 1.3.
- A response envelope carrying observed version, source replica, and replica lag.
- A hedging policy with its rate cap and its delay trigger.

**Quality Checkpoints**:

- No session-consistent read is served by a replica whose observed log position is below the token's required position.
- Every replicated-class response carries observed version, source replica, and lag; responses lacking them are treated as protocol defects.
- Hedge rate remains at or below 5 percent of read volume; a higher rate halts hedging and triggers latency investigation.

***

#### Step 4.2: Enforce the Staleness Budget and Label Degraded Reads

**Required Actions**:

- Compute staleness per read as the difference between the canonical commit position and the serving replica's observed position, expressed in milliseconds, rather than estimating it from a periodic lag gauge.
- Compare the computed staleness against the class budget declared in Step 1.2, and take one of three actions: return the response unlabelled where staleness is within budget; return it with an explicit degraded marker and its measured staleness where the class permits labelled continuation; refuse the read where the class declares a 0 millisecond budget.
- Require any agent receiving a degraded marker to revalidate against the canonical record before using the value to authorise an action, and to record the revalidation outcome.
- Alert on any stale read above the operation's budget, and treat a stale-read rate above 1 percent of reads in a class as a replication defect requiring investigation within one business day.
- Prohibit caching of authorization, consent, erasure status, and ownership at every layer, and keep negative-cache lifetimes shorter than positive ones during creation-heavy workloads.

**Required Outputs**:

- A staleness computation implemented at the point of decision rather than from a periodic gauge.
- A three-way response disposition rule per class: unlabelled, labelled degraded, or refused.
- A stale-read metric segmented by class, region, and replica.

**Quality Checkpoints**:

- Every read of a bounded-stale class carries a measured staleness value; an unmeasured read is a logging defect.
- No response exceeding its class budget is returned without a degraded marker or a refusal.
- Stale-read rate per class remains at or below 1 percent; a higher rate halts promotion of the configuration.

***

#### Step 4.3: Declare Degradation Behaviour for Every Dependency Failure

**Required Actions**:

- State, per dependency, what the read path does when that dependency is unavailable, before the failure occurs rather than during it.
- Fall back from vector retrieval to lexical retrieval or recent canonical memory, labelling recall as degraded; fall back from lexical retrieval to vector retrieval plus canonical validation.
- Serve only clearly labelled cached low-risk reads where canonical state is unavailable, and prohibit writes and irreversible actions for the duration.
- Permit canonical writes to continue while the change log is unavailable only while outbox capacity remains bounded, and halt writes when the outbox exceeds 80 percent of its provisioned depth.
- Fail closed where authorization or deletion status cannot be evaluated, returning denial rather than a permissive default.
- Give every network call a deadline shorter than its caller's remaining deadline, retry only transient errors on idempotent operations or under the same idempotency key, apply randomised exponential backoff with a retry budget, and open circuit breakers per dependency and tenant rather than globally.

**Required Outputs**:

- A degradation matrix naming, per dependency, the fallback, the label applied, and the operations prohibited.
- A deadline and retry-budget specification per call path.
- A circuit-breaker scope declaration at dependency and tenant granularity.

**Quality Checkpoints**:

- Every dependency in the read path has a declared degradation behaviour; an undeclared dependency halts release.
- Authorization and deletion-status evaluation failures return denial in every path.
- No retry policy is unbounded; every retry path carries a budget and randomised backoff.

***

### Phase 5: Conflict Resolution and Semantic Merge

**Objective**: Resolve every detected conflict through a deterministic ladder that preserves both parents, admitting a model-proposed merge only where no mechanical rule decides and only under deterministic validation.

#### Step 5.1: Apply the Deterministic Resolution Ladder

**Required Actions**:

- Determine the causal relationship first; where one version causally supersedes the other under an authorized domain rule, mark the older assertion superseded and stop.
- Where the versions are concurrent, retain both as disputed and proceed down the ladder rather than selecting one.
- Apply a convergent replicated data type where the field's mutation genuinely fits the type's algebra, such as grow-only observation sets, add and remove sets with defined semantics, counters, and collaboratively edited text, and record convergence as achieved.
- Apply a versioned deterministic resolver where the field is governed by source authority, evidence quality, valid time, scope, or policy, and record the resolver version and its inputs alongside the outcome.
- Escalate to Step 5.2 only where the conflicting field is natural-language content, no convergent type applies, and no deterministic resolver rule decides.
- Route to human review without a model proposal where the conflict touches safety, consent, ownership, deletion state, or an action authorization, regardless of content type.

**Resolution Ladder Ordering**:

```
CONFLICT DETECTED (concurrent under version-vector comparison)
STEP 1: causal_supersession_rule_applies?
        YES -> mark older superseded; record; STOP
STEP 2: field_governed_by_convergent_type?
        YES -> merge by type algebra; record convergence; STOP
STEP 3: deterministic_resolver_rule_decides?
        YES -> apply resolver; record version and inputs; STOP
STEP 4: conflict_touches_safety_consent_ownership_deletion_or_authorization?
        YES -> escalate to human review; preserve both; STOP
STEP 5: field_is_natural_language_and_no_rule_decides?
        YES -> proceed to model-proposed semantic merge (Step 5.2)
        NO  -> escalate to human review; preserve both
```

**Required Outputs**:

- A resolution outcome per conflict naming which ladder step decided it.
- A disputed-version record for every conflict not decided at step 1.
- An escalation queue entry for every conflict routed to human review.

**Quality Checkpoints**:

- No conflict skips a ladder step; the deciding step is recorded for every resolution.
- No conflict touching safety, consent, ownership, deletion state, or authorization reaches a model proposal.
- Both parent versions remain retrievable after every resolution, including those resolved at step 1.

***

#### Step 5.2: Commission a Model-Proposed Semantic Merge

**Required Actions**:

- Supply the model with both parent values, their causal metadata, their provenance, their valid-time intervals, and the field-level scope of the conflict, and with nothing outside that scope.
- Require the proposal to state the merged value, the reasoning category applied, and an explicit list of assertions taken from each parent, so that provenance coverage is checkable.
- Require the model to return a no-merge verdict where the two parents are contradictory rather than complementary, and treat a no-merge verdict as a valid and expected outcome rather than a failure.
- Prohibit the model from deciding whether the versions were concurrent, which parent is authoritative, whether a policy permits the merge, or whether the merged value may be committed.
- Cap merge proposals at 1 per conflict per resolution attempt and at 3 attempts per conflict, escalating to human review on the fourth.

**Required Outputs**:

- A merge proposal carrying the merged value, the assertion-to-parent mapping, and a no-merge verdict where applicable.
- A proposal attempt counter per conflict.
- An escalation record for every conflict exceeding 3 proposal attempts.

**Quality Checkpoints**:

- Every proposal maps each assertion in the merged value to at least one parent; unmapped assertions cause rejection.
- A no-merge verdict is recorded as an outcome and routed to human review rather than retried with a different prompt.
- No proposal is admitted that alters a field outside the declared conflict scope.

***

#### Step 5.3: Validate, Commit, and Preserve Both Parents

**Required Actions**:

- Validate every proposal deterministically against schema, length bounds, provenance coverage, prohibited-content rules, and the declared conflict scope, and reject the proposal on any failure.
- Write the accepted merge as a new version linked to both parent versions, never as a mutation of either parent.
- Preserve both parent versions unmodified and retrievable, with their provenance, evidence references, valid-time intervals, and status, for at least the retention period of the merged record.
- Record the conflict identity, the resolution policy version, the resolver or model identity, the action taken, the winning version, the preserved losing versions, and the resolution latency.
- Publish the resolution as a new claim rather than deleting history, and mark both parents superseded-by rather than removing them.

**Required Outputs**:

- A merged version record linked to both parents.
- Two preserved parent records with intact provenance.
- A conflict resolution log entry carrying policy version, resolver identity, action, and latency.

**Quality Checkpoints**:

- No parent version is mutated or deleted by a merge; parent retrieval succeeds after resolution in 100 percent of sampled cases.
- Provenance for both parents survives the merge and is reachable from the merged record.
- The deterministic validator holds authority; no proposal rejected by it is committed by any path.

***

### Phase 6: Partition Handling, Reconciliation, and Verification

**Objective**: Detect a partition mechanically, fence writers that must not proceed, reconcile divergent histories after healing, and prove the declared contract holds under injected fault before the configuration is promoted.

#### Step 6.1: Detect the Partition and Fence Non-Quorate Writers

**Required Actions**:

- Detect loss of quorum from replica acknowledgement counts, leader term changes, and failure-detector timeouts rather than from an inference over request latency.
- Declare a partition where a replication group cannot assemble its declared write acknowledgement count for longer than 3 consecutive health intervals, and record the detection timestamp and the observed membership.
- Stop writes immediately in every non-quorate or fenced segment, honouring the class partition behaviour declared in Step 1.2.
- Issue a monotonically increasing fencing token with every leadership or lease change, require it on every protected write, and require every protected resource to reject any token lower than the highest it has observed.
- Preserve both histories where a class declared accept-and-reconcile, and never merge them by wall-clock timestamp.

**Required Outputs**:

- A partition detection record with timestamp, affected group, and observed membership.
- A fencing token issue and rejection log covering every protected resource.
- A preserved-history record per segment for classes admitting divergence.

**Quality Checkpoints**:

- Partition detection derives from acknowledgement counts, terms, and failure detectors; no path infers it from latency alone.
- Every protected resource rejects a stale fencing token; a resource accepting one is a blocking defect.
- No segment continues writing where its class declared refuse-writes under partition.

***

#### Step 6.2: Reconcile Divergent Histories After Healing

**Required Actions**:

- Compare the two histories by version vector to classify every record as identical, causally ordered, or concurrent, and route only the concurrent set to Phase 5.
- Bound the reconciliation batch to 5,000 records per pass, and halt reconciliation and escalate where the concurrent set exceeds 5 percent of records touched during the partition, since that rate indicates a placement or ownership defect rather than incidental concurrency.
- Run continuous reconciliation independent of partition events, comparing canonical versions against derivative versions, re-enqueueing missing work, quarantining impossible version regressions, and measuring orphan age.
- Rebuild a derived index as a complete immutable generation, replay deltas to a watermark, validate quality and counts, then atomically switch a tenant-scoped alias, retaining the previous generation for rollback.
- Require every region to acknowledge readiness against a signed generation manifest before the routing generation advances, and otherwise keep each region routed to its last verified generation.

**Required Outputs**:

- A reconciliation report per pass naming identical, ordered, and concurrent counts.
- An orphan inventory with age distribution per derivative store.
- A generation manifest with per-region acknowledgement status.

**Quality Checkpoints**:

- Concurrent-record rate after a partition remains at or below 5 percent of records touched; a higher rate halts reconciliation and escalates.
- Orphan age at the 99th percentile remains below 900 seconds; a higher value triggers a repair backlog review.
- No routing generation advances while any required region has not acknowledged the manifest.

***

#### Step 6.3: Verify the Declared Contract Under Injected Fault

**Required Actions**:

- Build a history of invocations and completions including unknown outcomes after timeout, and check linearizable surfaces with a linearizability checker and weaker surfaces against their declared model.
- Test the exact client library, retry policy, load balancer, and consistency options that production uses, since a guarantee verified under different client settings is not the guarantee deployed.
- Inject leader loss, follower delay, asymmetric partition, packet loss, duplicate events, consumer rebalance, disk exhaustion, slow object storage, corrupt derivative entries, expired leases, clock offset, key-service denial, and whole-region loss, and assert safety during the fault and convergence after healing.
- Assert four negative properties explicitly under every fault: no cross-tenant read, no acknowledged checkpoint lost, no record resurrected after deletion, and no stale value labelled current.
- Run failover exercises at least quarterly and after every topology change, measuring detection, fencing, promotion, routing convergence, token behaviour, recovery point, recovery time, and safe failback.
- Evaluate end-to-end agent tasks under degraded memory, scoring task completion, factual correctness, prohibited-action rate, latency, and whether the agent disclosed degraded recall.

**Required Outputs**:

- A verification report per memory class naming the model tested, the checker used, and the verdict.
- A fault-injection matrix with the four negative properties asserted per fault.
- A task-level evaluation record under degraded memory conditions.

**Quality Checkpoints**:

- Every class carrying a linearizable or serializable declaration has been checked by a formal checker rather than by inspection.
- All four negative properties hold under every injected fault; any violation blocks promotion.
- Task-level success under degraded memory is measured, because a storage tier can meet its availability objective while agents repeatedly act on stale memory.

***

## III. Implementation Guidance for AI Agents

AI agents operating a distributed memory must follow systematic protocols ensuring that every consistency claim is declared, enforced by a deterministic component, and observable in a log. The following guidance translates the framework above into agent-executable instruction.

### A. Structured Execution Protocol

**Control Plane Components**:

1. **Contract Agent**: Owns the consistency declaration, the session-guarantee statement, and the staleness budget per memory class. It alone may amend a declaration, and every amendment is versioned. It refuses release of any operation lacking a declared model.
2. **Placement Agent**: Owns the partition key selection, the residency policy binding, the partition-map epoch, and the reshard runbook. It rejects any write bearing a stale epoch and holds the skew measurements that justify each key.
3. **Write Path Agent**: Owns the canonical commit boundary, the outbox, idempotency keys, ordering keys, and replication acknowledgement counting. It never writes to a derived store and never accepts a mutation without an idempotency key.
4. **Consistency Enforcement Agent**: Owns consistency-token issue and validation, read routing, staleness computation, and the degraded-response label. It holds authority over every read disposition and may refuse a read no replica can satisfy.
5. **Conflict Agent**: Owns version-vector comparison, the deterministic resolution ladder, the merge validator, and parent preservation. It detects conflicts, decides eligibility for model-proposed merge, and holds authority over every commit decision in Phase 5.
6. **Merge Proposer**: The single model-tier component. It proposes a merged value for a natural-language conflict or returns a no-merge verdict. It never commits, never determines concurrency, and never decides policy eligibility.
7. **Reconciliation Agent**: Owns continuous canonical-to-derivative comparison, orphan detection and quarantine, index generation swaps, partition detection, fencing enforcement, and post-partition reconciliation.

**Tier Enforcement Rule**: The Merge Proposer is the only component permitted to make a model call in the critical path of a memory operation. Every other component listed above is deterministic. A design that introduces a second model-tier component into the write path, the read path, conflict detection, or partition detection must be rejected at review, because it replaces a decidable computation with a probabilistic one and removes the basis for every guarantee this framework declares.

**Workflow Execution Pattern**:

```
STATE: Concurrent_Write_Resolution
INPUTS:
  1. Stored canonical version with version vector and provenance
  2. Incoming version with version vector and provenance
  3. Field-level resolution policy for the memory class
  4. Current partition-map epoch and fencing token
ACTIONS:
  1. Validate epoch and fencing token against current values
  2. Compare version vectors and classify the relationship
  3. Emit a conflict event where the relationship is concurrent
  4. Walk the deterministic resolution ladder in order
  5. Commission a merge proposal only where the ladder reaches step 5
  6. Validate any proposal and commit as a new version linked to both parents
VALIDATION:
  - request_epoch == current_partition_map_epoch
  - fencing_token >= highest_observed_token
  - relationship IN {descends, is_descended_from, concurrent}
  - deciding_ladder_step IS RECORDED
  - both_parent_versions_retrievable == TRUE
  - merged_assertions_mapped_to_parents == TRUE
TRANSITIONS:
  IF relationship != concurrent THEN next_state = Commit_Ordered_Version
  IF ladder_step <= 3 THEN next_state = Commit_Deterministic_Resolution
  IF ladder_step == 4 THEN next_state = Human_Review_Queue
  IF proposal_rejected OR attempts > 3 THEN next_state = Human_Review_Queue
  IF validation_failed THEN next_state = Conflict_Error_Handling
```

**Two-Phase Action Pattern**: Emit the intended resolution with its deciding ladder step, its parent identities, and its policy version without committing it; validate it against the validation block while no version is written; commit only after validation passes, writing the resolution log entry in the same operation as the merged version.

**Approval Gate**: Human authorisation is required before promoting a class from single-region to multi-region writable, before adopting last-writer-wins on any field, before advancing a routing generation that any region has not acknowledged, before relaxing a declared staleness budget, and before reconciling a partition whose concurrent-record rate exceeded 5 percent. Agents halt at these gates rather than proceeding with a recorded warning.

**Context Management Requirements**:

- Hold the consistency declaration, the placement policy, and the partition-map epoch in durable state read at request time, since these outlive any single agent context.
- Carry the consistency token in session state rather than reconstructing it, and treat a lost token as a lost session guarantee that must be reported rather than assumed satisfied.
- Bound conflict-resolution context to both parent versions and their metadata; supplying wider context to the Merge Proposer increases the probability of an out-of-scope edit that the validator must then reject.
- Write a handoff record naming class declarations, open conflicts, outstanding reconciliation batches, and current epoch at every context boundary.

### B. Quality Assurance Checkpoints

**Checkpoint 1: Declaration Completeness (After Phase 1)**

- **Automated Check**: Every operation class carries exactly one declared model; every non-linearizable operation carries a numeric staleness budget; every class states its partition behaviour and its session guarantees.
- **Agent Action on Pass**: Proceed to partitioning and placement.
- **Agent Action on Failure**: Halt release and return the undeclared operations; no agent writes through an undeclared operation.
- **Human Review Trigger**: Any class whose consistency model cannot be stated, or any class assigned eventual consistency without a repair objective.

**Checkpoint 2: Placement Integrity (After Phase 2)**

- **Automated Check**: The worst logical partition remains below 70 percent of tested capacity under one-replica loss; residency resolves from policy in 100 percent of sampled requests; a stale-epoch write is rejected in a synthetic test.
- **Agent Action on Pass**: Proceed to the write path.
- **Agent Action on Failure**: Return to key selection for the failing class only, not for the whole inventory.
- **Human Review Trigger**: Skew unresolvable by any candidate key, or an actual replica location outside the policy jurisdiction.

**Checkpoint 3: Write Path Integrity (After Phase 3)**

- **Automated Check**: No derived-store write originates outside the outbox; replaying a stream twice materialises no duplicate; every canonical record carries causal metadata; no truth, consent, ownership, deletion, or authorization field is governed by last-writer-wins.
- **Agent Action on Pass**: Proceed to the read path.
- **Agent Action on Failure**: Quarantine the affected write path and block its release; other paths continue.
- **Human Review Trigger**: Any proposal to adopt last-writer-wins, or a duplicate materialisation rate above 0.1 percent under replay.

**Checkpoint 4: Read Path Conformance (After Phase 4)**

- **Automated Check**: Stale-read rate per class at or below 1 percent; read-your-writes violations at 0 for every class guaranteeing it; every bounded-stale response carries a measured staleness value; every dependency carries a declared degradation behaviour.
- **Agent Action on Pass**: Proceed to conflict handling.
- **Agent Action on Failure**: Halt promotion of the configuration and return the violating class with its measured rate.
- **Human Review Trigger**: Any read-your-writes violation in a class guaranteeing it, or a stale-read rate above 5 percent.

**Checkpoint 5: Resolution Integrity (After Phase 5)**

- **Automated Check**: Both parents retrievable after 100 percent of sampled resolutions; deciding ladder step recorded for every conflict; no safety, consent, ownership, deletion, or authorization conflict reached a model proposal; every merged assertion maps to a parent.
- **Agent Action on Pass**: Release the resolution batch.
- **Agent Action on Failure**: Roll the batch back to disputed state and preserve both parents; a resolution failing validation is never released with a warning.
- **Human Review Trigger**: Any lost parent version, or unresolved-conflict count above 100 in one class.

**Checkpoint 6: Partition and Verification Readiness (After Phase 6)**

- **Automated Check**: All four negative properties hold under every injected fault; every linearizable class checked by a formal checker; failover exercise completed within the quarter; concurrent-record rate after the last partition at or below 5 percent.
- **Agent Action on Pass**: Permit promotion of the configuration.
- **Agent Action on Failure**: Withhold promotion and name the unmet property; clean-condition results alone never promote a configuration.
- **Human Review Trigger**: Any cross-tenant read, any lost acknowledged checkpoint, any resurrection after deletion, or any stale value labelled current.

**Checkpoint Documentation Template**:

```
CHECKPOINT_ID:
CHECKPOINT_NAME:
PHASE_BOUNDARY:
MEMORY_CLASS:
VALIDATION_CRITERIA:
MEASURED_VALUE:
PASS_CONDITION:
PASS_ACTION:
FAIL_ACTION:
HUMAN_REVIEW_TRIGGER:
RESPONSIBLE_COMPONENT:
```

### C. Error Handling and Troubleshooting

**Error Type 1: Concurrent Write to One Record From Two Agents**

- **Symptoms**: Version-vector comparison returns concurrent for a record pair; two agents report success on mutations that cannot both be reflected in the stored value; a field's value alternates between two stable states across successive reads.
- **Diagnostic Steps**: Confirm concurrency by vector comparison rather than by timestamp; identify whether the two writers share a home region, which indicates a routing defect rather than genuine geographic concurrency; determine whether the conflicting field is governed by a convergent type, a deterministic resolver, or neither; check whether the record's ownership rule confines it to one write region.
- **Resolution Protocol**: Option A, where a causal supersession rule applies, mark the older assertion superseded and record the deciding rule. Option B, where the field fits a convergent type's algebra, merge by that algebra and record convergence. Option C, where a versioned deterministic resolver decides on source authority, evidence quality, valid time, or scope, apply it and record its inputs. Option D, where the field is natural-language content and no rule decides, commission a model-proposed merge under Step 5.2 and commit only through the deterministic validator. Option E, where the conflict touches safety, consent, ownership, deletion state, or authorization, escalate to human review with both parents attached and no proposal.
- **Escalation Trigger**: Conflict rate above 2 percent of writes in a memory class halts writes to that class and escalates, because that rate indicates a partitioning or ownership defect rather than incidental concurrency. Unresolved-conflict count above 100 in one class escalates regardless of rate. This class is never resolved by retrying the write.

**Error Type 2: Read-Your-Own-Writes Violation**

- **Symptoms**: An agent commits a write, receives an acknowledgement, then issues a read that does not observe it; a task duplicates work it has already recorded; a validation step reports a record absent that the same agent created seconds earlier.
- **Diagnostic Steps**: Confirm the write was acknowledged and recover its commit log position; confirm whether the read carried a consistency token; compare the serving replica's observed log position against the token's required position; determine whether a load balancer, a retry to a different endpoint, or a cache layer bypassed the routing rule.
- **Resolution Protocol**: Option A, restore token propagation on the affected path and re-route the read against the token. Option B, route the class's reads to the leader until follower replay lag returns within budget. Option C, where the token was lost and cannot be reconstructed, return an explicit failure naming the unmet guarantee rather than serving the read. Option D, where a cache layer served the stale value, invalidate the tenant-scoped key set and exclude the class from caching.
- **Escalation Trigger**: Any read-your-writes violation in a class declaring that guarantee escalates on first occurrence, because the guarantee is binary and a single violation falsifies it. More than 3 violations in one class within 24 hours suspends the class's session-consistency claim until the routing defect is corrected.

**Error Type 3: Stale Read Driving Duplicated Work Across Agents**

- **Symptoms**: Two agents produce near-identical artifacts for one task; a second agent begins work a first agent already recorded as claimed; measured staleness on the claim-check read exceeds its class budget; duplicate memory records share a content hash but differ in operation identity.
- **Diagnostic Steps**: Measure staleness at the point of the claim-check read rather than from a periodic gauge; determine whether the claim check was assigned a bounded-stale model when it gates work allocation and therefore requires a linearizable compare-and-set; check whether replica lag exceeded its budget across the whole class or only on one replica.
- **Resolution Protocol**: Option A, reclassify the claim-check operation as a linearizable compare-and-set with a 0 millisecond budget, since an operation that gates work allocation is a checkpoint rather than a discovery read. Option B, remove the lagging replica from the read set until its observed position returns within budget. Option C, deduplicate the produced artifacts on tenant, operation identity, and logical mutation kind, and discard the later duplicate while preserving its provenance. Option D, where duplication is tolerable, label the class explicitly as admitting duplicate work and record the expected rate.
- **Escalation Trigger**: Duplicated-work rate above 1 percent of tasks in a class escalates for consistency reclassification. Stale-read rate above 5 percent in any class halts promotion of the configuration.

**Error Type 4: Split-Brain With Two Writable Partitions**

- **Symptoms**: Two segments each report a leader; fencing tokens from two distinct sequences appear at one resource; after healing, the concurrent-record set is large rather than incidental; acknowledged writes are absent from the surviving history.
- **Diagnostic Steps**: Recover the leader term and ownership epoch observed by each segment; determine which segment held the declared write quorum; enumerate writes acknowledged in the non-quorate segment; measure the concurrent-record rate over records touched during the partition window.
- **Resolution Protocol**: Option A, stop writes in every non-quorate or fenced segment immediately, verify the current term and ownership epoch, preserve both histories, and reconcile semantically through Phase 5. Option B, where a class declared refuse-writes and a segment nonetheless accepted them, treat the accepting path as a fencing defect, quarantine its writes, and repair the resource that failed to reject a stale token. Option C, where reconciliation is not possible within the recovery objective, promote the quorate history, quarantine the divergent history intact, and escalate for adjudication rather than discarding it.
- **Escalation Trigger**: Any acceptance of a write bearing a stale fencing token escalates on first occurrence. A concurrent-record rate above 5 percent of records touched during the partition halts automated reconciliation and escalates. Histories are never merged by wall-clock timestamp under any escalation.

**Error Type 5: Canonical-to-Derivative Divergence and Orphaned Entries**

- **Symptoms**: A derived index returns entries whose canonical record is absent or whose canonical version does not match; orphan age rises across reconciliation passes; a retrieval returns content the canonical store has deleted.
- **Diagnostic Steps**: Compare generation, canonical version, and content hash per entry; determine whether the outbox relay stalled, whether a consumer failed idempotently, or whether a generation swap advanced without regional acknowledgement; measure orphan age distribution rather than orphan count alone.
- **Resolution Protocol**: Option A, quarantine entries whose canonical record or matching version is absent, then repair or delete them from the outbox history. Option B, keep retrieval available from the last verified generation while a complete replacement generation is rebuilt and validated. Option C, where the divergence originates in a stalled relay, drain the outbox with rate limiting to avoid a recovery herd and re-run reconciliation. Option D, where deleted content is reachable through a derivative, deny reads immediately from the global tombstone and treat physical removal as a workflow with per-target completion evidence.
- **Escalation Trigger**: Orphan age at the 99th percentile above 900 seconds escalates for repair-capacity review. Any reachable content whose canonical record carries a tombstone escalates immediately and blocks release, and is never resolved by waiting for the next reconciliation pass.

**Error Type 6: Silent Consistency Downgrade**

- **Symptoms**: Responses report an effective consistency weaker than requested without a reason code; a class's measured staleness rises while its declared budget is unchanged; an operation with no declaration is discovered in production traffic.
- **Diagnostic Steps**: Compare requested against effective consistency across a sampled response set; identify the path that performed the downgrade, distinguishing a router fallback, a client library default, a retry to a different endpoint, and a cache interposition; check whether the operation appears in the declaration inventory at all.
- **Resolution Protocol**: Option A, restore the explicit failure path so that an unsatisfiable read returns an error naming the unmet guarantee rather than a weaker response. Option B, where a client library default caused it, pin the client options to the declared model and re-run verification with the pinned options, since a guarantee verified under different client settings is not the guarantee deployed. Option C, where the operation was undeclared, halt its traffic, assign a model under Step 1.2, and re-release.
- **Escalation Trigger**: Any downgrade returned without a reason code escalates on first occurrence. Discovery of an undeclared operation in production traffic halts that operation immediately and is never resolved by assigning the weakest model that happens to work.

**Troubleshooting Decision Tree**:

```
DISTRIBUTED MEMORY ANOMALY DETECTED
├─ CONCURRENCY DEFECT
│   ├─ Vectors concurrent, rule decides → Apply ladder step; record deciding step
│   ├─ Vectors concurrent, no rule, natural language → Model proposes; validator commits
│   ├─ Vectors concurrent, touches consent or ownership → HALT; human review, both parents kept
│   └─ Conflict rate above 2 percent of writes → HALT writes; escalate placement defect
├─ SESSION GUARANTEE DEFECT
│   ├─ Token absent on read → Restore propagation; fail explicitly meanwhile
│   ├─ No replica at required position → Route to leader; else return explicit failure
│   └─ Cache served pre-write value → Invalidate tenant key set; exclude class from cache
├─ STALENESS DEFECT
│   ├─ Measured staleness above class budget → Label degraded or refuse; never return bare
│   ├─ Claim check gating work is bounded-stale → Reclassify as linearizable compare-and-set
│   └─ Stale-read rate above 5 percent → HALT promotion; investigate replication
├─ PARTITION DEFECT
│   ├─ Quorum lost 3 intervals → Declare partition; fence non-quorate writers
│   ├─ Stale fencing token accepted → HALT; repair resource; quarantine its writes
│   └─ Concurrent rate above 5 percent after healing → HALT reconciliation; escalate
├─ DERIVATIVE DEFECT
│   ├─ Canonical version mismatch → Quarantine entry; rebuild generation; keep last verified
│   ├─ Tombstoned content reachable → HALT release; deny reads; run deletion workflow
│   └─ Orphan p99 age above 900 s → Escalate repair capacity review
└─ DECLARATION DEFECT
    ├─ Downgrade without reason code → HALT; restore explicit failure path
    └─ Operation undeclared in production → HALT operation; assign model; re-release
```

### D. Performance Metrics and Continuous Learning

**Consistency and Correctness Metrics**:

- **Read-your-writes violation count**: Reads failing to observe the session's own acknowledged write, per class guaranteeing it (target: 0; any occurrence escalates).
- **Stale-read rate**: Reads whose measured staleness exceeded the class budget over total reads (target: no more than 1 percent; above 5 percent halts promotion).
- **Staleness distribution**: Measured staleness at p50, p95, and p99 per class, region, and replica (target: p99 within the declared budget).
- **Conflict rate**: Writes detected as concurrent over total writes per class (target: no more than 2 percent; above that halts writes to the class).
- **Unresolved conflict count**: Conflicts held disputed beyond one resolution cycle (target: no more than 100 per class).
- **Suspected lost-write rate**: Acknowledged writes absent from the surviving history after a failover (target: 0 for synchronously replicated classes).

**Convergence and Repair Metrics**:

- **Replica lag distribution**: Observed lag in milliseconds and bytes at p50, p95, and p99, recorded at the moment of each decision rather than from a periodic gauge (target: p99 within the class staleness budget).
- **Derivative convergence time**: Interval from canonical commit to matching derivative version (target: within the class budget at p99).
- **Orphan rate and age**: Derivative entries lacking a matching canonical version, with age distribution (target: p99 age below 900 seconds).
- **Duplicate suppression rate**: Duplicate deliveries absorbed by idempotency keys over total deliveries, reported alongside duplicate materialisation rate (target: materialisation at or below 0.1 percent).
- **Reconciliation backlog age**: Age of the oldest outstanding reconciliation batch (target: below one repair cycle).
- **Deletion completion time**: Interval from tombstone write to per-target completion evidence, with outstanding-region count (target: within the declared deletion objective).

**Merge Quality Metrics**:

- **Merge proposal acceptance rate**: Proposals passing deterministic validation over proposals made (target: at least 70 percent; below 50 percent indicates the conflict scope supplied is too wide).
- **Out-of-scope edit rate**: Proposals altering a field outside the declared conflict scope (target: no more than 5 percent; every such proposal is rejected regardless).
- **Parent preservation rate**: Resolutions after which both parents remain retrievable (target: 100 percent; any shortfall is a blocking defect).
- **Human escalation rate on merges**: Conflicts routed to human review over conflicts detected (target: reported rather than minimised, since suppressing it trades safety for throughput).

**Learning and Adaptation Mechanisms**:

- **Budget recalibration**: Recompute every staleness budget per class against observed decision outcomes each quarter; the values in Step 1.2 are deployment defaults rather than measured constants.
- **Key re-selection on skew drift**: Re-run the skew measurement whenever the hottest partition crosses 60 percent of tested capacity, ahead of the 70 percent split threshold, so that resharding is planned rather than reactive.
- **Resolver versioning**: Version every deterministic resolver and record its identity with each resolution, so that a policy change is distinguishable from a behaviour regression in later analysis.
- **Component removal**: Remove any distributed component whose measured benefit has fallen below the 25 percent margin that justified its introduction, since the simplest architecture meeting the declared contract is the most reliable one to operate.

**Human-in-the-Loop Boundaries**: Adoption of last-writer-wins on any field, relaxation of a declared staleness budget, promotion of a class to multi-region writable, adjudication of a conflict touching safety, consent, ownership, deletion state, or authorization, and acceptance of a divergent history after split-brain are never automated.

***

## IV. Domain-Agnostic Application Guidance

This framework generalises across sectors because it governs the contract between a write and a subsequent read rather than the content of any particular memory. Its phases hold wherever more than one agent, process, or node reads and writes one logical memory and a partial failure is possible.

### 4.1 Cross-Domain Application Patterns

**Clinical and care coordination systems**: Ownership, consent, and current medication state take linearizable treatment with a 0 millisecond budget, because an agent acting on a revoked consent causes harm that no later reconciliation repairs. Residency binds to jurisdiction at the record level and blocks any recovery destination outside it. Concurrent notes from two clinicians are natural-language conflicts eligible for a proposed merge, but every merge preserves both parents because the clinical record is the evidence trail; a merged value that obscures which clinician asserted what is a defect even where it reads well. Discovery over historical episodes tolerates a 60 second budget.

**Financial operations and reconciliation**: Balance, entitlement, and settlement state take serializable treatment and refuse writes under partition, since a divergent balance accepted in two segments creates an obligation the institution cannot honour. Last-writer-wins is prohibited on every field in this domain without exception. Reconciliation runs continuously rather than on a schedule, and the deletion workflow must produce per-target completion evidence because retention obligations and erasure obligations coexist and neither may be inferred.

**Industrial and field operations**: Connectivity is intermittent by nature, so classes admitting local writes under partition are the norm rather than the exception, and ownership partitioning confines each asset's memory to one home site. Observation sets and counters fit convergent types cleanly and merge without proposals. Command state does not: a dispatched instruction is irreversible in the physical world, so it takes a linearizable checkpoint and pauses rather than reconstructing from a stale replica. Reconciliation on reconnection is a bounded batch with an escalation trigger, not an unbounded catch-up.

**Software engineering agent fleets**: Many agents write to one shared project memory, and the dominant failure is duplicated work from a stale claim check rather than data loss. The claim check is therefore a linearizable compare-and-set, not a bounded-stale read, and the framework's Error Type 3 governs it. Derived code indexes and embeddings are regenerable and tolerate a 60 second budget. Concurrent design notes are the canonical case for proposed merge, and the validator's out-of-scope edit check is the control that keeps a merge from silently rewriting a decision record.

**Public-sector case handling and records**: Auditability outranks latency. Every resolution records its deciding ladder step, its policy version, and both parents, because the reconstruction of why a record changed is itself a deliverable. Residency and isolation are contractual rather than architectural preferences, so a dedicated store per jurisdiction is often the correct isolation model despite its provisioning cost. Discovery reads tolerate generous budgets; status transitions do not.

**Research and scientific record systems**: Claims are bitemporal by nature, since when a finding is true in the world and when the platform learned it are distinct and both are queried. Concurrent claims from independent sources are preserved as disputed rather than resolved, because disagreement is data. A proposed merge is appropriate for two descriptions of one observation and inappropriate for two contradictory findings, and the resolution ladder's step 4 test is what separates them.

### 4.2 Scale, Risk, and Topology Adaptation

- **Single-node deployments**: Retain the consistency declaration and the session-guarantee statement even where one process holds all state, because the declaration is what makes a later distribution decision auditable. Collapse Phases 2, 3, and 6 to their declaration outputs and retain Phases 1, 4, and 5 in full. A single-node system still faces concurrent writes from two agents and still needs the resolution ladder.
- **Single-region multi-node deployments**: Apply every phase. Multi-leader topology is unnecessary, so conflicts arise only from application-level concurrency rather than from replication, and the conflict rate should sit well below the 2 percent trigger. A rate near that trigger in a single-region deployment indicates an ownership defect rather than a distribution property.
- **Multi-region active-passive deployments**: One write authority remains, and failback is a migration rather than a control. Measure replay lag continuously, test promotion quarterly, and never describe cross-region backups as active-active. Recovery point and recovery time are declared separately per memory class, since checkpoints and deletion ledgers may require near-zero recovery point while regenerable derivatives tolerate hours.
- **Multi-region active-active deployments**: Justified only where local write latency or regional autonomy is a stated requirement. Partition ownership so that each tenant or entity has exactly one write region; unrestricted same-key writes convert every business rule into a conflict-resolution rule and raise the conflict rate past what any resolution ladder handles economically. Promotion to this topology sits behind the approval gate.
- **High-risk and irreversible-action domains**: Tighten every budget toward 0 milliseconds for state gating an action, prefer refusal over labelled continuation under partition, and require both parents plus human adjudication for every conflict rather than only for the named categories. Abstention from an action is preferable to acting on memory whose currency cannot be established.
- **Latency-constrained deployments**: Shorten the replication path rather than weakening the declaration. Where a cross-region quorum cannot meet the deadline, move the record's home region rather than downgrading its consistency model, since a downgrade removes a guarantee while a placement change preserves it.

***

## V. Limitations and Considerations

**Thresholds here are deployment defaults, not measured constants**: The 70 percent partition capacity threshold, the 2 percent conflict rate, the 1 percent stale-read rate, the 5 percent post-partition concurrent rate, the 900 second orphan age, and the staleness budgets in Step 1.2 were chosen to be operable on first deployment rather than derived from a universal property of distributed systems. The consequence is that a deployment adopting them uncritically may halt on a rate that is normal for its workload or tolerate one that is not. The mitigation is the recalibration requirement in Section III.D, which obliges each deployment to recompute every threshold per memory class against observed outcomes each quarter and to record the recomputed value alongside the default it replaced.

**Quorum arithmetic is a necessary condition, not a correctness proof**: Requiring read and write sets to overlap does not by itself guarantee that a read observes the latest acknowledged write, because sloppy quorums, failed read repair, clock behaviour, and implementation detail each defeat the arithmetic. The consequence is that a system satisfying the formula can still return stale data while reporting a strong configuration. The mitigation is Step 6.3, which requires verification against a formal checker using the exact client library, retry policy, and consistency options that production uses, rather than acceptance of the arithmetic as evidence.

**A proposed semantic merge can be fluent and wrong**: A model reconciling two natural-language versions produces a value that reads as coherent whether or not it preserves both parents' meaning, and fluency is not evidence of fidelity. The consequence is that an unvalidated merge can quietly replace two accurate records with one plausible fabrication. The mitigation is the hybrid-tier contract in Section 1.3 and Step 5.3: the assertion-to-parent mapping is checked mechanically, out-of-scope edits are rejected, both parents survive unmodified and retrievable, and the deterministic validator holds authority in every disagreement.

**Conflict detection is decidable but conflict materiality is not**: Version-vector comparison establishes that two versions are concurrent without establishing whether the difference matters. The consequence is that a system can generate a high volume of conflicts that are semantically identical, consuming resolution capacity and masking the conflicts that do matter. The mitigation is the resolution ladder's early steps, which absorb convergent-type and resolver-decidable conflicts before any proposal is commissioned, and the merge acceptance-rate metric, which exposes an over-wide conflict scope.

**Last-writer-wins loses data whenever it is used**: Where a deployment adopts it, information is discarded by construction, and clock skew, late-arriving retries, and a later timestamp representing older knowledge each make the discard arbitrary rather than merely lossy. The consequence is silent, unrecoverable loss that no metric detects after the fact. The mitigation is the prohibition in Step 3.3 restricting it to genuinely replaceable hints, the approval gate requiring human authorisation for its adoption on any field, and the naming requirement that forces the accepted loss into the declaration rather than leaving it implicit.

**Verification cost grows faster than the topology**: Fault injection across leader loss, delay, asymmetric partition, packet loss, duplicate delivery, rebalance, storage exhaustion, corruption, lease expiry, clock offset, key-service denial, and region loss multiplies with each added region and store. The consequence is that deployments under schedule pressure verify the clean path and promote on that evidence. The mitigation is Checkpoint 6, which withholds promotion where any of the four negative properties is unasserted under any injected fault, and the explicit statement that clean-condition results alone never promote a configuration.

**A healthy storage tier does not imply correct agent behaviour**: Every metric in this guide can sit within target while agents repeatedly act on memory that is technically within budget and substantively out of date. The consequence is a system that reports availability while producing wrong work. The mitigation is the task-level evaluation in Step 6.3, which scores completion, factual correctness, prohibited-action rate, and whether the agent disclosed degraded recall, and which is the final acceptance criterion rather than a supplementary one.

**Distribution decisions are rarely reversed once made**: Each added region, store, and replication path acquires dependents, and removal is treated as a risk even where its benefit has lapsed. The consequence is architectures that accumulate components no measurement still justifies. The mitigation is the component-removal rule in Section III.D, which requires a distributed component whose measured benefit falls below its 25 percent introduction margin to be removed at the next review rather than retained by default.

***

## VI. Conclusion and Summary

Distributed agent memory is a declaration discipline before it is a storage problem. Every system in which more than one agent reads and writes one logical memory already has a consistency model; the only question is whether it was chosen at design time or discovered during an incident, and a model discovered during an incident is invariably the weakest one the components permitted. The framework above exists to force the choice forward: a declared model per operation, a numeric staleness budget per class, a stated partition behaviour, an enforced session guarantee, and a resolution rule that names what it discards.

The tier partition is what keeps that declaration honest. Replication, quorum arithmetic, version-vector comparison, partition detection, and conflict detection are decidable computations with exact answers, and a system that routes any of them to a model has traded a guarantee for a probability while retaining the language of a guarantee. The model tier has one legitimate load-bearing role, which is to propose a reconciled value where two natural-language versions conflict and no mechanical rule decides. That proposal is admitted only through a deterministic validator, records both parents, and preserves provenance for each, so that a merge adds a version rather than destroying two.

A team introducing distributed memory should distribute last rather than first. Prove the requirement against a measured single-region design, declare consistency per operation before any agent writes, implement the smallest topology that satisfies the declaration, verify it under injected fault with the exact client options production uses, and add a region only when the documented requirement survives that verification. Components are cheap to add and expensive to remove, and the simplest architecture that meets the declared contract is the most reliable one to operate.

**Key Success Factors**:

- **Declaration before traffic**: Every operation carries a consistency model, a numeric staleness budget, and a stated partition behaviour before any agent writes through it, so the contract is chosen rather than inherited.
- **One canonical record**: Exactly one representation is authoritative and every other is a regenerable derivative carrying canonical identity and version, so no index quietly becomes truth.
- **Deterministic detection, deterministic authority**: Concurrency, quorum, partition, and conflict are decided by mechanical comparison, and the deterministic component holds authority in every disagreement with a model proposal.
- **Session guarantees enforced, not hoped for**: A consistency token routes each read to a replica that has applied the session's own writes, and an unsatisfiable read fails explicitly rather than being served stale.
- **Both parents survive every merge**: No resolution mutates or deletes a parent version, provenance for each survives, and the deciding ladder step is recorded for audit.
- **Numeric triggers with stated consequences**: Conflict rate, stale-read rate, orphan age, partition concurrency, and skew each carry a threshold and a named halt, escalation, or reclassification action.

By following this guide, AI agents can operate a memory spread across failure domains in which what a read is guaranteed to return is stated in advance, a conflict is a recorded event with both versions preserved, and a partition produces a declared behaviour rather than a discovered one.

***

## VII. References and Further Reading

This guide is an operational restructuring of a single prose source. The corpus pointers below identify that source and the sibling guides bearing on particular phases. The external references that follow are transcribed from the originating prose guide as it cited them; they were not independently re-verified in the course of this conversion, and their titles and locations are reproduced rather than checked. Three areas were confirmed against independent retrieval during conversion and are noted where they appear: the standing of version vectors over timestamp-based resolution, the role of fencing tokens and monotonic epochs in split-brain prevention, and the observation that convergent replicated types eliminate mechanical merge failure while leaving a residue of semantic conflict that no algebra resolves.

**Corpus pointers**:

- `Distributed Memory Architectures for AI Agents: A Production Guide` — the originating prose guide from which this operational guide was derived. Source of the distribution gate, the consistency and staleness budgets by memory class, the partitioning and placement rules, the replication and conflict material, the truth-maintenance schema, the heterogeneous-store coordination rules, the failure catalogue, the metadata and logging contract, the verification programme, and the operational workflow. It carries inline citations to primary literature and vendor documentation on consistency models, consensus, replication, conflict-free replicated data types, change capture, durable execution, and reliability engineering; the external references listed below are transcribed from those citations.
- `advanced_task_guides/authoring/guide_guidewriting.md` — the normative house-style specification. Source of the archetype, the step slot template, the mandatory Implementation Guidance subsection names, and the conformance envelope this guide was written against.
- `advanced_task_guides/memory-management/guide_AgentMemoryManagement.md` — companion guidance on the memory lifecycle, applicable to the class inventory in Step 1.1 and to the operations whose consistency this guide declares.
- `advanced_task_guides/memory-management/guide_HierarchicalMemory.md` — companion guidance on memory tiering. Tiering determines what is stored at which level and does not determine replication or consistency, which remain this guide's subject; the two are composed by declaring a consistency model per tier.
- `advanced_task_guides/memory-management/guide_StructuredMemory.md` — companion guidance on structured record design, applicable to the canonical schema and the causal metadata fields in Step 3.3.
- `advanced_task_guides/memory-management/guide_EpisodicMemory.md` — companion guidance on episode capture, applicable to the durable-append and session-consistency assignments in Step 1.2.
- `advanced_task_guides/memory-management/guide_MemoryConsolidation.md` — companion guidance on consolidation, applicable to the derivative regeneration and index generation swaps in Step 6.2.
- `advanced_task_guides/memory-management/guide_MemoryReadWriteOperations.md` — owns the operation contract for a single read and a single write, including gate ordering, idempotency, and the terminal state vocabulary. This guide owns the guarantee that spans operations: what a read is promised after another writer's commit, and what the system does when that promise cannot be met.
- `advanced_task_guides/memory-management/guide_MemoryForgetting.md` — owns retention policy, obligation erasure, and the coverage proof a case requires; applicable wherever an erasure must reach every replica, backup, and reshard destination that the placement rules in Step 2.2 created.
- `advanced_task_guides/design-architecture/guide_TelemetryDesign.md` — companion guidance on event schema design and instrumentation, applicable to the metric derivation in Section III.D.

Transactive memory, which concerns which agent holds which expertise and how work is routed to it, is a separate task family and is deliberately not covered here; this guide specifies only the storage contract such a directory must satisfy, stated in Section 1.4. No corpus guide for that family exists on disk at the time of writing, so none is cited.

**External references**:

*Consistency models, consensus, and session guarantees*

1. MIT, *Perspectives on the CAP Theorem* — https://dspace.mit.edu/handle/1721.1/79112
2. Fischer, Lynch, and Paterson, *Impossibility of Distributed Consensus with One Faulty Process* — https://groups.csail.mit.edu/tds/papers/Lynch/jacm85.pdf
3. Ongaro and Ousterhout, *In Search of an Understandable Consensus Algorithm* — https://raft.github.io/raft.pdf
4. Jepsen, *Consistency Models* — https://jepsen.io/consistency/models/linearizable
5. Terry and colleagues, *Session Guarantees for Weakly Consistent Replicated Data* — https://dl.acm.org/doi/10.1109/ICDCS.1994.302392
6. Google Research, *Spanner: Google's Globally-Distributed Database* — https://research.google/pubs/spanner-googles-globally-distributed-database-2/
7. Lamport, *Time, Clocks, and the Ordering of Events in a Distributed System* — https://lamport.azurewebsites.net/pubs/time-clocks.pdf

*Replication, partitioning, and conflict behaviour*

8. Amazon, *Dynamo: Amazon's Highly Available Key-value Store* — https://www.allthingsdistributed.com/files/amazon-dynamo-sosp2007.pdf
9. Apache Cassandra, *Dynamo-style architecture and tunable consistency* — https://cassandra.apache.org/doc/latest/cassandra/architecture/dynamo.html
10. PostgreSQL, *Table Partitioning* — https://www.postgresql.org/docs/current/ddl-partitioning.html
11. PostgreSQL, *Log-Shipping Standby Servers* — https://www.postgresql.org/docs/current/warm-standby.html
12. PostgreSQL, *Row Security Policies* — https://www.postgresql.org/docs/current/ddl-rowsecurity.html
13. Redis, *Redis Cluster Specification* — https://redis.io/docs/latest/operate/oss_and_stack/reference/cluster-spec/

*Convergent replicated data types*

14. Automerge, *Documentation* — https://automerge.org/docs/
15. Yjs, *Documentation* — https://docs.yjs.dev/

*Change capture, ordering, and durable execution*

16. Debezium, *Outbox Event Router* — https://debezium.io/documentation/reference/stable/transformations/outbox-event-router.html
17. Apache Kafka, *Exactly Once Semantics* — https://cwiki.apache.org/confluence/display/KAFKA/Kafka+Exactly+Once+Semantics
18. Temporal, *Durable Execution documentation* — https://docs.temporal.io/temporal

*Retrieval systems with documented consistency controls*

19. Milvus, *Consistency Level* — https://milvus.io/docs/consistency.md
20. Qdrant, *Distributed Deployment* — https://qdrant.tech/documentation/guides/distributed_deployment/
21. Weaviate, *Replication Architecture and Consistency* — https://docs.weaviate.io/weaviate/concepts/replication-architecture/consistency

*Multi-region operation, deletion, and object replication*

22. Amazon Web Services, *Plan for Disaster Recovery* — https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/plan-for-disaster-recovery-dr.html
23. Amazon Web Services, *What Is and Is Not Replicated in S3* — https://docs.aws.amazon.com/AmazonS3/latest/userguide/replication-what-is-isnot-replicated.html
24. European Union, *General Data Protection Regulation* — https://eur-lex.europa.eu/eli/reg/2016/679/oj

*Operations, reliability, and verification*

25. Google, *Addressing Cascading Failures* — https://sre.google/sre-book/addressing-cascading-failures/
26. Google, *Error Budget Policy* — https://sre.google/workbook/error-budget-policy/
27. OpenTelemetry, *Context Propagation* — https://opentelemetry.io/docs/concepts/context-propagation/
28. *Principles of Chaos Engineering* — https://principlesofchaos.org/
29. Kingsbury and Alvaro, *Elle: Inferring Isolation Anomalies from Experimental Observations* — https://arxiv.org/abs/2003.10554

*Agent-memory research cited by the prose source*

30. *SEDM: Self-Evolving Distributed Memory for multi-agent systems* — https://arxiv.org/abs/2509.09498. The prose source notes that this work evaluates reasoning quality and token overhead rather than partition, replication, isolation, or recovery correctness, and that its systems claims should be treated as research rather than as evidence of those properties.
