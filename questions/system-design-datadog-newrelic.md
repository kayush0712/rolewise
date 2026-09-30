# System Design Interview: Observability Platform (Datadog / New Relic)

---

# PASS 1 — Compressed Full-System Scaffold

## 1. Interview Context

This is a **multi-workload data-platform problem**, not a single-service problem — the candidate must design metrics ingestion, distributed tracing, and alerting as three coupled but distinctly-shaped subsystems (time-series writes, graph-stitching writes, streaming-query reads) under one multi-tenant umbrella. It's a strong L7 problem because there's no single "right" datastore: naive candidates reach for "just use Cassandra for everything" and miss that metrics cardinality explosion, trace-assembly ordering, and alert-evaluation latency each demand different tradeoffs. Hidden challenges: **tag cardinality explosion** (a single bad tag like `user_id` can create billions of unique series), **out-of-order/late-arriving data** at the edge (agent buffering, network partitions), and **the alerting correctness/latency tradeoff** (false negatives on an outage are worse than false positives, but you can't scan raw data per rule per tenant). Likely probe areas: cardinality control, hot partition handling in the TSDB, tail-based trace sampling, and alert engine watermarking.

## 2. Scope Clarification

| Category | Question | Why it matters |
|---|---|---|
| Business | Is this B2B SaaS (customers are companies instrumenting their own infra), single-tenant, or self-hosted? | Determines multi-tenancy and noisy-neighbor design |
| UX | Do users need sub-second dashboard refresh, or is 10-60s acceptable? | Drives whether reads hit raw data or precomputed rollups |
| Scale | How many hosts/containers, how many custom tags per metric, how many total unique time series? | Cardinality is the dominant sizing driver, not raw request volume |
| Reliability | Is losing a few seconds of metrics during a regional failover acceptable, but losing an alert firing NOT acceptable? | Different durability SLAs per subsystem |
| Multi-tenancy | Can one tenant's cardinality spike degrade another tenant's write/query latency? | Determines shard isolation strategy |
| Security/Compliance | Do enterprise customers need data residency (EU data stays in EU) and RBAC down to the dashboard level? | Affects storage topology and control-plane design |
| Operational | What's the on-call expectation for alert delivery latency (30s? 2min?) | Sets the NFR for the alerting subsystem specifically |

**Stated assumptions** (typical for this interview):
- B2B SaaS, ~50,000 customer organizations, largest customer has ~200,000 hosts.
- Scope: **Metrics (time series) + Distributed Tracing (APM) + Alerting**. Logs are explicitly out of scope (different cost/storage profile, would double the interview).
- Dashboard queries should return in <500ms p95 for rollup queries; alert evaluation must fire within 60s of the triggering condition.
- Multi-tenant, shared infrastructure with per-tenant cardinality quotas.

## 3. Functional Requirements

**Must Have**
- Ingest metrics (name, tags, value, timestamp) from agents at high frequency — this is the core product.
- Ingest distributed traces (spans with trace_id/span_id/parent_id) and reconstruct full traces — this is the second core product.
- Define alert rules over metrics (threshold, anomaly) and traces (error rate, latency) and fire notifications within SLA.
- Dashboards: query and visualize metrics over arbitrary time windows with aggregation (sum/avg/p99) and group-by-tag.

**Nice to Have**
- Anomaly-detection-based alerting (ML-driven baselines) — valuable but orthogonal to the core storage/query problem.
- Log correlation with traces (trace_id in log lines) — deferred since logs are out of scope.
- Synthetic monitoring / uptime checks — a separate product surface, not core to this design.

**Explicitly Out of Scope**
- Log ingestion and full-text log search — different storage engine (inverted index vs TSDB), would dilute focus.
- SIEM/security event correlation — separate product line.
- Billing/usage metering internals — assume it consumes the same pipeline, not designed here.

## 4. Non-Functional Requirements

| NFR | Why it matters | Target |
|---|---|---|
| Write availability (metrics) | Losing agent writes during a regional blip erodes trust in the product | 99.99%, with local agent buffering to survive short outages |
| Write durability (alerts config) | Losing an alert *definition* is a customer-visible bug | 99.999% (control plane, low volume, strongly consistent store) |
| Query latency (dashboards) | Interactive UX requirement | p95 < 500ms for rollup queries over 24h; p95 < 3s for raw high-res queries |
| Alert evaluation latency | Directly maps to incident response time for customers | p99 < 60s from data landing to notification fired |
| Cardinality isolation | One tenant's bad tag shouldn't degrade others | Per-tenant cardinality quota enforced at ingestion |
| Storage cost efficiency | Time-series data volume dwarfs almost every other data type in the company | Automatic downsampling/rollup after retention tiers (raw 15d, 5-min rollup 13mo) |
| Trace sampling fidelity | Must keep 100% of error/slow traces even while sampling 99% of normal traffic | Tail-based sampling with zero-miss on error traces |

## 5. Capacity Planning

**Metrics ingestion**
- 50,000 orgs, avg 500 hosts/org (long tail), largest org 200k hosts → ~15M hosts total (dominated by large orgs, assume effective ~10M active hosts).
- ~150 metrics/host, emitted every 10s → 10M hosts × 150 × 0.1/s = **150M data points/sec** at peak (assume this is the actual working number the interview converges on — realistically closer to 5–20M/s for a platform this size; state the assumption explicitly and use it consistently).
- Using a more grounded estimate for the interview: **10M active hosts × 150 metrics ÷ 10s interval ≈ 150M points/sec is too high for a single platform** — recalibrate: assume 2M active hosts (large but plausible for a major vendor), 150 metrics/host/10s → 2M × 150 / 10 = **30M points/sec** ingest.
- Each point ≈ 24 bytes (metric ID hash 8B, timestamp 8B, value 8B) after tag interning → 30M × 24B = **720 MB/s raw write**, ~62 TB/day before compression. Columnar + delta-of-delta encoding typically gets 10-20x → ~4-6 TB/day stored.
- Unique time series (cardinality): assume avg 20 unique tag combinations per metric name × 2M hosts × 150 metrics ≈ **6 billion active series** — this is the number that actually drives the hard design decisions (index size, hot-partition risk), not raw point volume.

**Tracing**
- Assume 500k requests/sec platform-wide across all customers, avg 20 spans/trace → 10M spans/sec generated at the edge.
- 100% of error/slow traces kept, ~1% of normal traces kept post-sampling → ingested span rate ≈ **150k spans/sec** into durable storage.
- Avg span size 1KB → 150 MB/s trace storage, ~13 TB/day raw.

**Alerting**
- Assume 50,000 orgs × avg 20 active alert rules = **1M active alert rules**, each needs evaluation on a rolling window (e.g., every 30-60s) → ~20k rule-evaluations/sec.

**System profile**: write-heavy and storage-heavy for metrics (extreme cardinality, not extreme request-count), write-heavy and consistency-sensitive for traces (must stitch spans across nodes before a sampling decision), and read+compute-heavy for alerting (continuous streaming aggregation, not simple point reads).

## 6. Core Domain Model

- **MetricSeries** — a unique (metric_name, tag_set) combination; identified by a `series_id` hash. Purpose: the addressable unit of time-series data.
- **MetricPoint** — (series_id, timestamp, value). Purpose: the actual measurement, append-only.
- **Trace** — (trace_id, root_span, status, duration). Purpose: logical grouping of spans representing one request's journey.
- **Span** — (span_id, trace_id, parent_span_id, service_name, start_time, duration, tags). Purpose: one unit of work within a trace.
- **AlertRule** — (rule_id, org_id, query_definition, threshold, evaluation_window, notification_targets). Purpose: control-plane definition of what to watch.
- **AlertEvent** — (event_id, rule_id, fired_at, resolved_at, state). Purpose: the record of an alert transitioning firing/resolved — this is what drives dedup and flapping suppression.
- **Organization/Tenant** — (org_id, cardinality_quota, retention_tier). Purpose: multi-tenancy and billing boundary.

Relationships: Org 1—N MetricSeries, Org 1—N AlertRule, Trace 1—N Span, AlertRule 1—N AlertEvent.

## 7. API Design

```
POST /v1/series
  Body: { series: [{ metric: "app.request.latency", tags: {...}, points: [[ts, val], ...] }] }
  Idempotency: point writes are naturally idempotent on (series_id, timestamp) — last-write-wins on
  duplicate timestamp is acceptable for gauges; counters require client-side monotonic sequence.

POST /v1/traces
  Body: { spans: [{ trace_id, span_id, parent_span_id, service, start, duration, tags }] }
  Idempotency: keyed on span_id — duplicate span delivery (agent retry) is deduped at the collector.

GET /v1/query?metric=X&tags=Y&agg=avg&from=&to=&groupby=
  Read-only rollup query, routed to the appropriate resolution tier based on time range.

POST /v1/alert-rules
  Body: { org_id, query, threshold, window, notify: [...] }
  Idempotency: client-supplied rule_id (UUID) makes creation idempotent under retry.

GET /v1/alert-events?rule_id=&state=firing
  Read current firing state — powers the alert inbox / on-call UI.
```

## 8. High-Level Architecture

Components: **Agent** (runs on customer hosts, batches and buffers metrics/spans locally to survive network blips) → **Ingestion Gateway** (stateless, auth + per-tenant cardinality quota enforcement + routing) → **Kafka** (durable buffer, partitioned by tenant+series/trace_id, decouples ingest spikes from storage write throughput) → **Metrics Writer** (batches points into the TSDB, handles downsampling) → **TSDB** (wide-column store, the metrics system of record) → **Trace Assembler** (stateful service that buffers spans by trace_id in a distributed cache until the trace is complete or times out, then makes the sampling decision) → **Trace Store** (wide-column store, spans keyed by trace_id) → **Alert Evaluator** (streaming consumers reading from Kafka and/or querying the TSDB on a schedule, maintaining rolling-window state per rule) → **Notification Service** (dedups and delivers firing/resolved events) → **Query Service** (serves dashboard reads, routes to raw vs rollup tiers) → **Metadata/Control-Plane Store** (strongly consistent relational store for AlertRule, Org, RBAC — low volume, correctness-critical).

Request flow: an agent batches metrics/spans and pushes to the Ingestion Gateway over HTTPS; the gateway authenticates, checks the tenant's cardinality quota, and writes to Kafka partitioned by tenant to guarantee ordering per series/trace without creating a global bottleneck. The Metrics Writer and Trace Assembler consume independently at their own pace, decoupling ingest bursts from storage backpressure. The Alert Evaluator taps the same Kafka stream (or queries the TSDB directly for coarser-grained rules) to maintain in-memory rolling aggregates per rule and fires through the Notification Service when thresholds are crossed, with dedup against the AlertEvent table to prevent re-notifying on every evaluation tick while still firing.

## 9. Tradeoff Table

| Decision | Option A | Option B | Chosen | Why |
|---|---|---|---|---|
| Metrics storage | Row-store (Postgres/MySQL) | Wide-column TSDB (Cassandra/Bigtable-style) | B | Append-heavy, time-ordered, needs horizontal partitioning by series — row stores can't handle 6B series' write throughput |
| Cardinality control | Allow unlimited tags, let storage absorb it | Enforce per-tenant cardinality quota at ingestion | B | Unbounded cardinality is the #1 real-world outage cause in TSDBs (a single bad tag can 100x series count) |
| Trace sampling | Head-based (decide at span-start) | Tail-based (decide after trace completes) | B | Head-based can't guarantee 100% capture of error/slow traces since you don't know the outcome yet |
| Alert evaluation | Poll the TSDB per rule on a timer | Stream-based rolling aggregation off Kafka | Hybrid: stream for high-frequency/low-latency rules, poll for coarse rules | Streaming gives sub-minute latency for the rules that need it; polling is simpler/cheaper for the long tail of infrequent rules |
| Rollup strategy | Query raw data always, compute aggregates at read time | Precompute rollups (5-min, 1-hr) on write, query raw only for short windows | B | Read-time aggregation over 13 months of raw 10s data is infeasible; rollups trade storage for query latency |
| Consistency for alert config | Eventually consistent (same store as metrics) | Strongly consistent relational store, separate from the TSDB | B | Alert *definitions* are low-volume and correctness-critical (a lost/duplicated rule is a customer-visible bug); don't couple its consistency model to the TSDB's |

## 10. Operational & Business Appendix

**Security**: Per-org API keys scoped to write-only (agent) vs read-write (dashboard/API) roles; RBAC at the dashboard/alert level for enterprise tenants; data residency handled by regional deployment of the entire pipeline (agents route to region-pinned gateways) rather than cross-region replication of raw data. **Observability** (of the observability platform itself — the classic "who watches the watchmen" problem): the platform runs its own lightweight internal metrics/tracing pipeline, isolated from customer traffic, so an incident in the customer-facing TSDB doesn't blind on-call to the incident itself. **Product/business framing**: pricing is typically per-host or per-metric-cardinality, which creates a direct incentive tension — the sales/product team wants generous default retention and cardinality limits, while the platform team needs quotas to protect shared infrastructure; this tension is exactly why per-tenant quotas (Section 9) matter both technically and commercially. **Evolution roadmap**: v1 ships metrics + basic threshold alerting; v2 adds tracing and tail-sampling; v3 adds anomaly-detection alerting and log correlation (at which point the out-of-scope log pipeline becomes the next major design effort).

---

# PASS 2 — Mandatory Deep Dives

**Step 1 — Component selection.** The three components that carry real signal, and why they beat the alternatives:

1. **The metrics TSDB schema and partition/shard key** — this is where cardinality explosion and hot-partition failures actually live; a wrong partition key here doesn't degrade the system, it takes it down.
2. **The trace assembler / tail-sampling mechanism** — this is a genuinely hard distributed-systems problem (buffering an unbounded, unordered stream of spans keyed by trace_id, deciding when a trace is "done," and doing it under memory pressure at 10M spans/sec generated).
3. **The alert evaluator's watermarking and dedup mechanism** — the interesting failure here isn't "the query is slow," it's silent correctness bugs: late data causing a missed alert, or a naive re-evaluation causing alert-storming (paging on-call 50 times for one outage).

Everything else — the ingestion gateway, Kafka buffering, the control-plane store — is a standard, well-understood pattern that doesn't differentiate a Staff candidate. I'm explicitly *not* deep-diving "the database" in the abstract; I'm deep-diving the specific schema/sharding decisions inside two different databases plus one stateful streaming component, because that's where this problem's actual difficulty is.

---

### Deep Dive 1: Metrics TSDB — Schema, Sharding, and the Hot-Partition Failure

**Schema** (Cassandra/ScyllaDB-style wide-column, chosen for linear horizontal scalability and native wide-row support for time-ordered data):

```sql
-- Metadata table: maps a metric+tag combination to a compact series_id.
-- This indirection exists so hot-path writes never carry raw tag strings.
CREATE TABLE series_metadata (
    org_id          uuid,
    metric_name     text,
    tags_hash       bigint,      -- hash of sorted tag key/value pairs
    series_id       bigint,      -- compact numeric id, generated once
    tags            map<text,text>,
    created_at      timestamp,
    PRIMARY KEY ((org_id, metric_name), tags_hash)
);

-- Hot path: the actual time-series data.
-- Partition key is (org_id, series_id, time_bucket) — NOT just series_id, and
-- critically NOT (org_id, metric_name) alone. See sharding reasoning below.
CREATE TABLE metric_points (
    org_id          uuid,
    series_id       bigint,
    time_bucket     text,        -- e.g. "2026-08-29-14" (hourly bucket)
    ts              timestamp,
    value           double,
    PRIMARY KEY ((org_id, series_id, time_bucket), ts)
) WITH CLUSTERING ORDER BY (ts ASC)
  AND compaction = {'class': 'TimeWindowCompactionStrategy'};

-- Precomputed rollups, same partitioning pattern, coarser time_bucket + resolution.
CREATE TABLE metric_rollups_5m (
    org_id          uuid,
    series_id       bigint,
    time_bucket     text,        -- e.g. "2026-08-29" (daily bucket at 5-min resolution)
    ts              timestamp,
    avg_value       double,
    min_value       double,
    max_value       double,
    count           int,
    PRIMARY KEY ((org_id, series_id, time_bucket), ts)
) WITH CLUSTERING ORDER BY (ts ASC);
```

**Primary query — dashboard reads a metric over 24h, grouped by a tag:**

```sql
-- Step 1 (control plane / cached): resolve which series_ids match the query's tag filter
SELECT series_id FROM series_metadata
WHERE org_id = ? AND metric_name = 'app.request.latency';
-- (tag filtering happens in an inverted index maintained alongside this table — see
-- "what changes to fix" below; naive full-scan-and-filter doesn't survive 10x load)

-- Step 2 (hot path, fanned out per series_id, per time_bucket in range): read rollups
SELECT ts, avg_value, count FROM metric_rollups_5m
WHERE org_id = ? AND series_id = ? AND time_bucket = ? AND ts >= ? AND ts < ?;
```

At **10x load**: the fan-out in Step 2 (one query per matching series_id per time bucket) starts to dominate — a dashboard widget matching 10,000 series over 24h/hourly buckets is 240,000 point queries. Fix: batch reads via `IN` on time_bucket where the driver supports token-aware batching, and cap/paginate the number of series a single query can expand to (push cardinality limits into the query layer, not just ingestion).
At **100x load**: per-query fan-out is no longer viable at all; this forces precomputing common group-by aggregations at write time (a "pre-aggregated rollup by tag-group" table, effectively a materialized view keyed by the group-by dimension), trading write amplification for read simplicity — this is the same rollup-vs-raw tradeoff from Section 9, just pushed one level deeper.

**Partition-key reasoning — argued, not asserted.**

The chosen partition key is **`(org_id, series_id, time_bucket)`**. Walk through what breaks with the "obvious" wrong design of putting `time_bucket` in the *clustering* (sort) key only, with partition key `(org_id, series_id)` alone (i.e., one giant partition per series, unbounded in time):

1. Every point for a given series, forever, lands in the same partition. Cassandra/Scylla partitions are physically colocated on a fixed set of replica nodes.
2. A high-frequency series (e.g., a metric emitted every 1s for years) grows that partition unboundedly — this is the classic **unbounded partition** anti-pattern. Compaction has to repeatedly rewrite an ever-growing partition, degrading write throughput over time on exactly the nodes holding that series.
3. Worse: because a *specific* series_id always maps to the *same* replica set (Cassandra's partitioner hashes the partition key to a fixed set of nodes), a customer with one extremely high-traffic metric (e.g., a global request-counter) creates a **permanent hot partition** — those 3 replica nodes take disproportionate write load for the *life of the series*, with no way to redistribute.
4. Now add `time_bucket` (e.g., hourly) into the partition key: the same series' data is spread across a *new* partition every hour, which (a) bounds partition size regardless of series lifetime, and (b) means the hash of the partition key changes every hour, so the *physical replica set* for that series' current writes rotates over time — a hot series doesn't permanently pin the same 3 nodes, it hot-spots one bucket's replica set for one hour and moves on.
5. The tradeoff this creates: range queries across many hours now hit many partitions (the fan-out problem above) instead of one. That's an accepted cost — read fan-out is solvable with parallelism and rollups; write-side unbounded/permanently-hot partitions are not solvable without this key design.

**Concrete failure case — hot partition from a bad tag, worked step by step:**

1. A customer instruments their code with `request.latency` tagged by `user_id` (a well-intentioned but catastrophic mistake — cardinality goes from ~20 combinations to millions).
2. Each unique `user_id` creates a new row in `series_metadata` and a new `series_id`. Write volume to `series_metadata`'s partition `(org_id, metric_name)` spikes — this partition key is *not* time-bucketed, so it's an unbounded partition by cardinality (not by time), and it starts absorbing millions of new rows in minutes.
3. The replica set for that `(org_id, metric_name)` partition becomes hot: writes to `series_metadata` for this one metric name saturate 3 nodes' write path, and because Cassandra co-locates the partition, there's no way to shard it further without a schema change.
4. Symptom: p99 write latency for the *entire org* (all their metrics, not just this one) degrades, because the ingestion path for this org is now bottlenecked on the `series_metadata` write for this one bad metric — and if replicas are shared across tenants (multi-tenant cluster), *other tenants* on the same physical nodes see latency degradation too (the noisy-neighbor problem from Section 4's isolation NFR).
5. **Bookkeeping mechanism that catches this before it becomes an outage**: a per-org, per-metric cardinality counter maintained via a Cassandra counter column (or a separate fast key-value store like Redis with periodic flush), incremented on every *new* series_id creation:
```sql
CREATE TABLE cardinality_counters (
    org_id       uuid,
    metric_name  text,
    series_count counter,
    PRIMARY KEY (org_id, metric_name)
);
-- On the ingestion gateway, before creating a new series_id:
UPDATE cardinality_counters SET series_count = series_count + 1
WHERE org_id = ? AND metric_name = ?;
-- Gateway reads the counter (cached, refreshed every few seconds) and REJECTS
-- new-series creation once the org's quota (Section 4/9) is exceeded, returning
-- a 429 with a clear "cardinality limit exceeded for metric X" error to the agent.
```
6. **What changes to fix it, structurally** (not just the quota band-aid): split `series_metadata`'s partition key to include a shard suffix — `(org_id, metric_name, shard = hash(tags_hash) % N)` — so even a single metric name's cardinality explosion spreads across N partitions/replica-sets instead of one. This is the same "add a distributing dimension to the partition key" fix as the time_bucket fix above, applied to the cardinality dimension instead of the time dimension.

---

### Deep Dive 2: Trace Assembler & Tail-Based Sampling — Stateful Stream Stitching

**The core problem**: spans for one trace arrive out of order, from different services, over a span of seconds to (in pathological cases) minutes, and the sampling decision ("keep or discard this whole trace") can only be made once you know whether *any* span in the trace was an error or was slow — which means you must buffer the *entire trace* before deciding, at 10M spans/sec of inbound volume.

**Design**: spans are routed by `trace_id` (consistent hashing) to a specific Trace Assembler shard, guaranteeing all spans of one trace land on the same node — this is the deliberate partition-key choice, directly analogous to the TSDB's series_id choice, and for the same reason: co-location of related writes on one node is what makes assembly possible without a distributed transaction.

```sql
-- In-memory/local-disk buffer per assembler shard (not the durable store —
-- this is working state, e.g., RocksDB-backed for spill-to-disk under memory pressure).
CREATE TABLE trace_buffer (
    trace_id        text,
    span_id         text,
    parent_span_id  text,
    service_name    text,
    start_time      timestamp,
    duration_ms     int,
    is_error        boolean,
    first_seen_at   timestamp,   -- when THIS assembler shard first saw any span for this trace
    PRIMARY KEY (trace_id, span_id)
);

-- Durable store, written only AFTER the sampling decision is made.
CREATE TABLE spans (
    trace_id        text,
    span_id         text,
    parent_span_id  text,
    service_name    text,
    start_time      timestamp,
    duration_ms     int,
    tags            map<text,text>,
    PRIMARY KEY ((trace_id), span_id)
);
```

**Watermark mechanism (the actual bookkeeping)**: each assembler shard tracks, per trace_id, `first_seen_at`. A background sweep runs every second:

```
FOR each trace_id in trace_buffer WHERE first_seen_at < now() - 10s:
    decision = SHOULD_SAMPLE(trace_id)   -- true if any span has is_error=true
                                          -- OR total trace duration > slow_threshold
                                          -- OR random() < base_sample_rate
    IF decision == keep:
        bulk-write all buffered spans for trace_id to durable `spans` table
    DELETE FROM trace_buffer WHERE trace_id = trace_id
```

The `10s` value is the **watermark** — the assembler's declared belief that "a trace is done" if no new spans have arrived for 10s after the first span was seen. This is a heuristic, not a guarantee (analogous to Flink/Beam event-time watermarks), and it's the single biggest source of correctness bugs in real tracing systems.

**Concrete failure case, worked step by step — the late-span/split-decision race:**

1. A trace starts; assembler shard S receives spans for services A, B, C within the first 2 seconds. No errors seen yet. `first_seen_at = T0`.
2. Service D is on a host with a network partition and its span (which *does* have `is_error=true`) doesn't reach the gateway until `T0 + 12s` — past the 10s watermark.
3. At `T0 + 10s`, the sweep fires: `SHOULD_SAMPLE` sees no error spans buffered, rolls the random sample dice, and (say) decides "discard" — spans for A, B, C are deleted from the buffer.
4. At `T0 + 12s`, D's error span arrives at shard S, looks up `trace_id` in `trace_buffer` — **it's gone**. The assembler has two bad options: (a) discard D's span too (losing the error trace entirely — the exact failure mode the NFR in Section 4 says must never happen for error traces), or (b) write D's span alone to durable storage as an orphaned partial trace (misleading — the trace now appears to have started at D with no upstream context).
5. **This is the concrete flaw the design must surface and fix**, not paper over.

**What changes to fix it**: two changes, both necessary —
- **Widen the watermark asymmetrically**: don't delete the buffer entry on a "discard" decision — instead mark it `tombstoned_at = now()` and keep a *lightweight* tombstone (trace_id + tombstone timestamp only, spans actually discarded to save memory) for an additional grace period (e.g., 60s). A late span arriving within that grace period, if it's an error span, triggers a **re-open**: the assembler cannot recover the already-discarded A/B/C spans (they're gone), but it can at least write D's span with an explicit `partial_trace = true` flag and emit a metric (`late_span_after_discard_count`) so the platform team can tune the watermark based on real p99 late-arrival latency instead of guessing.
- **Track a per-service "late arrival" distribution** and set the watermark dynamically per-org (or per-service) based on observed p99 span latency, rather than a single global 10s constant — an org with services on flaky networks needs a longer watermark than one with a tight internal network, and a fixed global constant is either too aggressive (data loss, as above) or too conservative (memory pressure from buffering too long, hurting the 10x/100x scaling story).

**Under 10x/100x load**: the binding constraint shifts from CPU (assembly logic is cheap) to **memory** — buffering 10x more concurrent in-flight traces per shard. Fix: spill `trace_buffer` to local SSD (RocksDB) once in-memory size crosses a threshold, and shard `trace_id` hashing across more assembler nodes — but note this doesn't change the *correctness* problem above, only the capacity problem; the late-span race exists at any scale.

---

### Deep Dive 3: Alert Evaluator — Watermarking, Dedup, and the Flapping/Storm Problem

**The core problem**: naive design re-evaluates every rule on a fixed timer against the latest data and fires a notification whenever the condition is true. Two failure modes fall out of this immediately: (a) if the evaluator fires *every time* the condition is still true (not just on transition), on-call gets paged every 30s for the duration of an outage — an **alert storm**; (b) if data for the evaluation window arrives late (a host was disconnected, its metrics land 90s after their timestamp), a rule evaluated strictly on wall-clock time can either miss the breach entirely (if it already evaluated and moved on) or double-fire once the late data arrives and re-triggers.

**Schema**:

```sql
-- Control plane (strongly consistent, low volume — see Section 9's tradeoff).
CREATE TABLE alert_rules (
    rule_id         uuid PRIMARY KEY,
    org_id          uuid,
    series_query    text,
    threshold       double,
    comparator      text,       -- '>', '<', etc.
    window_seconds  int,
    eval_interval_s int
);

-- State table: the CURRENT firing/resolved state per rule, with a version for CAS.
CREATE TABLE alert_state (
    rule_id         uuid PRIMARY KEY,
    state           text,        -- 'ok' | 'firing'
    last_fired_at   timestamp,
    last_value      double,
    version         int          -- optimistic concurrency token
);

-- History: append-only, powers the on-call inbox and dedup lookups.
CREATE TABLE alert_events (
    rule_id         uuid,
    event_id        uuid,
    transitioned_at timestamp,
    from_state      text,
    to_state        text,
    triggering_value double,
    PRIMARY KEY ((rule_id), transitioned_at)
) WITH CLUSTERING ORDER BY (transitioned_at DESC);
```

**Primary write — the evaluation tick, with compare-and-swap to prevent double-fire under concurrent evaluators:**

```sql
-- Read current state
SELECT state, version FROM alert_state WHERE rule_id = ?;

-- Only write a transition, using CAS on version — this is the mechanism that
-- prevents two evaluator replicas (running for HA) from both firing the same
-- transition if they race on the same evaluation tick.
UPDATE alert_state
SET state = 'firing', last_fired_at = ?, last_value = ?, version = version + 1
WHERE rule_id = ? IF version = ?;
-- LWT (lightweight transaction) — only succeeds if no other evaluator won the race.
-- On failure (version mismatch), the losing evaluator simply no-ops for this tick.

-- Only insert into alert_events (which triggers notification) on an ACTUAL
-- state transition (ok->firing or firing->ok), never on ok->ok or firing->firing.
INSERT INTO alert_events (rule_id, event_id, transitioned_at, from_state, to_state, triggering_value)
VALUES (?, uuid(), now(), 'ok', 'firing', ?);
```

This CAS-on-`version` field is the explicit bookkeeping mechanism: it converts "did the state change" into an atomic, race-free operation across however many evaluator replicas are running for HA, and the "only insert alert_events on actual transition" rule is what prevents the alert storm — repeated `firing`→`firing` ticks update `last_fired_at`/`last_value` for freshness but never re-trigger a notification.

**Concrete failure case — late data causing a false resolve, worked step by step:**

1. Rule: "avg CPU > 90% over a 5-min window, evaluated every 30s." At `T0`, CPU spikes to 95% but only 2 of the expected 10 hosts' data points have landed (the other 8 are delayed in Kafka due to a partial network issue) — the partial average looks like 60%, below threshold. State stays `ok`.
2. At `T0+30s`, the missing 8 hosts' data arrives (late by ~25s). Recomputing the 5-min window average now correctly shows 95% — but the evaluator already "moved past" that window in its naive polling model if it's not tracking a watermark, and the next tick evaluates a *new* rolling window that may or may not still show the breach depending on timing — this is a **missed alert**, exactly the failure the NFR in Section 4 says is worse than a false positive.
3. **Root cause**: the evaluator was treating "now" as the watermark, rather than tracking how far behind the actual data stream is.
4. **Fix — explicit watermark tracking per rule's underlying series**: the Alert Evaluator, consuming from the same Kafka stream as the Metrics Writer (Section 8), tracks the max timestamp seen per partition and computes a watermark = `max_seen_timestamp - allowed_lateness (e.g., 30s)`. A rule's window is only considered "closed" (safe to finalize the ok/firing decision) once the watermark has passed the window's end — this is the same event-time-vs-processing-time distinction as the trace assembler's watermark in Deep Dive 2, applied here to prevent under-counting instead of over-buffering.
5. **Tradeoff this introduces**: waiting for the watermark before finalizing a decision adds up to `allowed_lateness` (30s) of latency to alert firing — directly trading against the p99 < 60s NFR from Section 4. This is resolved by firing a **provisional/tentative** notification immediately if the *partial* data already crosses threshold (fast path, matches the "false positives less bad than false negatives" priority), and only using the watermark-gated recomputation to *correct* (upgrade to certain, or in rare cases retract) that notification once late data settles — giving both fast initial signal and eventual correctness.

---

### Step 3: Worked Follow-Up Questions

**1. How do you prevent one tenant's write burst from starving others on a shared Kafka cluster?**
Partition Kafka topics by `org_id` with a bounded number of partitions per tier (e.g., small orgs share a partition pool, largest orgs get dedicated partitions), and enforce per-org produce quotas at the broker level (Kafka's native `quota.producer.byte-rate` keyed by client-id=org_id). A large org's burst is throttled at the client, not left to degrade shared broker I/O.

**2. What happens to the TSDB schema if you need to support metric *deletion* (GDPR right-to-erasure on a specific host's data)?**
Point-level deletes in a TimeWindowCompactionStrategy table are expensive (tombstone accumulation degrades read performance). Instead: since data is partitioned by `time_bucket`, and GDPR erasure requests are rare/batched, implement erasure as a background job that reads the affected partitions, rewrites them excluding the target rows, and swaps — essentially a targeted compaction — rather than issuing per-row `DELETE` statements against a live table.

**3. How would you support a "top 10 hosts by CPU" query, which requires a cross-series aggregation the schema wasn't designed for?**
This doesn't fit the `(org_id, series_id, time_bucket)` partition key at all — it requires scanning all series for an org at a given timestamp. Add a secondary, purpose-built table: `CREATE TABLE latest_by_metric (org_id uuid, metric_name text, time_bucket text, series_id bigint, value double, PRIMARY KEY ((org_id, metric_name, time_bucket), value)) WITH CLUSTERING ORDER BY (value DESC);` — written alongside the primary write path specifically to serve top-N queries via clustering-key ordering, trading write amplification for a query pattern the primary schema can't serve.

**4. Two evaluator replicas both crash mid-tick after the CAS succeeds but before the notification is sent — does the alert get lost?**
No: the `INSERT INTO alert_events` is the durability boundary, and the Notification Service consumes from `alert_events` (e.g., via CDC/Kafka Connect on that table) rather than being called synchronously by the evaluator. A crash after the state transition is durably written still leaves a row for the Notification Service to pick up on its next poll/stream read — decoupling the state transition from the notification delivery is exactly what makes this safe.

**5. How do you bound the trace assembler's memory if a customer sends a "trace" with 100,000 spans (a bug or an attack)?**
Cap buffered spans per trace_id (e.g., 5,000) at the assembler; beyond that, force-close the trace early (make the sampling decision on partial data, marked `truncated = true`) rather than allowing unbounded buffer growth per trace_id — this is a second, independent bound alongside the per-shard cardinality quota from Deep Dive 1.

**6. Your cardinality quota (Deep Dive 1) rejects new series with a 429 — what does the customer's agent do with that, and does it risk data loss?**
The agent should drop the specific offending series locally (not retry indefinitely, which would just hot-loop against the quota) and surface a local warning/metric (`agent.dropped_points_cardinality_limit`) so the customer can see it in their own telemetry — a deliberate design choice that a *visible, bounded* data loss (this one bad metric) is far better than an *invisible, unbounded* one (the whole org's write path degrading, per the Deep Dive 1 failure case).

**7. How does regional failover work for the metrics write path without violating the 99.99% write availability NFR?**
Agents are configured with a primary + fallback regional gateway endpoint; on primary failure, agents buffer locally (bounded ring buffer, e.g., 5 minutes) and retry, then fail over to the secondary region if the primary stays down past the buffer's capacity — trading a brief window of at-risk data (bounded by buffer size) for avoiding a hard dependency on cross-region synchronous replication, which would itself hurt write latency under normal operation.

**8. Short-answer follow-ups** (no full worked answer required): How would you support percentile aggregations (p99) across rolled-up data without storing every raw point? What's the RBAC model for a dashboard shared across 3 teams with different data-access scopes? How do you handle clock skew between agent-reported timestamps and gateway receive-time? How would you migrate the `series_metadata` sharding scheme (Deep Dive 1's fix) without downtime? What's the disaster-recovery RPO/RTO for the control-plane AlertRule store specifically? How do you cost-attribute storage back to individual tenants for billing given shared TSDB infrastructure?

---

# Final Section — Staff-Level Summary

**Key architectural decisions**
- Wide-column TSDB with `(org_id, series_id, time_bucket)` partitioning — bounds partition size by time and rotates the hot replica set, rather than the naive `(org_id, series_id)`-only key that creates permanent hot partitions.
- Tail-based trace sampling via trace_id-consistent-hashed assembler shards with an explicit, tunable watermark — not a fixed global timeout.
- Alert state machine with CAS-based transitions and watermark-gated window finalization, decoupled from notification delivery via a durable event log.

**Biggest tradeoffs**
- Rollup precomputation trades write amplification for read latency at scale — necessary but adds pipeline complexity and eventual-consistency windows between raw and rolled-up views.
- The alert evaluator's fast-path/watermark-correction split trades a small rate of "corrected" notifications for meeting the 60s SLA — this needs to be a visible, understood behavior for customers (a notification that gets retracted), not a hidden inconsistency.

**Biggest risks**
- Cardinality quota enforcement is the single most load-bearing mechanism in the whole system — get the quota UX wrong (too strict) and customers lose real data; too loose and one tenant takes down shared infrastructure.
- The trace assembler's late-span/discard race (Deep Dive 2) is a genuine unsolved-in-full correctness gap — the mitigation (grace-period tombstones) reduces but doesn't eliminate the failure mode, and that should be stated honestly rather than presented as fully solved.

**Scorecard**

| Dimension | Score |
|---|---|
| Problem Framing | 9/10 |
| Requirements | 8/10 |
| NFRs | 8/10 |
| Capacity Planning | 7/10 |
| Data Modeling | 9/10 |
| Architecture | 8/10 |
| Tradeoffs | 9/10 |
| Failure Analysis | 9/10 |
| Product Thinking | 7/10 |
| **Overall** | **8.2/10** |

**Path to Senior Staff / Principal**: this answer stays within a single-region, single-cluster mental model for each subsystem; Principal-level depth would additionally reason about cross-region replication strategy for the TSDB itself (not just agent failover), the org-level cost-modeling feedback loop between pricing and the cardinality quota (a genuine product-vs-platform tension flagged but not resolved above), and a migration strategy for evolving the partition key scheme (follow-up #7) on a live system serving 30M points/sec without a maintenance window — the difference between "designs a correct system" and "designs a system that can safely evolve under production load with a live customer base."
