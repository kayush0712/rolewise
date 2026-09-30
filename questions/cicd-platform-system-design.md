# CI/CD Platform — Staff System Design Interview (L7/E7)

---

## PASS 1 — Compressed Full-System Scaffold

### 1. Interview Context

This is a **workflow-orchestration-under-multi-tenancy** problem, structurally close to Temporal/Airflow but with a hard real-time UX layer (live logs, live status) bolted on. The hidden challenges are: (a) fair scheduling of compute across tenants sharing a finite runner fleet, (b) DAG execution semantics that must survive worker crashes without double-running non-idempotent steps (e.g. `terraform apply`, `npm publish`), and (c) log/artifact volume that is bursty and enormous relative to the metadata volume. It's a good L7 problem because the "obvious" design (queue + workers + Postgres) breaks in three distinct, well-known ways — noisy-neighbor starvation, at-least-once execution corrupting non-idempotent build steps, and unbounded log storage cost — and a Staff engineer is expected to anticipate all three before writing code, not discover them in a postmortem. Likely probes: how do you keep one tenant's 10,000-job monorepo from starving everyone else, how do you guarantee a step doesn't run twice, how do you stream logs from an ephemeral pod, how do you replay/rerun from a mid-pipeline failure without redoing everything.

### 2. Scope Clarification

| Category | Question | Why it matters |
|---|---|---|
| Business | Self-hosted runners, hosted runners, or both? | Determines whether we own compute isolation or just orchestration |
| Business | Single tenant (internal platform) or multi-tenant SaaS (GitHub Actions style)? | Drives fairness, isolation, and billing requirements |
| UX | Do users need live log streaming, or is polling-after-completion acceptable? | Live logs require a real-time fanout path, not just storage |
| UX | Can pipelines be manually re-triggered from a failed step, or only from scratch? | Determines whether we need step-level checkpointing |
| Scale | How many pipeline runs/day, and what's the peak concurrency (e.g. all-hands push at 9am)? | Sets queue depth and autoscaling targets |
| Scale | What's the largest single DAG (steps, fanout)? | Determines DAG storage/traversal strategy |
| Reliability | Is a duplicate execution of a build step acceptable, or must it be exactly-once-effect? | Deploy/publish steps are not idempotent — this dictates the whole execution model |
| Multi-tenancy | Is there a hard per-tenant compute quota, or best-effort fairness? | Determines whether we need admission control or just weighted scheduling |
| Security/Compliance | Do pipelines need to run untrusted third-party code (e.g. PR from a fork)? | Drives sandbox/isolation requirements (gVisor/Firecracker vs. shared VM) |
| Operational | What's acceptable staleness for "job status" in the UI — seconds, or must it be push-exact? | Determines whether we can batch status updates |

**Stated assumptions:** Multi-tenant SaaS, hosted ephemeral runners (containers, not bare metal), live log streaming required, pipelines defined as YAML DAGs with a mix of idempotent and non-idempotent steps, hard per-tenant concurrency quotas, forked-PR builds run in a stronger sandbox. Scale target: 50M pipeline runs/day platform-wide, largest DAGs ~500 steps.

### 3. Functional Requirements

**Must Have**
- Define pipelines as DAGs of steps (YAML), with dependency edges, retries, and conditional execution — this is the product.
- Trigger on git push/PR/tag/schedule/manual — triggers are the entry point for everything downstream.
- Schedule steps onto a runner fleet with per-tenant fairness — without this the platform is unusable under contention.
- Stream logs live and persist them durably — logs are the primary debugging surface users touch.
- Guarantee each step executes with at-most-once *effect* even under worker crash — non-idempotent steps (deploys) demand this.
- Artifact passing between steps (build output → deploy step) — DAGs are useless if steps can't hand off state.

**Nice to Have**
- Distributed build caching (skip unchanged steps) — big cost/latency win, not correctness-critical.
- Matrix builds (fan out one job across N configs) — a scheduling convenience, not core semantics.
- Manual approval gates — a workflow feature layered on top of the state machine.

**Explicitly Out of Scope**
- The container image build process itself (Dockerfile semantics) — treated as an opaque step.
- Secrets management internals (assume a Vault-like secret store exists and is injected).
- Billing/metering pipeline — noted as an appendix concern only.

### 4. Non-Functional Requirements

| NFR | Why it matters | Target |
|---|---|---|
| Step scheduling latency | Time from "step is runnable" to "container running" — this is the perceived speed of CI | p50 < 5s, p99 < 30s |
| Log delivery latency | Live-tail UX degrades badly above a couple seconds | < 2s end-to-end |
| Execution correctness | Non-idempotent steps must not double-run | Zero tolerance — architectural invariant, not a percentile |
| Availability (control plane) | Scheduling/API must stay up even if a region's runner fleet is degraded | 99.95% |
| Fairness | No tenant should starve another under load | Max wait-time skew bounded by weighted-fair-share, not FIFO |
| Durability (logs/artifacts) | Post-hoc debugging depends on logs surviving pod death | 99.999% (object storage-grade) |

### 5. Capacity Planning

- Pipeline runs: 50M/day → ~580/sec average, peak (9–11am cluster, ~6x) ≈ **3,500 runs/sec**.
- Steps per run: avg 15 steps → **~52,000 steps/sec at peak** scheduled.
- Step duration: avg 90s → concurrent running steps ≈ 52,000 × 90 ≈ **4.7M concurrent containers at peak** (platform-wide, sharded across regions/cells — no single scheduler sees this number).
- Log volume: avg step emits 50KB logs → 52,000/sec × 50KB ≈ **2.6 GB/sec log ingest at peak**. Over a day, log storage growth ≈ 50M × 15 × 50KB ≈ **37.5 TB/day** (before compression/retention pruning).
- Metadata (job/step state rows): 50M runs × 15 steps × ~1KB row ≈ **750 GB/day** of state-table writes, dominated by status transitions (each step: queued→running→completed = 3 writes) → **2.25B row writes/day** ≈ 26,000 writes/sec average, ~150K/sec peak.
- **System profile: write-heavy on metadata (state transitions), throughput-heavy on logs (blob storage, not a database problem), and scheduling-heavy on the control plane (packing problem, not a storage problem).** This is not primarily a "big data" storage problem — it's a real-time scheduling and consistency problem wrapped around a blob-storage-heavy logging pipeline.

### 6. Core Domain Model

- **Pipeline** — the YAML-defined DAG template, versioned per commit. Belongs to a Repo/Tenant.
- **Run** — one execution instance of a Pipeline, triggered by an event. Has a status (queued/running/succeeded/failed/cancelled).
- **Step** — one node in the DAG for a given Run. Has dependencies (other Step IDs), a status, an assigned Runner, retry count.
- **StepAttempt** — one execution attempt of a Step (a Step can have >1 attempt on retry/crash-recovery). This is the unit that actually maps to a container.
- **Runner** — an ephemeral compute unit (container/VM) that executes exactly one StepAttempt at a time.
- **Tenant** — owns Pipelines, has a compute quota, has scheduling weight.
- **Artifact** — a blob produced by a Step, referenced by downstream Steps via content hash.
- **LogChunk** — an ordered chunk of log output for a StepAttempt, streamed and persisted.

Relationships: Tenant 1—N Pipeline; Pipeline 1—N Run; Run 1—N Step (DAG edges among Steps); Step 1—N StepAttempt; StepAttempt 1—1 Runner (at a time); StepAttempt 1—N LogChunk; StepAttempt N—N Artifact (produces/consumes).

### 7. API Design

```
POST /v1/runs
  { pipeline_id, trigger: {type: "push", sha, branch}, idempotency_key }
  → { run_id, status: "queued" }
  Idempotency: idempotency_key (e.g. hash of webhook delivery ID) dedupes replayed webhooks server-side.

GET /v1/runs/{run_id}
  → { run_id, status, steps: [{step_id, status, attempt_count, started_at}] }

POST /v1/runs/{run_id}/steps/{step_id}/retry
  → { new_attempt_id }
  Idempotency: retry is a new StepAttempt row; safe to double-click (returns existing attempt if one is already in-flight).

GET /v1/runs/{run_id}/steps/{step_id}/logs?since_offset=...
  → chunked stream of log lines with monotonic offsets (also available over WebSocket for live tail)

POST /internal/runner/{runner_id}/heartbeat
  { step_attempt_id, lease_token, status }
  → { lease_renewed: bool }
  This is the lease-renewal call that underlies the exactly-once-effect mechanism (Pass 2).
```

### 8. High-Level Architecture

**Components:** *Webhook Ingest* (validates + dedupes incoming git events) → *Trigger Service* (resolves which Pipeline to run, materializes the DAG for this Run) → *Scheduler* (assigns runnable Steps to Runners under fairness constraints — the packing problem) → *Runner Fleet* (autoscaled container pool, one StepAttempt each) → *State Store* (Run/Step/StepAttempt status, the source of truth for the DAG state machine) → *Log Ingest Pipeline* (Runner → local agent → Kafka → both a hot path for live-tail and a cold path to blob storage) → *Artifact Store* (content-addressable blob storage, e.g. S3 keyed by hash) → *Notification/Webhook-out Service* (status changes fan out to Slack/GitHub checks). Request flow: a push event hits Webhook Ingest, is deduped and handed to Trigger Service, which materializes Steps in the State Store as `pending`; the Scheduler continuously polls for Steps whose dependencies are satisfied and assigns them to available Runners under the tenant's fair-share weight; each Runner streams logs through the Log Ingest Pipeline and reports terminal status back through the State Store via a leased heartbeat, which unblocks downstream Steps in the DAG.

### 9. Tradeoff Table

| Decision | Option A | Option B | Chosen | Why |
|---|---|---|---|---|
| Execution guarantee | Exactly-once execution (distributed transactions) | At-least-once execution + idempotency/lease layer | **B** | True exactly-once across a crash-prone container fleet is not achievable without unacceptable latency; lease-based at-most-once-effect is the standard, provable pattern |
| Scheduler architecture | Central scheduler owns all assignment decisions | Sharded/cell-based schedulers per region+tenant-band | **B** | A single scheduler at 4.7M concurrent containers is a throughput and blast-radius risk; cells bound both |
| Log storage | Write logs straight to Postgres/state DB | Kafka → blob storage (S3) + a hot ring-buffer for live tail | **B** | Logs are 50x the write volume of metadata; co-locating them with transactional state would tank state-store performance |
| DAG state persistence | Store the whole DAG as a JSON blob, mutate in place | Normalize Steps as rows with an explicit state machine + version column | **B** | Row-level CAS updates are required for safe concurrent step-completion; a JSON blob invites lost-update races |
| Fairness mechanism | FIFO global queue | Weighted fair queuing per tenant, computed at dequeue time | **B** | FIFO lets one large monorepo's burst starve small tenants — directly violates the fairness NFR |
| Artifact addressing | Path-based (per-run directory) | Content-addressable (hash-based, dedup'd across runs) | **B** | Same dependency lockfile/build output recurs across runs; content-addressing gives free dedup and cache-hit detection |

### 10. Operational & Business Appendix

**Security:** forked-PR builds run in a stronger isolation boundary (microVM, e.g. Firecracker) than trusted first-party builds, secrets are injected at runtime via short-lived tokens scoped to the specific StepAttempt (never baked into the image), and network egress from untrusted builds is default-denied. **Observability:** the platform emits its own meta-metrics (scheduler queue depth per tenant, p99 step-assignment latency, runner utilization, lease-expiry-triggered retries) — a CI platform that can't observe its own scheduler fairness will silently degrade for large tenants first. **Product/business framing:** the monetizable unit is compute-minutes consumed, with tenant quotas mapping directly to pricing tiers; the fairness mechanism doubles as the enforcement mechanism for quota, which is a nice architectural convergence. **Evolution roadmap:** v1 ships with a single scheduling cell and simple weighted-fair-share; v2 adds cell sharding by tenant size band once a single cell's blast radius becomes a reliability concern; v3 adds distributed build caching once cost pressure from redundant compute justifies the complexity of content-addressed cache invalidation.

---

## PASS 2 — Mandatory Deep Dives

### Step 1: Component Selection

The two components that carry real distributed-systems signal here are:

1. **The Scheduler / Fair-Share Queue** — this is a live packing + fairness problem under contention, not a CRUD read path. The hard part isn't storing a queue, it's making dequeue decisions that are simultaneously fair, low-latency, and free of a hot-partition on popular tenants.
2. **The Step Execution Lease & DAG State Machine** — this is where at-least-once infrastructure meets non-idempotent user code (deploys, publishes). The hard part is guaranteeing at-most-once *effect* despite worker crashes, and doing so without a distributed transaction.

I'm explicitly *not* deep-diving log ingestion or artifact storage — both are well-understood "Kafka + blob store" patterns with no interesting distributed-systems wrinkle specific to this problem; they'd be padding, not signal.

---

### Deep Dive 1: Scheduler / Fair-Share Queue

**Schema**

```sql
CREATE TABLE schedulable_steps (
    tenant_id        UUID        NOT NULL,
    priority_bucket  SMALLINT    NOT NULL,   -- 0=default, 1=high (paid tier), derived from tenant plan
    enqueued_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    step_attempt_id  UUID        NOT NULL,
    run_id           UUID        NOT NULL,
    resource_class   TEXT        NOT NULL,   -- e.g. "2x-cpu", "gpu-small" — runner pool selector
    lease_token      UUID        NULL,       -- set when assigned, see Deep Dive 2
    PRIMARY KEY (tenant_id, priority_bucket, enqueued_at, step_attempt_id)
) PARTITION BY HASH (tenant_id);

CREATE TABLE tenant_scheduling_state (
    tenant_id         UUID PRIMARY KEY,
    weight            INT NOT NULL,           -- fair-share weight, from plan tier
    virtual_time      DOUBLE PRECISION NOT NULL DEFAULT 0,  -- for weighted fair queuing
    running_count     INT NOT NULL DEFAULT 0,
    quota_max         INT NOT NULL
);
```

**Partition key reasoning:** the table is hash-partitioned on `tenant_id`. Walk through what breaks if instead it were range-partitioned (or just sorted) on `enqueued_at` as the leading key, which is the "obvious" choice for a queue: every scheduler worker doing a dequeue scan would hit the *same* leading edge of the table — the most-recently-enqueued rows — because that's where "next runnable step" lookups concentrate. Under 3,500 runs/sec × 15 steps, that's ~52K inserts/sec all landing in the same time-ordered partition, and every scheduler replica doing a "find next step for tenant X respecting fairness" query would still have to scan across that single hot partition and filter by tenant, turning an O(tenants) fair-share decision into an O(all pending steps) scan. Hashing on `tenant_id` spreads both the write load and the "per-tenant next step" read pattern across partitions, and — critically — bounds a single noisy tenant's queue growth to *their own* partition rather than degrading a shared time-ordered structure for everyone else. The composite key then orders *within* a tenant's partition by `(priority_bucket, enqueued_at)`, which is exactly the scan order the scheduler needs for that tenant.

**Primary query (main access pattern):** "give me the next runnable step for tenant X that respects its fair-share turn."

```sql
SELECT step_attempt_id, run_id, resource_class
FROM schedulable_steps
WHERE tenant_id = $1
  AND lease_token IS NULL
ORDER BY priority_bucket DESC, enqueued_at ASC
LIMIT 1
FOR UPDATE SKIP LOCKED;
```

Which tenant to query is decided *outside* this query, by a weighted-fair-queuing (WFQ) selector that picks the tenant with the lowest `virtual_time` among tenants with runnable work and `running_count < quota_max` — that selection is O(tenants-with-work), kept in an in-memory min-heap per scheduler cell, not re-derived from the DB on every tick.

**At 10x load:** 520K steps/sec. The per-tenant partition query still works, but the *selector* (min-heap of tenants) becomes the bottleneck if it's a single in-memory structure per scheduler replica — so at 10x we shard scheduler replicas by `tenant_id % N` (a scheduling *cell* per shard, matching the Pass-1 tradeoff), each owning its own heap and its own slice of `schedulable_steps` partitions. **At 100x** (5.2M steps/sec), even per-cell heaps of "all tenants with work" become large if tenant count grows proportionally; at that point we'd move to a hierarchical scheme — a coarse cell-level WFQ over *tenant bands* (grouping small tenants), with fine-grained per-tenant WFQ only within the band that currently has contention — trading a small amount of fairness precision for the selector staying O(bands) instead of O(tenants).

**Failure case, worked step-by-step — hot tenant starving quota enforcement:**

1. A large tenant pushes a monorepo commit that fans out into 2,000 steps at once, all hitting `schedulable_steps` for `tenant_id = T1` in the same partition, all with `priority_bucket = 0`.
2. `tenant_scheduling_state.running_count` for T1 races toward `quota_max` (say 200) almost instantly — 200 steps get leased and start running.
3. Meanwhile T1's `virtual_time` (which should increase as it consumes scheduler turns) is updated by a separate scheduler replica doing an `UPDATE tenant_scheduling_state SET virtual_time = virtual_time + cost WHERE tenant_id = $1`. If two scheduler replicas both lease a T1 step in the same tick and both issue this update without a compare-and-swap, the update is not lost (Postgres serializes row-level writes), but the *decision* each replica made to pick T1 next was based on a **stale read** of `virtual_time` taken before either write — both replicas independently decided "T1 has the lowest virtual_time, pick it" using the same stale snapshot, so T1 gets scheduled twice in the same round when it should only get one turn per round under WFQ. This is a classic read-then-write race on the fairness counter, not a data-loss bug — the DB stays consistent, but *fairness* silently degrades: T1 gets 2x its entitled share for that round, and a smaller tenant's step waits one extra scheduling tick.
4. Over thousands of rounds during T1's 2,000-step burst, this compounds into measurable starvation of small tenants — exactly the failure the fairness NFR exists to prevent — even though no individual query violated correctness.

**Bookkeeping/consistency mechanism — optimistic version on the fairness counter:**

```sql
ALTER TABLE tenant_scheduling_state ADD COLUMN version BIGINT NOT NULL DEFAULT 0;

-- scheduler read (per tick, per candidate tenant):
SELECT tenant_id, virtual_time, version FROM tenant_scheduling_state
WHERE tenant_id = ANY($tenant_ids_with_work) AND running_count < quota_max;

-- after selecting T1 and leasing a step, the scheduler must win this CAS before the pick is final:
UPDATE tenant_scheduling_state
SET virtual_time = virtual_time + $cost, version = version + 1
WHERE tenant_id = $1 AND version = $read_version;
-- if 0 rows affected: another replica already advanced T1's turn this round; release the lease candidate and re-select.
```

**Corrected design:** the scheduler's per-tick selection becomes "read virtual_time + version, tentatively lease a step, then CAS the version — if the CAS fails, put the leased step back as unleased and re-run selection." This closes the stale-read race: only one replica's advance-turn write can win per version, so T1 cannot be picked twice on the same virtual_time snapshot. The cost is a small amount of wasted work (a lease taken and released) under contention, which is strictly cheaper than the fairness violation it prevents.

---

### Deep Dive 2: Step Execution Lease & DAG State Machine

**Schema**

```sql
CREATE TABLE step_attempts (
    step_attempt_id   UUID PRIMARY KEY,
    step_id           UUID NOT NULL,
    run_id            UUID NOT NULL,
    status            TEXT NOT NULL CHECK (status IN
                        ('pending','leased','running','succeeded','failed','lease_expired')),
    lease_token       UUID NULL,
    lease_owner       TEXT NULL,          -- runner_id holding the lease
    lease_expires_at  TIMESTAMPTZ NULL,
    version           BIGINT NOT NULL DEFAULT 0,   -- CAS guard for all status transitions
    idempotency_key   TEXT NOT NULL,      -- deterministic: hash(step_id, attempt_number)
    is_idempotent     BOOLEAN NOT NULL,   -- from pipeline YAML step definition
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX ON step_attempts (run_id, status);

CREATE TABLE step_dependencies (
    run_id        UUID NOT NULL,
    step_id       UUID NOT NULL,
    depends_on    UUID NOT NULL,
    PRIMARY KEY (run_id, step_id, depends_on)
);
```

**Primary query — "is this step now runnable?"** (fires when any dependency completes):

```sql
SELECT s.step_id
FROM step_dependencies sd
JOIN step_attempts s ON s.step_id = sd.step_id AND s.run_id = sd.run_id
WHERE sd.run_id = $1
  AND sd.step_id = ANY(
      SELECT step_id FROM step_dependencies WHERE run_id = $1 AND depends_on = $2
  )
  AND s.status = 'pending'
GROUP BY s.step_id
HAVING COUNT(*) FILTER (WHERE sd.depends_on IN (
      SELECT depends_on FROM step_dependencies WHERE run_id = $1 AND step_id = s.step_id
  )) = (
      SELECT COUNT(*) FROM step_dependencies dd
      JOIN step_attempts d ON d.step_id = dd.depends_on AND d.run_id = dd.run_id
      WHERE dd.run_id = $1 AND dd.step_id = s.step_id AND d.status = 'succeeded'
  );
```

In practice this "all dependencies satisfied" check is precomputed incrementally rather than re-scanned per event: each `step_attempts` row carries a `remaining_deps` counter, decremented via `UPDATE step_attempts SET remaining_deps = remaining_deps - 1 WHERE step_id = $child AND run_id = $1 RETURNING remaining_deps`, and the step becomes runnable the moment `remaining_deps` hits 0 — O(1) per completion event instead of a graph re-scan. **At 10x/100x load**, the join-based query above would become the bottleneck first (it's O(DAG size) per completion event); the counter-decrement approach is what actually scales, and is the corrected design referenced below.

**Partition-key reasoning:** `step_attempts` is keyed by `step_attempt_id` but the hot lookup pattern is "all steps for this run" (`run_id, status`), so it's indexed, not partitioned, on `(run_id, status)` — partitioning by `run_id` itself would be wrong because a single run's ~500 steps would all land in one partition, recreating a hot-partition problem at the *run* level for large monorepo DAGs; keeping the table hash-partitioned on `step_attempt_id` (uniform random) and relying on the secondary index for the run-scoped query gets uniform write distribution while still serving the read pattern efficiently.

**Failure/edge case, worked step-by-step — worker crash mid-deploy-step:**

1. Runner R1 is leased `step_attempt_id = A` for a `terraform apply` step (`is_idempotent = false`). Lease: `lease_token = L1, lease_owner = 'R1', lease_expires_at = now() + 30s, status = 'leased'`.
2. R1 transitions status to `running` and starts sending heartbeats every 10s to renew the lease (`lease_expires_at = now() + 30s` on each heartbeat, CAS'd against `lease_token = L1`).
3. R1's underlying VM is reclaimed by the cloud provider mid-`terraform apply` — after the apply has already mutated real infrastructure but before it reported success. R1 sends no more heartbeats.
4. At `lease_expires_at`, a lease-reaper process (polling `WHERE status IN ('leased','running') AND lease_expires_at < now()`) marks the attempt `lease_expired` and — this is the critical decision point — **must not** simply create a new StepAttempt and re-run the step, because the terraform apply may have partially or fully succeeded; blindly retrying risks a second concurrent apply against the same state, a classic double-execution of non-idempotent infrastructure code.
5. Because `is_idempotent = false`, the reaper does **not** auto-retry. It transitions the Step (not just the attempt) to `failed` with reason `lease_expired_non_idempotent`, and surfaces this to the user as "step outcome unknown — manual verification required before retry," rather than silently re-running. For `is_idempotent = true` steps (e.g. a build/test step with no external side effects), the reaper *does* auto-create a new StepAttempt with a fresh `idempotency_key = hash(step_id, attempt_number + 1)`.

**Bookkeeping mechanism — the lease itself, with explicit CAS on every transition:**

```sql
-- acquiring a lease (scheduler, after WFQ selection):
UPDATE step_attempts
SET status = 'leased', lease_token = gen_random_uuid(), lease_owner = $runner_id,
    lease_expires_at = now() + interval '30 seconds', version = version + 1
WHERE step_attempt_id = $1 AND status = 'pending' AND version = $expected_version
RETURNING lease_token;
-- 0 rows = another scheduler replica already leased it; abort, no double-assignment.

-- heartbeat renewal (runner, every 10s):
UPDATE step_attempts
SET lease_expires_at = now() + interval '30 seconds', version = version + 1
WHERE step_attempt_id = $1 AND lease_token = $held_token AND version = $last_known_version
RETURNING version;
-- 0 rows = lease was reaped out from under this runner (it was too slow/network-partitioned);
-- runner MUST stop work immediately and not report a terminal status — its lease is no longer valid.

-- terminal report (runner):
UPDATE step_attempts
SET status = $succeeded_or_failed, version = version + 1
WHERE step_attempt_id = $1 AND lease_token = $held_token
RETURNING step_attempt_id;
-- 0 rows = lease already expired/reaped; the runner's result is discarded even if the work "succeeded,"
-- because ownership of the outcome already transferred to the reaper's failure path.
```

The lease token plus version CAS is what gives at-most-once-effect *authority*, even though execution itself is only at-least-once at the infrastructure level: only the runner currently holding a live, unexpired `lease_token` is permitted to write a terminal status, and a network-partitioned runner that finishes work after its lease expired has its result silently discarded rather than raced into the state store.

**Corrected design (from the failure case above):** the initial "obvious" design — auto-retry every lease-expired step with a new attempt — is unsafe for the ~30% of steps in a typical pipeline that are non-idempotent (deploys, publishes, DB migrations). The corrected design splits reaper behavior on `is_idempotent`, and additionally requires idempotent-step retries to carry a stable `idempotency_key` derived from `(step_id, attempt_number)` so that even if a stale runner's write briefly races the reaper's retry-creation (both think they're "attempt 2"), the downstream execution target (e.g. a build system) can dedupe on that key rather than relying purely on the DB CAS.

---

### Step 3: Worked Follow-Up Questions

1. **"What happens if the reaper itself crashes while marking a lease expired?"** The reaper is stateless and idempotent by construction — it only ever does `UPDATE ... WHERE lease_expires_at < now() AND version = $v`, so a crashed-and-restarted reaper (or multiple reaper replicas) re-scanning the same overdue rows just re-issues the same CAS, which either succeeds once or finds the row already transitioned (0 rows affected, no-op). No coordination lock is needed between reaper replicas because the CAS itself is the coordination.

2. **"How do you avoid the lease-reaper's polling query itself becoming a hot scan at 100x scale?"** `WHERE status IN ('leased','running') AND lease_expires_at < now()` needs a partial index: `CREATE INDEX ON step_attempts (lease_expires_at) WHERE status IN ('leased','running');` — this keeps the reaper's working set to only in-flight attempts (a small fraction of the table at any instant), not a scan of historical terminal-status rows.

3. **"Two steps both depend on a step that fails — what happens to the DAG?"** Both dependents transition directly to `skipped` (not `pending` forever) via the same `remaining_deps` counter mechanism: a failed dependency triggers a fanout that marks all *transitive* downstream steps `skipped` rather than decrementing their counters, specifically to avoid a dependent step waiting on a counter that will never reach zero because one of its inputs failed instead of succeeding.

4. **"What if a tenant's `weight` changes mid-burst (e.g. they upgrade their plan while 2,000 steps are queued)?"** `virtual_time` is deliberately *not* renormalized retroactively — the new weight only affects the rate at which `virtual_time` accrues on *future* scheduling rounds. Retroactively rewriting virtual_time for already-queued work would require locking the tenant's entire queue and is not worth the complexity for a rare event; the tenant sees improved fairness within one scheduling round of the plan change, not instantaneously.

5. **"Why not use a distributed lock (e.g. Redis/etcd) instead of a DB-row lease for step execution?"** A DB-row CAS lease piggybacks on the same store that already holds the source-of-truth DAG state, giving atomicity between "who owns this step" and "what is this step's status" for free within one transaction. A separate lock service (Redis/etcd) would require a two-system consistency story — e.g. what happens if the lock is acquired in Redis but the subsequent state-store write fails — which reintroduces exactly the kind of split-brain risk the lease is meant to eliminate.

6. **"How do you bound `schedulable_steps` table growth for a tenant that queues far more work than its quota allows?"** Admission control at the Trigger Service layer, not the scheduler: when materializing a Run's Steps, if a tenant's `pending + running` count would exceed a hard ceiling well above `quota_max` (a burst allowance, not the steady-state quota), new Steps are created with `status = 'blocked_admission'` and are periodically promoted to `pending` as older work completes — this keeps the actively-schedulable set bounded regardless of how much a single tenant's monorepo fans out.

7. **"How does live log tailing avoid overwhelming the state store described above?"** It deliberately doesn't touch `step_attempts` at all — log chunks flow Runner → local agent → Kafka topic keyed by `step_attempt_id`, with the live-tail WebSocket path consuming directly from Kafka (a short retention hot topic) while a separate consumer group asynchronously drains to blob storage for durable/cold access. This is intentionally decoupled from the DAG state machine's CAS-heavy write path in Deep Dive 2, since log volume (2.6 GB/sec) and metadata volume (150K writes/sec) have completely different scaling profiles and coupling them would let log burstiness degrade scheduling correctness.

8. **"What's the failure mode if the Scheduler cell for a tenant band goes down entirely?"** Because `schedulable_steps` is durably persisted (not held in the scheduler's memory) and hash-partitioned by `tenant_id`, a dead scheduler cell doesn't lose queued work — it just stalls scheduling for the tenants in its shard until the cell is replaced/failed-over, at which point the new cell resumes by reading the same durable partition. The `lease_expires_at` reaper independently continues to reclaim any in-flight leases whose owning runners also went dark, so recovery doesn't depend on the scheduler cell's memory state at all.

*(Remaining follow-ups, unworked — short prompts only: How would you support step-level manual approval gates in this state machine? How do you handle a Step that legitimately runs longer than any reasonable lease TTL, e.g. a 6-hour integration test? How would cross-run build caching change the Artifact schema? How do you prevent a malicious pipeline YAML from defining a cyclic DAG? What's your rollback strategy if a scheduler deploy introduces a WFQ bug that mis-prioritizes all tenants? How do you test the lease-CAS logic for the crash scenarios above? How would you shard `step_dependencies` differently if DAGs became much wider (10,000+ parallel steps) rather than deep? How do you handle clock skew between the reaper's `now()` and a runner's local clock for lease expiry?)*

---

## Final Section — Staff-Level Summary

**Key architectural decisions:** at-least-once execution + CAS-guarded leases instead of attempting true exactly-once; hash-partitioned per-tenant scheduling queues with weighted fair queuing instead of a global FIFO; complete decoupling of the log-ingest path (Kafka/blob) from the DAG state machine (transactional DB); split retry behavior on step idempotency rather than a uniform retry policy.

**Biggest tradeoffs:** choosing eventual/CAS-based fairness over a stronger but slower coordination mechanism (accepting occasional wasted lease-then-release cycles under contention); choosing not to renormalize virtual_time on plan changes (simplicity over perfect instantaneous fairness); choosing admission control over unbounded queue growth (a burst-tolerant tenant experience takes a backseat to system-wide bounded resource use).

**Biggest risks:** the non-idempotent-step lease-expiry path is the single highest-consequence failure mode in the whole system — getting the `is_idempotent` classification wrong on even one dangerous step type (e.g. treating a DB migration as idempotent when it isn't) silently reintroduces the exact double-execution risk the entire lease design exists to prevent; the WFQ selector's stale-read race, if the CAS fix were skipped, would be a slow-burning fairness bug that's hard to detect until a large tenant complains.

| Dimension | Score |
|---|---|
| Problem Framing | 9/10 |
| Requirements | 8/10 |
| NFRs | 8/10 |
| Capacity Planning | 9/10 |
| Data Modeling | 9/10 |
| Architecture | 8/10 |
| Tradeoffs | 9/10 |
| Failure Analysis | 9/10 |
| Product Thinking | 7/10 |
| **Overall** | **8.5/10** |

To reach Senior Staff/Principal level, the answer would need to go further on the *organizational* dimension of this system — how do you roll out a scheduler fairness-algorithm change across a fleet already running 4.7M concurrent containers without a flag-day cutover, how do you migrate the `step_attempts` schema (e.g. adding the version/CAS columns shown here) on a live table taking 150K writes/sec without downtime, and how do you design the tenant-facing SLA/error-budget story so that the "non-idempotent step failed with unknown outcome" case in Deep Dive 2 has a defined, contractual customer experience rather than just a correct engineering answer.
