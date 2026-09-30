"""Seed 3 new HLD questions into MongoDB with full staff-level breakdowns.

Run: python seed_new_questions.py
"""

import asyncio
import os
from datetime import datetime

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

MONGODB_URI = os.getenv("MONGODB_URI")

# ─── Question 1: Distributed Rate Limiter ────────────────────────

RATE_LIMITER_BREAKDOWN = {
    "focusAreas": ["Distributed Systems", "Concurrency Control", "Cross-Region Consistency", "Hot-Key Handling"],
    "targetRole": "Staff Engineer",
    "totalSections": 10,
    "completedSections": 0,
    "sections": [
        {
            "id": "interview-context",
            "stepNumber": 1,
            "label": "CONTEXT",
            "title": "Interview Context",
            "blocks": [
                {"type": "text", "content": "This is a 'small surface area, deep water' problem — the API is trivial (allow(key) → bool), which is exactly why it's a good L7 filter: candidates who stay at the algorithm level (token bucket vs sliding window) top out at L5. The hidden challenges are distributed-systems ones wearing a disguise."},
                {"type": "callout", "variant": "warning", "title": "What the Interviewer Really Wants", "content": "A strong L7 candidate will proactively raise the tension between strict correctness (never let a single request slip past the limit) and availability/latency (a rate limiter sitting in the hot path cannot itself add meaningful tail latency, and must fail open or closed predictably)."},
                {"type": "text", "content": "Likely probe areas: hot-key behavior for a single viral API key or IP, cross-region/global limit enforcement, the exactly-once-adjacent problem of atomic check-and-increment under concurrency, and graceful degradation when the counter store is unreachable."},
            ],
        },
        {
            "id": "requirements",
            "stepNumber": 2,
            "label": "REQUIREMENTS",
            "title": "Requirements",
            "blocks": [
                {"type": "functional-nonfunctional",
                 "functional": [
                     "check_and_consume(key, cost=1) → {allowed, remaining, reset_at} — atomic decision",
                     "Multiple concurrent algorithms per key-class (token bucket for smooth APIs, fixed/sliding window for simple quotas)",
                     "Dynamic, hot-reloadable limit configuration per key",
                     "Global (multi-region) limit enforcement for a subset of keys",
                 ],
                 "nonFunctional": [
                     "Decision latency: <5ms p99, <1ms p50",
                     "Availability: 99.99% on the decision path",
                     "Throughput: 2M decisions/sec sustained, 5M burst",
                     "Correctness: no more than ~1-2% over-admission during races, 0% under-admission",
                     "Config propagation: <5s from write to global enforcement",
                 ]},
                {"type": "callout", "variant": "info", "title": "Stated Assumptions", "content": "Platform-wide limiter-as-a-service fronting hundreds of downstream APIs. Limits are composable (per-API-key AND per-IP). Config is hot-reloadable. Fail-open on counter-store outage with a local fallback limiter. Slight over-admission during network partitions is acceptable. Global (cross-region) limits needed for a subset of premium keys."},
            ],
        },
        {
            "id": "capacity",
            "stepNumber": 3,
            "label": "CAPACITY",
            "title": "Capacity Planning",
            "blocks": [
                {"type": "text", "content": "Peak platform QPS: 2,000,000 req/s. Composable limiting (per-API-key + per-IP) → ~2× counter operations per request → 4,000,000 counter ops/sec."},
                {"type": "text", "content": "Distinct active keys: ~50M API keys + ~200M active IPs in any 5-min window → ~250M active counter entries. Per-entry state (token bucket): ~100B/entry. Total hot-state memory: ~25 GB raw — budget ~100-150 GB across a Redis Cluster with replication."},
                {"type": "text", "content": "Network: 4M ops/sec × ~150B request/response ≈ ~1.2 GB/s aggregate to the counter tier — this is the real scaling constraint, not CPU or memory."},
                {"type": "callout", "variant": "definition", "title": "System Profile", "content": "Extremely write-heavy (every request is a read-modify-write), latency-critical, memory-resident, network-throughput-bound. Not storage-heavy, not compute-heavy."},
            ],
        },
        {
            "id": "entities",
            "stepNumber": 4,
            "label": "ENTITIES",
            "title": "Core Domain Model",
            "blocks": [
                {"type": "entity-table", "entities": [
                    {"name": "RateLimitRule", "purpose": "Defines algorithm (token bucket / sliding window), capacity, refill rate, key pattern, scope (regional/global)"},
                    {"name": "LimitCounterState", "purpose": "Live, mutable per-key state: current tokens/count, last-updated timestamp. Lives in the counter store, not a durable record"},
                    {"name": "DecisionAuditEvent", "purpose": "Sampled/aggregated record of allow/deny decisions fed to analytics (async, off critical path)"},
                    {"name": "TenantConfig", "purpose": "Maps a tenant/API to applicable RateLimitRule(s); supports composition (multiple rules AND'd together)"},
                ]},
            ],
        },
        {
            "id": "api-design",
            "stepNumber": 5,
            "label": "API DESIGN",
            "title": "API Design",
            "blocks": [
                {"type": "api-table", "endpoints": [
                    {"method": "POST", "endpoint": "/v1/check", "description": "Atomic check-and-consume with composable keys and per-key remaining/limit/reset info"},
                    {"method": "PUT", "endpoint": "/v1/rules/{rule_id}", "description": "Create or update a rate limit rule (admin path, low QPS, strongly consistent)"},
                ]},
                {"type": "callout", "variant": "warning", "title": "Idempotency", "content": "The /v1/check endpoint is intentionally NOT idempotent — each call consumes quota. Mitigate client retries by having the client pass a decision_id (request UUID); the limiter caches the result for that ID for a short TTL (~2s) and returns the cached result on retry."},
            ],
        },
        {
            "id": "hld",
            "stepNumber": 6,
            "label": "HIGH-LEVEL DESIGN",
            "title": "High-Level Architecture",
            "blocks": [
                {"type": "architecture-flow", "nodes": [
                    {"label": "Client SDK / Sidecar", "type": "supporting"},
                    {"label": "Limiter Decision Service", "type": "critical"},
                    {"label": "Redis Cluster (Counter Store)", "type": "critical"},
                    {"label": "Config Store (etcd/Consul)", "type": "supporting"},
                    {"label": "L1 Local Cache (Fallback)", "type": "supporting"},
                    {"label": "Kafka (Audit Pipeline)", "type": "supporting"},
                ], "connections": [
                    {"from": "Client SDK / Sidecar", "to": "Limiter Decision Service", "style": "unidirectional"},
                    {"from": "Limiter Decision Service", "to": "Redis Cluster (Counter Store)", "style": "bidirectional"},
                    {"from": "Config Store (etcd/Consul)", "to": "Limiter Decision Service", "style": "unidirectional"},
                    {"from": "Limiter Decision Service", "to": "L1 Local Cache (Fallback)", "style": "bidirectional"},
                    {"from": "Limiter Decision Service", "to": "Kafka (Audit Pipeline)", "style": "unidirectional"},
                ], "explanation": "The Decision Service is stateless — it resolves applicable rules from its local config cache, computes counter keys, and issues a single atomic Lua script call to the appropriate Redis shard. If the Counter Store times out, it falls back to the local approximate limiter and fails open."},
            ],
        },
        {
            "id": "tradeoffs",
            "stepNumber": 7,
            "label": "TRADE-OFFS",
            "title": "Key Trade-offs",
            "blocks": [
                {"type": "comparison", "title": "Algorithm: Fixed Window vs Token Bucket", "optionA": {"label": "Fixed Window Counter", "description": "Simple, easy to implement"}, "optionB": {"label": "Token Bucket / Sliding Window", "description": "Smooth rate limiting without boundary bursts"}, "recommendation": "Token Bucket", "rationale": "Fixed window allows 2x burst at window boundaries; token bucket smooths without storing per-request logs."},
                {"type": "comparison", "title": "Counter Store: Durable DB vs In-Memory Cache", "optionA": {"label": "Strongly-consistent DB (CP store)", "description": "Durable, ACID guarantees"}, "optionB": {"label": "Redis Cluster with atomic Lua scripts", "description": "Sub-ms latency, ephemeral/recomputable state"}, "recommendation": "Redis Cluster", "rationale": "Latency budget (<5ms p99) rules out a durable DB round trip; rate-limit state is inherently ephemeral."},
                {"type": "comparison", "title": "Failure Mode: Fail Closed vs Fail Open", "optionA": {"label": "Fail Closed", "description": "Reject all traffic when counter store is unreachable"}, "optionB": {"label": "Fail Open with local fallback", "description": "Approximate local limiting, emit degradation metrics"}, "recommendation": "Fail Open", "rationale": "This is a protection mechanism, not a security boundary. Failing closed turns a cache outage into a full platform outage."},
                {"type": "comparison", "title": "Config Propagation: Direct Read vs Cached + Push", "optionA": {"label": "Every decision reads config store", "description": "Always fresh, simple"}, "optionB": {"label": "Local cache + pub/sub push on change", "description": "Sub-5s propagation, massive read savings"}, "recommendation": "Local cache + push", "rationale": "Config reads at 4M ops/sec would overwhelm any config store. Requirement is 5s propagation, not synchronous consistency."},
            ],
        },
        {
            "id": "deep-dive-1",
            "stepNumber": 8,
            "label": "DEEP DIVE",
            "title": "Atomic Check-and-Consume (Lua Script)",
            "blocks": [
                {"type": "text", "content": "The single most important design fact: Redis executes Lua scripts single-threadedly and atomically per shard. This eliminates the TOCTOU race where two Decision Service instances both read tokens=1, both decide to allow, both write tokens=0 — one request that should have been denied was admitted."},
                {"type": "callout", "variant": "definition", "title": "Token Bucket Lua Script", "content": "The Lua script performs: (1) read current tokens and last_refill timestamp, (2) refill based on elapsed time, (3) check if tokens >= cost, (4) deduct if allowed — all in one atomic round trip. Each key also gets a PEXPIRE TTL of (capacity / refill_rate) × 2, so idle keys self-expire."},
                {"type": "callout", "variant": "warning", "title": "Hot-Key Failure Case", "content": "At 200K req/s on a single viral API key, every request hashes to the same Redis shard. That shard's single-threaded event loop saturates, and unrelated tenants sharing that shard see latency spikes. The fix: split the key into N sub-keys across different shards, each holding capacity/N tokens, trading precision for throughput."},
            ],
        },
        {
            "id": "deep-dive-2",
            "stepNumber": 9,
            "label": "DEEP DIVE",
            "title": "Cross-Region Global Limits",
            "blocks": [
                {"type": "text", "content": "A premium tenant's API key has one logical limit (e.g., 10,000 req/min) that must hold in aggregate across US, EU, and APAC regional clusters, each running its own Counter Store for latency reasons."},
                {"type": "text", "content": "Mechanism: each region maintains a LOCAL counter plus a 'global_capacity_share' that's periodically refreshed via a background sync (~500ms-1s). The aggregator redistributes capacity proportionally to each region's recent demand."},
                {"type": "callout", "variant": "warning", "title": "Split-Brain Failure", "content": "During a sync partition, if US's redistribution logic isn't watermark-aware, it could bump its own share based on stale assumptions: US(8,000) + EU(4,000) = 12,000, exceeding the global 10,000 limit by 20%."},
                {"type": "callout", "variant": "definition", "title": "The Asymmetric Fix", "content": "The corrected redistribution rule is asymmetric: decrease your local share unilaterally on any signal of staleness; only increase your local share on a freshly-confirmed sync. This single asymmetry converts unbounded split-brain over-admission into a bounded one."},
            ],
        },
        {
            "id": "summary",
            "stepNumber": 10,
            "label": "SUMMARY",
            "title": "Staff-Level Summary",
            "blocks": [
                {"type": "text", "content": "Key architectural decisions: (1) Single-round-trip atomic Lua script as the concurrency-control primitive, eliminating the check-then-write race. (2) Key-hash-based sharding (never time-based), with dynamic sub-key sharding for hot keys. (3) Asymmetric redistribution rule for cross-region global limits."},
                {"type": "text", "content": "Biggest tradeoffs: Fail-open with local approximate fallback trades strict correctness for availability. Global limits are eventually-consistent by design."},
                {"type": "text", "content": "Biggest risks: Hot-key detection is reactive-by-sampling unless proactively built. The idempotency decision_id mechanism is easy to hand-wave; without it, client retry storms silently double-consume quota."},
                {"type": "callout", "variant": "info", "title": "Path to Principal", "content": "A Principal-level answer would address how this becomes a platform primitive other teams build on, how the hot-key detector's signal could be shared with a broader abuse-prevention system, and which specific business risk each tradeoff protects against."},
            ],
        },
    ],
}


# ─── Question 2: CI/CD Platform ──────────────────────────────────

CICD_BREAKDOWN = {
    "focusAreas": ["Workflow Orchestration", "Multi-Tenancy", "Exactly-Once Execution", "Fair Scheduling"],
    "targetRole": "Staff Engineer",
    "totalSections": 10,
    "completedSections": 0,
    "sections": [
        {
            "id": "interview-context",
            "stepNumber": 1,
            "label": "CONTEXT",
            "title": "Interview Context",
            "blocks": [
                {"type": "text", "content": "This is a workflow-orchestration-under-multi-tenancy problem, structurally close to Temporal/Airflow but with a hard real-time UX layer (live logs, live status) bolted on."},
                {"type": "callout", "variant": "warning", "title": "Hidden Challenges", "content": "The 'obvious' design (queue + workers + Postgres) breaks in three distinct ways: (a) noisy-neighbor starvation, (b) at-least-once execution corrupting non-idempotent build steps (e.g. terraform apply, npm publish), and (c) unbounded log storage cost. A Staff engineer anticipates all three before writing code."},
                {"type": "text", "content": "Likely probes: how do you keep one tenant's 10,000-job monorepo from starving everyone else, how do you guarantee a step doesn't run twice, how do you stream logs from an ephemeral pod, how do you replay/rerun from a mid-pipeline failure without redoing everything."},
            ],
        },
        {
            "id": "requirements",
            "stepNumber": 2,
            "label": "REQUIREMENTS",
            "title": "Requirements",
            "blocks": [
                {"type": "functional-nonfunctional",
                 "functional": [
                     "Define pipelines as DAGs of steps (YAML) with dependency edges, retries, and conditional execution",
                     "Trigger on git push/PR/tag/schedule/manual",
                     "Schedule steps onto a runner fleet with per-tenant fairness",
                     "Stream logs live and persist them durably",
                     "Guarantee each step executes with at-most-once effect even under worker crash",
                     "Artifact passing between steps (build output → deploy step)",
                 ],
                 "nonFunctional": [
                     "Step scheduling latency: p50 <5s, p99 <30s",
                     "Log delivery latency: <2s end-to-end",
                     "Execution correctness: zero tolerance for double-running non-idempotent steps",
                     "Availability (control plane): 99.95%",
                     "Fairness: max wait-time skew bounded by weighted-fair-share",
                     "Log/artifact durability: 99.999%",
                 ]},
                {"type": "callout", "variant": "info", "title": "Stated Assumptions", "content": "Multi-tenant SaaS, hosted ephemeral runners (containers), live log streaming required, pipelines defined as YAML DAGs with a mix of idempotent and non-idempotent steps, hard per-tenant concurrency quotas, forked-PR builds run in a stronger sandbox. Scale: 50M pipeline runs/day."},
            ],
        },
        {
            "id": "capacity",
            "stepNumber": 3,
            "label": "CAPACITY",
            "title": "Capacity Planning",
            "blocks": [
                {"type": "text", "content": "Pipeline runs: 50M/day → ~580/sec average, peak (~6x) ≈ 3,500 runs/sec. Steps per run: avg 15 → ~52,000 steps/sec at peak. Step duration: avg 90s → ~4.7M concurrent containers at peak (platform-wide, sharded across regions/cells)."},
                {"type": "text", "content": "Log volume: avg step emits 50KB logs → 2.6 GB/sec log ingest at peak, ~37.5 TB/day before compression."},
                {"type": "text", "content": "Metadata: 50M runs × 15 steps × ~1KB × 3 writes/step = ~2.25B row writes/day ≈ 150K/sec peak."},
                {"type": "callout", "variant": "definition", "title": "System Profile", "content": "Write-heavy on metadata (state transitions), throughput-heavy on logs (blob storage, not a database problem), and scheduling-heavy on the control plane (packing problem, not a storage problem)."},
            ],
        },
        {
            "id": "entities",
            "stepNumber": 4,
            "label": "ENTITIES",
            "title": "Core Domain Model",
            "blocks": [
                {"type": "entity-table", "entities": [
                    {"name": "Pipeline", "purpose": "YAML-defined DAG template, versioned per commit. Belongs to a Repo/Tenant"},
                    {"name": "Run", "purpose": "One execution instance of a Pipeline, triggered by an event (queued/running/succeeded/failed/cancelled)"},
                    {"name": "Step", "purpose": "One node in the DAG for a given Run. Has dependencies, status, assigned Runner, retry count"},
                    {"name": "StepAttempt", "purpose": "One execution attempt of a Step (retries/crash-recovery). Maps to a container"},
                    {"name": "Runner", "purpose": "Ephemeral compute unit (container/VM) that executes exactly one StepAttempt at a time"},
                    {"name": "Tenant", "purpose": "Owns Pipelines, has a compute quota and scheduling weight"},
                    {"name": "Artifact", "purpose": "Blob produced by a Step, referenced by downstream Steps via content hash"},
                    {"name": "LogChunk", "purpose": "Ordered chunk of log output for a StepAttempt, streamed and persisted"},
                ]},
            ],
        },
        {
            "id": "api-design",
            "stepNumber": 5,
            "label": "API DESIGN",
            "title": "API Design",
            "blocks": [
                {"type": "api-table", "endpoints": [
                    {"method": "POST", "endpoint": "/v1/runs", "description": "Create a new pipeline run with idempotency_key to dedupe replayed webhooks"},
                    {"method": "GET", "endpoint": "/v1/runs/{run_id}", "description": "Get run status with all steps and their statuses"},
                    {"method": "POST", "endpoint": "/v1/runs/{run_id}/steps/{step_id}/retry", "description": "Retry a step — creates a new StepAttempt, safe to double-click"},
                    {"method": "GET", "endpoint": "/v1/runs/{run_id}/steps/{step_id}/logs", "description": "Chunked log stream with monotonic offsets (also WebSocket for live tail)"},
                    {"method": "POST", "endpoint": "/internal/runner/{runner_id}/heartbeat", "description": "Lease renewal call with step_attempt_id and lease_token"},
                ]},
            ],
        },
        {
            "id": "hld",
            "stepNumber": 6,
            "label": "HIGH-LEVEL DESIGN",
            "title": "High-Level Architecture",
            "blocks": [
                {"type": "architecture-flow", "nodes": [
                    {"label": "Webhook Ingest", "type": "supporting"},
                    {"label": "Trigger Service", "type": "critical"},
                    {"label": "Scheduler (WFQ)", "type": "critical"},
                    {"label": "Runner Fleet", "type": "critical"},
                    {"label": "State Store (Postgres)", "type": "critical"},
                    {"label": "Log Pipeline (Kafka → S3)", "type": "supporting"},
                    {"label": "Artifact Store (S3)", "type": "supporting"},
                ], "connections": [
                    {"from": "Webhook Ingest", "to": "Trigger Service", "style": "unidirectional"},
                    {"from": "Trigger Service", "to": "State Store (Postgres)", "style": "unidirectional"},
                    {"from": "Scheduler (WFQ)", "to": "State Store (Postgres)", "style": "bidirectional"},
                    {"from": "Scheduler (WFQ)", "to": "Runner Fleet", "style": "unidirectional"},
                    {"from": "Runner Fleet", "to": "Log Pipeline (Kafka → S3)", "style": "unidirectional"},
                    {"from": "Runner Fleet", "to": "State Store (Postgres)", "style": "unidirectional"},
                ], "explanation": "A push event is deduped at Webhook Ingest, materialized into Steps by the Trigger Service, and assigned to Runners by the Scheduler under the tenant's fair-share weight. Logs flow through Kafka to both a hot live-tail path and cold blob storage, completely decoupled from the DAG state machine."},
            ],
        },
        {
            "id": "tradeoffs",
            "stepNumber": 7,
            "label": "TRADE-OFFS",
            "title": "Key Trade-offs",
            "blocks": [
                {"type": "comparison", "title": "Execution Guarantee", "optionA": {"label": "Exactly-once execution", "description": "Distributed transactions across workers"}, "optionB": {"label": "At-least-once + lease layer", "description": "Lease-based at-most-once-effect"}, "recommendation": "At-least-once + leases", "rationale": "True exactly-once across a crash-prone container fleet is not achievable without unacceptable latency. Lease-based at-most-once-effect is the standard, provable pattern."},
                {"type": "comparison", "title": "Scheduler Architecture", "optionA": {"label": "Central scheduler", "description": "Single decision-maker, simple"}, "optionB": {"label": "Sharded/cell-based schedulers", "description": "Per region+tenant-band, bounded blast radius"}, "recommendation": "Cell-based", "rationale": "A single scheduler at 4.7M concurrent containers is a throughput and blast-radius risk."},
                {"type": "comparison", "title": "Fairness Mechanism", "optionA": {"label": "FIFO global queue", "description": "Simple, first-come first-served"}, "optionB": {"label": "Weighted fair queuing per tenant", "description": "Computed at dequeue time"}, "recommendation": "Weighted fair queuing", "rationale": "FIFO lets one large monorepo's burst starve small tenants — directly violates the fairness NFR."},
                {"type": "comparison", "title": "Log Storage", "optionA": {"label": "Write logs to Postgres", "description": "Co-locate with state DB"}, "optionB": {"label": "Kafka → blob storage (S3)", "description": "Separate hot and cold paths"}, "recommendation": "Kafka → S3", "rationale": "Logs are 50x the write volume of metadata. Co-locating them with transactional state would tank state-store performance."},
            ],
        },
        {
            "id": "deep-dive-1",
            "stepNumber": 8,
            "label": "DEEP DIVE",
            "title": "Scheduler / Fair-Share Queue",
            "blocks": [
                {"type": "text", "content": "The schedulable_steps table is hash-partitioned on tenant_id. This avoids the hot-partition problem of time-based partitioning where every scheduler worker's dequeue scan hits the same leading edge."},
                {"type": "text", "content": "Tenant selection uses Weighted Fair Queuing (WFQ): a min-heap of tenants sorted by virtual_time. The tenant with the lowest virtual_time and available quota gets the next scheduling slot."},
                {"type": "callout", "variant": "warning", "title": "Stale-Read Race on Fairness Counter", "content": "Two scheduler replicas both read the same stale virtual_time for tenant T1, both pick T1, both lease a step — T1 gets 2x its entitled share. Over thousands of rounds during a burst, this compounds into measurable starvation of small tenants."},
                {"type": "callout", "variant": "definition", "title": "The Fix: Optimistic CAS", "content": "Add a version column to tenant_scheduling_state. After selecting a tenant and leasing a step, the scheduler must CAS: UPDATE SET virtual_time = virtual_time + cost, version = version + 1 WHERE version = read_version. If 0 rows affected, another replica already advanced this turn — release the lease and re-select."},
            ],
        },
        {
            "id": "deep-dive-2",
            "stepNumber": 9,
            "label": "DEEP DIVE",
            "title": "Step Execution Lease & DAG State Machine",
            "blocks": [
                {"type": "text", "content": "The step_attempts table tracks lease_token, lease_owner, lease_expires_at, and a version for CAS. Only the runner currently holding a live, unexpired lease_token is permitted to write a terminal status."},
                {"type": "callout", "variant": "warning", "title": "Worker Crash Mid-Deploy", "content": "A runner executing terraform apply is reclaimed mid-operation. The lease-reaper marks the attempt lease_expired. Because is_idempotent = false, the reaper does NOT auto-retry — it transitions the Step to 'failed' with reason 'lease_expired_non_idempotent' and surfaces it for manual verification. For idempotent steps, the reaper auto-creates a new StepAttempt."},
                {"type": "text", "content": "The lease token plus version CAS gives at-most-once-effect authority: a network-partitioned runner that finishes work after its lease expired has its result silently discarded rather than raced into the state store."},
                {"type": "callout", "variant": "info", "title": "Why DB-Row Lease, Not Redis/etcd?", "content": "A DB-row CAS lease piggybacks on the same store that holds the source-of-truth DAG state, giving atomicity between 'who owns this step' and 'what is this step's status' in one transaction. A separate lock service would require a two-system consistency story."},
            ],
        },
        {
            "id": "summary",
            "stepNumber": 10,
            "label": "SUMMARY",
            "title": "Staff-Level Summary",
            "blocks": [
                {"type": "text", "content": "Key decisions: at-least-once execution + CAS-guarded leases; hash-partitioned per-tenant scheduling with WFQ; complete decoupling of log-ingest from DAG state machine; split retry behavior on step idempotency."},
                {"type": "text", "content": "Biggest risks: The non-idempotent-step lease-expiry path is the highest-consequence failure mode. Getting the is_idempotent classification wrong reintroduces the exact double-execution risk the entire lease design exists to prevent."},
                {"type": "callout", "variant": "info", "title": "Path to Principal", "content": "A Principal-level answer would address: how to roll out a scheduler fairness-algorithm change across a fleet running 4.7M concurrent containers without a flag-day cutover, how to migrate the step_attempts schema on a live table at 150K writes/sec without downtime, and how to design the tenant-facing SLA for the 'non-idempotent step failed with unknown outcome' case."},
            ],
        },
    ],
}


# ─── Question 3: Observability Platform ──────────────────────────

OBSERVABILITY_BREAKDOWN = {
    "focusAreas": ["Time-Series Data", "Distributed Tracing", "Multi-Tenancy", "Cardinality Management"],
    "targetRole": "Staff Engineer",
    "totalSections": 10,
    "completedSections": 0,
    "sections": [
        {
            "id": "interview-context",
            "stepNumber": 1,
            "label": "CONTEXT",
            "title": "Interview Context",
            "blocks": [
                {"type": "text", "content": "This is a multi-workload data-platform problem — the candidate must design metrics ingestion, distributed tracing, and alerting as three coupled but distinctly-shaped subsystems under one multi-tenant umbrella."},
                {"type": "callout", "variant": "warning", "title": "Why This Is a Good L7 Problem", "content": "There's no single 'right' datastore. Naive candidates reach for 'just use Cassandra for everything' and miss that metrics cardinality explosion, trace-assembly ordering, and alert-evaluation latency each demand different tradeoffs."},
                {"type": "text", "content": "Hidden challenges: tag cardinality explosion (a single bad tag like user_id can create billions of unique series), out-of-order/late-arriving data, and the alerting correctness/latency tradeoff (false negatives are worse than false positives). Likely probes: cardinality control, hot partition handling, tail-based trace sampling, alert engine watermarking."},
            ],
        },
        {
            "id": "requirements",
            "stepNumber": 2,
            "label": "REQUIREMENTS",
            "title": "Requirements",
            "blocks": [
                {"type": "functional-nonfunctional",
                 "functional": [
                     "Ingest metrics (name, tags, value, timestamp) from agents at high frequency",
                     "Ingest distributed traces (spans with trace_id/span_id/parent_id) and reconstruct full traces",
                     "Define alert rules over metrics and traces, fire notifications within SLA",
                     "Dashboards: query and visualize metrics over arbitrary time windows with aggregation and group-by",
                 ],
                 "nonFunctional": [
                     "Write availability (metrics): 99.99%",
                     "Query latency (dashboards): p95 <500ms for rollup queries over 24h",
                     "Alert evaluation latency: p99 <60s from data landing to notification",
                     "Cardinality isolation: per-tenant quota enforced at ingestion",
                     "Storage cost: automatic downsampling (raw 15d, 5-min rollup 13mo)",
                     "Trace sampling: 100% of error/slow traces kept even while sampling 99% of normal traffic",
                 ]},
                {"type": "callout", "variant": "info", "title": "Scope", "content": "B2B SaaS, ~50,000 customer organizations. Scope: Metrics (time series) + Distributed Tracing (APM) + Alerting. Logs are explicitly out of scope (different cost/storage profile, would double the interview)."},
            ],
        },
        {
            "id": "capacity",
            "stepNumber": 3,
            "label": "CAPACITY",
            "title": "Capacity Planning",
            "blocks": [
                {"type": "text", "content": "Metrics: ~2M active hosts × 150 metrics/host ÷ 10s interval = 30M points/sec ingest. Each point ~24 bytes → 720 MB/s raw, ~62 TB/day before compression. With columnar + delta encoding (10-20x): ~4-6 TB/day stored."},
                {"type": "text", "content": "Cardinality: avg 20 unique tag combinations × 2M hosts × 150 metrics ≈ 6 billion active series — this number drives the hard design decisions (index size, hot-partition risk), not raw point volume."},
                {"type": "text", "content": "Tracing: 500k requests/sec platform-wide, avg 20 spans/trace → 10M spans/sec generated. With tail sampling (~1% normal kept): ~150k spans/sec ingested, ~13 TB/day."},
                {"type": "text", "content": "Alerting: 50,000 orgs × avg 20 rules = 1M active alert rules → ~20k rule-evaluations/sec."},
                {"type": "callout", "variant": "definition", "title": "System Profile", "content": "Write-heavy and storage-heavy for metrics (extreme cardinality), write-heavy and consistency-sensitive for traces (must stitch spans before sampling), read+compute-heavy for alerting (continuous streaming aggregation)."},
            ],
        },
        {
            "id": "entities",
            "stepNumber": 4,
            "label": "ENTITIES",
            "title": "Core Domain Model",
            "blocks": [
                {"type": "entity-table", "entities": [
                    {"name": "MetricSeries", "purpose": "Unique (metric_name, tag_set) combination identified by series_id hash"},
                    {"name": "MetricPoint", "purpose": "(series_id, timestamp, value) — the actual measurement, append-only"},
                    {"name": "Trace", "purpose": "(trace_id, root_span, status, duration) — logical grouping of spans for one request"},
                    {"name": "Span", "purpose": "(span_id, trace_id, parent_span_id, service_name, start_time, duration, tags)"},
                    {"name": "AlertRule", "purpose": "Control-plane definition: query, threshold, evaluation window, notification targets"},
                    {"name": "AlertEvent", "purpose": "Record of an alert transitioning firing/resolved — drives dedup and flapping suppression"},
                    {"name": "Organization", "purpose": "Multi-tenancy and billing boundary with cardinality quota and retention tier"},
                ]},
            ],
        },
        {
            "id": "api-design",
            "stepNumber": 5,
            "label": "API DESIGN",
            "title": "API Design",
            "blocks": [
                {"type": "api-table", "endpoints": [
                    {"method": "POST", "endpoint": "/v1/series", "description": "Ingest metric data points (naturally idempotent on series_id + timestamp)"},
                    {"method": "POST", "endpoint": "/v1/traces", "description": "Ingest spans (deduped on span_id at the collector)"},
                    {"method": "GET", "endpoint": "/v1/query", "description": "Rollup query routed to appropriate resolution tier based on time range"},
                    {"method": "POST", "endpoint": "/v1/alert-rules", "description": "Create alert rule with client-supplied rule_id for idempotent creation"},
                    {"method": "GET", "endpoint": "/v1/alert-events", "description": "Read current firing state — powers the alert inbox / on-call UI"},
                ]},
            ],
        },
        {
            "id": "hld",
            "stepNumber": 6,
            "label": "HIGH-LEVEL DESIGN",
            "title": "High-Level Architecture",
            "blocks": [
                {"type": "architecture-flow", "nodes": [
                    {"label": "Agent", "type": "supporting"},
                    {"label": "Ingestion Gateway", "type": "critical"},
                    {"label": "Kafka", "type": "critical"},
                    {"label": "Metrics Writer → TSDB", "type": "critical"},
                    {"label": "Trace Assembler", "type": "critical"},
                    {"label": "Alert Evaluator", "type": "critical"},
                    {"label": "Query Service", "type": "supporting"},
                    {"label": "Notification Service", "type": "supporting"},
                ], "connections": [
                    {"from": "Agent", "to": "Ingestion Gateway", "style": "unidirectional"},
                    {"from": "Ingestion Gateway", "to": "Kafka", "style": "unidirectional"},
                    {"from": "Kafka", "to": "Metrics Writer → TSDB", "style": "unidirectional"},
                    {"from": "Kafka", "to": "Trace Assembler", "style": "unidirectional"},
                    {"from": "Kafka", "to": "Alert Evaluator", "style": "unidirectional"},
                    {"from": "Alert Evaluator", "to": "Notification Service", "style": "unidirectional"},
                    {"from": "Metrics Writer → TSDB", "to": "Query Service", "style": "bidirectional"},
                ], "explanation": "Agents batch metrics/spans and push to the Ingestion Gateway. The gateway authenticates, checks cardinality quotas, and writes to Kafka partitioned by tenant. Metrics Writer, Trace Assembler, and Alert Evaluator consume independently, decoupling ingest bursts from storage backpressure."},
            ],
        },
        {
            "id": "tradeoffs",
            "stepNumber": 7,
            "label": "TRADE-OFFS",
            "title": "Key Trade-offs",
            "blocks": [
                {"type": "comparison", "title": "Metrics Storage", "optionA": {"label": "Row-store (Postgres/MySQL)", "description": "Familiar, ACID"}, "optionB": {"label": "Wide-column TSDB (Cassandra/Bigtable)", "description": "Horizontal partitioning by series, append-heavy"}, "recommendation": "Wide-column TSDB", "rationale": "Append-heavy, time-ordered writes with 6B series — row stores can't handle this write throughput."},
                {"type": "comparison", "title": "Cardinality Control", "optionA": {"label": "Allow unlimited tags", "description": "Maximum flexibility for users"}, "optionB": {"label": "Per-tenant cardinality quota at ingestion", "description": "Enforce limits before bad data enters the system"}, "recommendation": "Per-tenant quota", "rationale": "Unbounded cardinality is the #1 real-world outage cause in TSDBs — a single bad tag can 100x series count."},
                {"type": "comparison", "title": "Trace Sampling", "optionA": {"label": "Head-based", "description": "Decide at span-start"}, "optionB": {"label": "Tail-based", "description": "Decide after trace completes"}, "recommendation": "Tail-based", "rationale": "Head-based can't guarantee 100% capture of error/slow traces since you don't know the outcome yet."},
                {"type": "comparison", "title": "Rollup Strategy", "optionA": {"label": "Compute aggregates at read time", "description": "Simpler write path"}, "optionB": {"label": "Precompute rollups on write", "description": "5-min and 1-hr rollups, query raw only for short windows"}, "recommendation": "Precompute rollups", "rationale": "Read-time aggregation over 13 months of raw 10s data is infeasible; rollups trade storage for query latency."},
            ],
        },
        {
            "id": "deep-dive-1",
            "stepNumber": 8,
            "label": "DEEP DIVE",
            "title": "TSDB Schema & Hot-Partition Failure",
            "blocks": [
                {"type": "text", "content": "Partition key: (org_id, series_id, time_bucket). The time_bucket (hourly) is critical: without it, a high-frequency series creates an unbounded partition. With it, data rotates across different physical replica sets every hour — a hot series doesn't permanently pin the same 3 nodes."},
                {"type": "callout", "variant": "warning", "title": "Hot Partition from Bad Tags", "content": "A customer tags request.latency with user_id — cardinality goes from ~20 to millions. Writes to series_metadata's (org_id, metric_name) partition spike. This single partition saturates 3 replica nodes, degrading the entire org and potentially other tenants sharing those physical nodes."},
                {"type": "callout", "variant": "definition", "title": "Fix: Cardinality Counter + Partition Sharding", "content": "A per-org, per-metric cardinality counter at the ingestion gateway rejects new series once the quota is exceeded (429). Structurally: shard series_metadata's partition key to include hash(tags_hash) % N, spreading cardinality explosion across N partitions."},
                {"type": "text", "content": "The tradeoff of time-bucketed partition keys: range queries across many hours now hit many partitions (fan-out). This is solvable with parallelism and rollups; write-side unbounded/permanently-hot partitions are not solvable without this key design."},
            ],
        },
        {
            "id": "deep-dive-2",
            "stepNumber": 9,
            "label": "DEEP DIVE",
            "title": "Trace Assembler & Tail-Based Sampling",
            "blocks": [
                {"type": "text", "content": "Spans are routed by trace_id (consistent hashing) to a specific Trace Assembler shard, guaranteeing all spans of one trace land on the same node. The assembler buffers spans in a local RocksDB-backed store and uses a 10s watermark to decide when a trace is 'done'."},
                {"type": "callout", "variant": "warning", "title": "Late-Span / Split-Decision Race", "content": "A service on a partitioned network sends its error span 12s after trace start — past the 10s watermark. The assembler already discarded spans A/B/C based on a 'no error seen' sampling decision. The error trace is lost entirely — the exact failure the NFR says must never happen."},
                {"type": "callout", "variant": "definition", "title": "Fix: Tombstone Grace Period + Dynamic Watermark", "content": "On 'discard' decision, keep a lightweight tombstone for 60s. A late error span triggers a partial re-open. Additionally, set the watermark dynamically per-org based on observed p99 span latency, rather than a global 10s constant — orgs with flaky networks need a longer watermark."},
                {"type": "text", "content": "Under 10x/100x load, the binding constraint shifts to memory — buffering more concurrent in-flight traces per shard. Fix: spill trace_buffer to local SSD (RocksDB) and shard across more assembler nodes. The correctness problem (late spans) exists at any scale."},
            ],
        },
        {
            "id": "summary",
            "stepNumber": 10,
            "label": "SUMMARY",
            "title": "Staff-Level Summary",
            "blocks": [
                {"type": "text", "content": "Key decisions: (1) Wide-column TSDB with (org_id, series_id, time_bucket) partitioning to bound partition size and rotate hot replicas. (2) Tail-based trace sampling via consistent-hash assembler shards with tunable watermark. (3) Alert state machine with CAS-based transitions and watermark-gated window finalization."},
                {"type": "text", "content": "Biggest tradeoffs: Rollup precomputation trades write amplification for read latency. The alert evaluator's fast-path/watermark-correction split trades a small rate of 'corrected' notifications for meeting the 60s SLA."},
                {"type": "text", "content": "Biggest risks: Cardinality quota enforcement is the single most load-bearing mechanism — too strict and customers lose data; too loose and one tenant takes down shared infrastructure. The trace assembler's late-span race is a genuine unsolved-in-full correctness gap."},
                {"type": "callout", "variant": "info", "title": "Path to Principal", "content": "A Principal-level answer would reason about cross-region replication for the TSDB itself, the org-level cost-modeling feedback loop between pricing and cardinality quotas, and a migration strategy for evolving the partition key scheme on a live system serving 30M points/sec."},
            ],
        },
    ],
}


# ─── Questions to Insert ─────────────────────────────────────────

NEW_QUESTIONS = [
    {
        "slug": "distributed-rate-limiter",
        "title": "Design a Distributed Rate Limiter",
        "track": "hld",
        "difficulty": "stretch",
        "timeboxMinutes": 55,
        "prompt": "Design a platform-wide rate limiter-as-a-service: stateless app servers must agree on a shared counter for API keys and IPs, handle hot keys, fail gracefully when the counter store is unreachable, and enforce global (cross-region) limits for premium tenants.",
        "outline": [
            "Scope clarification: platform limiter vs single-API limiter, composable key types",
            "Functional and non-functional requirements with latency/throughput targets",
            "Capacity planning: 4M counter ops/sec, 250M active counter entries",
            "Core domain model: RateLimitRule, LimitCounterState, TenantConfig",
            "API design: atomic check-and-consume with composable keys",
            "Architecture: Decision Service + Redis Cluster + Config Store + Local Fallback",
            "Deep dive: atomic Lua script eliminating the TOCTOU race",
            "Deep dive: hot-key sharding with sub-key splitting",
            "Deep dive: cross-region global limits with asymmetric redistribution",
            "Tradeoffs: fail-open vs fail-closed, token bucket vs sliding window, consistency model",
        ],
        "sources": ["https://github.com/donnemartin/system-design-primer"],
        "status": "published",
        "discoveredBy": None,
        "versions": [
            {
                "role": "staff",
                "levelBar": "Atomic Lua script in Redis for the concurrency-control primitive, key-hash sharding with dynamic sub-key splitting for hot keys, and asymmetric redistribution rule for cross-region global limits that converts unbounded split-brain into bounded staleness.",
                "breakdown": RATE_LIMITER_BREAKDOWN,
            },
        ],
    },
    {
        "slug": "cicd-platform",
        "title": "Design a CI/CD Platform",
        "track": "hld",
        "difficulty": "stretch",
        "timeboxMinutes": 55,
        "prompt": "Design a multi-tenant CI/CD platform (like GitHub Actions): YAML-defined pipeline DAGs, ephemeral runners, per-tenant fair scheduling, live log streaming, and exactly-once-effect execution guarantees for non-idempotent build steps like deploys.",
        "outline": [
            "Scope: multi-tenant SaaS with 50M pipeline runs/day, DAG-based pipelines",
            "Requirements: fair scheduling, at-most-once effect, live logs, artifact passing",
            "Capacity planning: 52K steps/sec, 4.7M concurrent containers, 2.6 GB/s log ingest",
            "Domain model: Pipeline, Run, Step, StepAttempt, Runner, Tenant, Artifact",
            "API design: idempotent run creation, lease-based heartbeat protocol",
            "Architecture: Webhook Ingest → Trigger → Scheduler (WFQ) → Runner Fleet → State Store",
            "Deep dive: Weighted Fair Queuing with CAS-guarded virtual_time",
            "Deep dive: lease-based step execution with idempotent/non-idempotent split",
            "Tradeoffs: exactly-once vs at-least-once+leases, FIFO vs WFQ, central vs cell-based",
        ],
        "sources": [],
        "status": "published",
        "discoveredBy": None,
        "versions": [
            {
                "role": "staff",
                "levelBar": "CAS-guarded weighted fair queuing for tenant scheduling, lease-based at-most-once-effect execution with split retry behavior for idempotent vs non-idempotent steps, and complete decoupling of log ingestion from the DAG state machine.",
                "breakdown": CICD_BREAKDOWN,
            },
        ],
    },
    {
        "slug": "observability-platform",
        "title": "Design an Observability Platform (Datadog / New Relic)",
        "track": "hld",
        "difficulty": "stretch",
        "timeboxMinutes": 55,
        "prompt": "Design a multi-tenant observability platform with metrics ingestion (30M points/sec), distributed tracing with tail-based sampling, and real-time alerting — handling tag cardinality explosion, hot partitions in the TSDB, late-arriving data, and alert dedup/flapping.",
        "outline": [
            "Scope: B2B SaaS with 50K orgs, metrics + tracing + alerting (logs out of scope)",
            "Requirements: sub-second dashboards, 60s alert SLA, cardinality isolation",
            "Capacity planning: 30M points/sec, 6B active series, 150K spans/sec, 1M alert rules",
            "Domain model: MetricSeries, MetricPoint, Trace, Span, AlertRule, AlertEvent",
            "Architecture: Agent → Ingestion Gateway → Kafka → separate writers per subsystem",
            "Deep dive: TSDB schema with (org_id, series_id, time_bucket) partitioning",
            "Deep dive: cardinality explosion failure case and per-metric quota enforcement",
            "Deep dive: trace assembler with watermark-based tail sampling",
            "Deep dive: alert evaluator with CAS-based state machine and watermark-gated evaluation",
            "Tradeoffs: TSDB partitioning, head vs tail sampling, rollup precomputation",
        ],
        "sources": [],
        "status": "published",
        "discoveredBy": None,
        "versions": [
            {
                "role": "staff",
                "levelBar": "Wide-column TSDB with time-bucketed partition keys preventing permanent hot partitions, tail-based trace sampling with watermark and tombstone grace period for late spans, and alert state machine with CAS transitions and provisional-then-corrected notification pattern.",
                "breakdown": OBSERVABILITY_BREAKDOWN,
            },
        ],
    },
]


async def seed_new_questions():
    """Insert new questions into the questions collection."""
    client = AsyncIOMotorClient(MONGODB_URI)
    db_name = MONGODB_URI.rsplit("/", 1)[-1].split("?")[0] or "rolewise"
    db = client[db_name]

    now = datetime.utcnow()
    inserted = 0
    skipped = 0

    for q in NEW_QUESTIONS:
        existing = await db.questions.find_one({"slug": q["slug"]})
        if existing:
            print(f"⊘ '{q['slug']}' already exists, skipping")
            skipped += 1
            continue

        q["createdAt"] = now
        q["updatedAt"] = now
        await db.questions.insert_one(q)
        print(f"✓ Inserted '{q['slug']}' ({q['title']})")
        inserted += 1

    client.close()
    print(f"\n✅ Done! Inserted {inserted}, skipped {skipped}.")


if __name__ == "__main__":
    asyncio.run(seed_new_questions())
