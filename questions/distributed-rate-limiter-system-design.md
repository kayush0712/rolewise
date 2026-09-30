# Distributed Rate Limiter — Staff-Level (L7/E7) System Design Interview

---

## PASS 1 — Compressed Full-System Scaffold

### 1. Interview Context

This is a "small surface area, deep water" problem — the API is trivial (`allow(key) -> bool`), which is exactly why it's a good L7 filter: candidates who stay at the algorithm level (token bucket vs sliding window) top out at L5. The hidden challenges are distributed-systems ones wearing a disguise: how do independent stateless app servers agree on a shared counter without a single point of contention becoming both a bottleneck and a single point of failure; what happens to correctness when the counter store itself is sharded and replicated; and how much precision you're willing to trade for throughput when the limiter must never become slower than the traffic it's supposed to protect. A strong L7 candidate will proactively raise the tension between **strict correctness** (never let a single request slip past the limit) and **availability/latency** (a rate limiter sitting in the hot path cannot itself add meaningful tail latency, and must fail open or closed predictably). Likely probe areas: hot-key behavior for a single viral API key or IP, cross-region/global limit enforcement, the exactly-once-adjacent problem of atomic check-and-increment under concurrency, and graceful degradation when the counter store is unreachable.

### 2. Scope Clarification

**Business**
- Is this a general-purpose platform limiter (like Stripe's or Cloudflare's, protecting arbitrary downstream services) or a limiter for one specific API? *Why it matters:* determines whether limits are static config or a self-service product with its own control plane.
- Do limits need to be configurable per tenant/plan tier at runtime? *Why it matters:* drives whether limit config is baked into deploys or a hot-reloadable data store.

**UX**
- What does the client see on rejection — hard 429, or a queued/delayed response? *Why it matters:* changes whether this is a pure gate or also a scheduler.
- Do we need to return `Retry-After` / remaining-quota headers? *Why it matters:* requires exposing internal counter state via the API, not just a boolean.

**Scale**
- Peak QPS the limiter itself must handle (this is on every request path, so it's the true peak of the platform, not a business metric). *Why it matters:* the limiter must be provably faster than the QPS it gates, or it becomes the outage.
- Number of distinct rate-limit keys (users × APIs × IPs). *Why it matters:* determines whether counter state fits on one node class or must be sharded.

**Reliability**
- Fail-open or fail-closed if the counter store is unreachable? *Why it matters:* a security-facing limiter (anti-abuse) should fail closed; a UX-facing one (protect a backend) usually fails open.
- Is slight over-admission (a few extra requests during a race) acceptable? *Why it matters:* this is the central precision/throughput tradeoff of the whole system.

**Multi-tenancy**
- Are limits per-tenant, per-API-key, per-IP, per-user, or composable (all of the above simultaneously)? *Why it matters:* composable limits mean multiple counter lookups per request, multiplying load.

**Security/Compliance**
- Is this also the anti-abuse/DDoS layer, or strictly a fairness/quota mechanism? *Why it matters:* anti-abuse needs to be adversary-resistant (can't be starved by an attacker spraying keys); fairness limiting does not.

**Operational**
- Who owns limit configuration changes, and do they need to propagate without a redeploy? *Why it matters:* determines whether config is a push-based data store with versioning.

**Stated assumptions:** platform-wide limiter-as-a-service, fronting hundreds of downstream APIs; limits are composable (per-API-key AND per-IP); config is hot-reloadable; fail-open on counter-store outage with a local fallback limiter; slight over-admission during network partitions is acceptable (this is a fairness/protection mechanism, not a hard security boundary); global (cross-region) limits are needed for a subset of "premium" keys, most keys are regional-only.

### 3. Functional Requirements

**Must Have**
- `check_and_consume(key, cost=1) -> {allowed, remaining, reset_at}` — atomic decision. *Rationale: this is the entire product.*
- Multiple concurrent algorithms per key-class (token bucket for smooth APIs, fixed/sliding window for simple quotas). *Rationale: different downstream APIs have different burst tolerance.*
- Dynamic, hot-reloadable limit configuration per key. *Rationale: stated business requirement — no redeploy for limit changes.*

**Nice to Have**
- Global (multi-region) limit enforcement for a subset of keys. *Rationale: needed for premium tier only, adds real complexity, deprioritize in MVP.*
- Usage analytics/dashboards per key. *Rationale: valuable but not on the critical request path.*

**Explicitly Out of Scope**
- Billing/metering (distinct from rate limiting, different consistency requirements — metering must be exact, limiting can tolerate slop). *Rationale: different SLAs, should be a separate system fed by the same event stream.*
- Payload-content-based throttling (e.g., cost-based limiting by request complexity beyond a static `cost` parameter). *Rationale: scope creep into request introspection.*

### 4. Non-Functional Requirements

| NFR | Why it matters | Target |
|---|---|---|
| Decision latency (p99) | Sits in the hot path of every gated request | < 5ms p99, < 1ms p50 |
| Availability of the decision path | Limiter outage = platform outage if fail-closed | 99.99% |
| Throughput | Must exceed peak platform QPS with headroom | 2M decisions/sec sustained, 5M burst |
| Correctness under concurrency | Core value proposition | No more than ~1-2% over-admission during races, 0% under-admission (never wrongly reject) |
| Config propagation latency | Business requirement: hot-reload | < 5s from config write to global enforcement |
| Cross-region consistency (global limits only) | Explicitly scoped for premium tier | Best-effort, bounded staleness < 2s |

### 5. Capacity Planning

- Peak platform QPS (all gated APIs combined): **2,000,000 req/s**.
- Composable limiting (per-API-key + per-IP checked together) → **~2×** counter operations per request → **4,000,000 counter ops/sec**.
- Distinct active keys (API keys + IPs seen in a rolling window): assume 50M API keys, 200M active IPs in any 5-min window → **~250M active counter entries**.
- Per-entry state (token bucket): key (avg 40B) + tokens (8B float) + last_refill_ts (8B) + metadata overhead (~40B in Redis hash) ≈ **~100B/entry**.
- Total hot-state memory: 250M × 100B ≈ **25 GB** raw — comfortably fits in-memory across a modest Redis Cluster (with replication and headroom, budget **~100–150 GB** across the cluster).
- Config store: tens of thousands of limit rules × ~1KB each ≈ **tens of MB** — trivial, but read QPS is enormous since every request may need a config lookup (mitigate with in-process caching, see Architecture).
- Network: 4M ops/sec × ~150B request/response ≈ **~1.2 GB/s** aggregate to the counter tier — this is the real scaling constraint, not CPU or memory.
- **System profile: extremely write-heavy (every request is a read-modify-write), latency-critical, memory-resident, network-throughput-bound. Not storage-heavy, not compute-heavy.**

### 6. Core Domain Model

- **RateLimitRule** — defines algorithm (token bucket / sliding window / fixed window), capacity, refill rate, key pattern (e.g., `apikey:{id}`, `ip:{addr}`), scope (regional/global). One rule can match many keys via pattern.
- **LimitCounterState** — the live, mutable per-key state: current tokens/count, last-updated timestamp, version/CAS token. This is the hot object, lives in the counter store, not a durable "record" in the traditional sense.
- **DecisionAuditEvent** (optional, async) — a sampled or aggregated record of allow/deny decisions, fed to analytics; explicitly *not* on the synchronous path.
- **TenantConfig** — maps a tenant/API to which RateLimitRule(s) apply; supports composition (multiple rules AND'd together).

Relationships: TenantConfig selects RateLimitRule(s) → RateLimitRule is applied against a derived key → produces/mutates one LimitCounterState per (rule, key) pair.

### 7. API Design

**Client-facing (from the gated service, called synchronously in the request path):**
```
POST /v1/check
{
  "keys": ["apikey:abc123", "ip:203.0.113.5"],   // composable — checked atomically together
  "cost": 1
}
→ 200 OK
{
  "allowed": true,
  "results": [
    {"key": "apikey:abc123", "remaining": 998, "limit": 1000, "reset_at": "2026-08-19T10:00:00Z"},
    {"key": "ip:203.0.113.5", "remaining": 45,  "limit": 100,  "reset_at": "2026-08-19T09:31:00Z"}
  ]
}
```
Idempotency note: this endpoint is **intentionally not idempotent** — each call consumes quota by design. The idempotency concern instead lives in the client's retry behavior: if the gated service times out waiting for `/v1/check` and retries, it must NOT double-consume. Mitigate by having the client pass a `decision_id` (request UUID); the limiter caches the decision for that `decision_id` for a short TTL (e.g., 2s) and returns the cached result on retry rather than re-consuming. This is a small but real idempotency mechanism worth naming explicitly, not hand-waved.

**Config (admin path, low QPS, strongly consistent):**
```
PUT /v1/rules/{rule_id}
{ "algorithm": "token_bucket", "capacity": 1000, "refill_per_sec": 16.7, "key_pattern": "apikey:{id}", "scope": "regional" }
```

### 8. High-Level Architecture

Components: **(a) Client SDK / sidecar** embedded in each gated service, does the `/v1/check` call and enforces a local circuit breaker; **(b) Limiter Decision Service** — stateless fleet, holds no counter state itself, executes the algorithm logic and talks to the counter store; **(c) Distributed Counter Store (sharded, in-memory)** — e.g., Redis Cluster, holds the actual LimitCounterState, executes atomic Lua scripts for check-and-consume; **(d) Config Store + Propagation** — a strongly-consistent small store (etcd/Consul or a versioned Postgres table) with a pub/sub or long-poll propagation mechanism to push rule changes to Decision Service instances' local caches; **(e) Local L1 Cache in Decision Service** — an approximate, short-TTL local token bucket used only as a fail-open fallback when the Counter Store is unreachable; **(f) Async Audit/Analytics Pipeline** — Kafka-fed, off the critical path, for usage dashboards.

Request flow: the gated service's SDK calls the Decision Service (co-located in-region for latency) with the composed keys; the Decision Service resolves the applicable RateLimitRule(s) from its local config cache, computes the derived counter keys, and issues a single atomic Lua script call to the appropriate Redis Cluster shard(s) that performs read-check-consume-write in one round trip; the result is returned to the client. If the Counter Store call times out or errors, the Decision Service falls back to its local approximate limiter and fails open, emitting a metric so operators see degraded-mode traffic.

### 9. Tradeoff Table

| Decision | Option A | Option B | Chosen | Why |
|---|---|---|---|---|
| Algorithm | Fixed window counter | Sliding window log / token bucket | Token bucket (sliding-window approx for burst-sensitive APIs) | Fixed window allows 2x burst at window boundaries; token bucket smooths without storing per-request logs |
| Counter store | Single strongly-consistent DB (e.g. CP store) | In-memory sharded cache (Redis Cluster) with atomic scripts | Redis Cluster | Latency budget (<5ms p99) rules out a durable DB round trip; rate-limit state is inherently ephemeral/recomputable |
| Consistency model for global limits | Strict cross-region consensus per decision | Async local counting + periodic aggregation | Async aggregation with bounded staleness | Strict consensus adds cross-region RTT to every request, violating the latency NFR; a rate limiter tolerating brief over-admission is an acceptable tradeoff, unlike e.g. a payments ledger |
| Failure mode on counter-store outage | Fail closed (reject all) | Fail open with local approximate fallback | Fail open (per stated assumption) | This is a protection mechanism, not a security boundary; failing closed turns a cache outage into a full platform outage |
| Config propagation | Every decision reads config store directly | Config cached locally, pushed via pub/sub on change | Local cache + push | Config reads at 4M ops/sec would overwhelm any config store; requirement is 5s propagation, not synchronous consistency |
| Composable key checks | Sequential independent calls per key | Single batched atomic multi-key script | Batched atomic | Sequential checks create a race (key A passes, key B fails, but A was already consumed) and double the round trips |

### 10. Operational & Business Appendix

**Security:** the Decision Service and Counter Store sit entirely inside the trust boundary — no external client talks to them directly, only gated services via their SDK, which limits the blast radius of a compromised client to its own quota. Config write access (rule changes) is admin-gated and audited, since a malicious or buggy rule push (e.g., setting a limit to zero for a key pattern matching `*`) is a self-inflicted outage vector — worth a canary/staged-rollout mechanism for config changes.

**Observability:** the two metrics that actually matter operationally are (1) decision latency p50/p99/p999 per region, since this is the metric that turns into cascading downstream failures if it regresses, and (2) fallback/degraded-mode traffic percentage, since a silent creeping increase in fail-open traffic means the counter store is unhealthy before anyone notices via error rates alone. Per-key deny-rate dashboards matter for the product side but are secondary to these two.

**Product/business framing:** the real product surface is the config/admin experience (self-service limit tuning per tenant), not the limiter internals — tenants will churn on either "my legitimate traffic got throttled" or "I got hit by an abusive neighbor sharing my shard," both of which are UX/support problems downstream of the technical design choices above.

**Evolution roadmap:** v1 ships regional-only limiting with the async-fallback pattern; v2 adds the global cross-region aggregation for premium tier; v3 could add cost-based/adaptive limiting (dynamically tightening limits under detected abuse patterns), which is a genuinely different problem (anomaly detection feeding rule updates) rather than an extension of the core mechanism.

---

## PASS 2 — Mandatory Deep Dives

### Step 1: Component Selection

The three components carrying real signal for this problem:

1. **The atomic check-and-consume mechanism inside the Counter Store** — this is where the actual concurrency-control difficulty lives: many Decision Service instances hitting the same key simultaneously, and the correctness of the whole system hinges on this being a true atomic read-modify-write, not a check-then-write with a race window.
2. **The sharding/partition-key strategy for the Counter Store** — a rate limiter's access pattern is uniquely adversarial to naive sharding: a single viral key (a popular API key, or an attacker's IP) can create a hot partition that no amount of horizontal scaling fixes, because you cannot split one key across shards without breaking atomicity.
3. **The cross-region synchronization mechanism for global limits** — this is the genuinely hard distributed-systems problem in the whole design: enforcing one logical limit across independently-operating regional counter clusters without paying cross-region latency on every request.

Everything else (config propagation via pub/sub, the SDK/circuit-breaker pattern, the audit pipeline) is a standard, well-understood pattern — not where an L7 bar is set.

---

### Deep Dive 1: Atomic Check-and-Consume in the Counter Store

**Schema (Redis, not a relational DDL — but the equivalent structural contract):**

```
-- Logical structure per key, stored as a Redis HASH:
HSET ratelimit:{key_hash} 
  tokens        <float>      -- current available tokens
  last_refill   <int64>      -- unix millis of last refill computation
  capacity      <float>      -- cached from config, avoids a second lookup
  refill_rate   <float>      -- tokens per second, cached from config
  version       <int64>      -- monotonic version, incremented every write (used for observability/debugging, not CAS — the Lua script itself is the concurrency mechanism)

-- TTL set to (capacity / refill_rate) * 2, so fully-idle keys self-expire and don't
-- accumulate unbounded memory for one-off IPs/keys.
```

**Primary access pattern — the atomic decision, as a Lua script (executed server-side in Redis, single-threaded, hence atomic without external locking):**

```lua
-- KEYS[1] = ratelimit:{key_hash}
-- ARGV[1] = now_millis, ARGV[2] = cost, ARGV[3] = capacity, ARGV[4] = refill_rate

local key = KEYS[1]
local now = tonumber(ARGV[1])
local cost = tonumber(ARGV[2])
local capacity = tonumber(ARGV[3])
local refill_rate = tonumber(ARGV[4])

local data = redis.call('HMGET', key, 'tokens', 'last_refill')
local tokens = tonumber(data[1]) or capacity
local last_refill = tonumber(data[2]) or now

-- refill based on elapsed time since last touch
local elapsed = math.max(0, now - last_refill) / 1000.0
tokens = math.min(capacity, tokens + elapsed * refill_rate)

local allowed = 0
if tokens >= cost then
  tokens = tokens - cost
  allowed = 1
end

redis.call('HMSET', key, 'tokens', tokens, 'last_refill', now)
redis.call('PEXPIRE', key, math.ceil((capacity / refill_rate) * 2000))

return {allowed, tokens}
```

This is the single most important design fact in the whole system: **Redis executes Lua scripts single-threadedly and atomically per shard**, so this script is a true atomic read-modify-write with zero external locking, zero CAS retry loop, and one round trip. This is *why* Redis (or an equivalent single-threaded/atomic-script-capable store) was chosen over a generic KV store with separate GET/SET — a naive `GET tokens; if tokens >= cost: SET tokens - cost` from the *application* side has a classic TOCTOU race: two Decision Service instances both read `tokens=1`, both decide to allow, both write `tokens=0` — one request that should have been denied was admitted. Pushing the entire decision into the script eliminates the round trip between check and write entirely.

**Under 10x load (40M ops/sec):** a single Redis shard tops out around 100–150K ops/sec for simple commands, less for Lua scripts (~50-80K/sec realistically with this script's complexity) — so 10x load simply requires proportionally more shards; the script itself doesn't change, because each key's script execution is independent and shard-local. The real question at 10x is whether the *key distribution* stays even (see Deep Dive 2).

**Under 100x load (400M ops/sec) on a single hot key:** this is where the script stops being sufficient. A single viral API key cannot be split across shards without breaking atomicity, so a truly hot single key eventually saturates the one shard it lives on regardless of cluster size. The fix at this scale is **not** a smarter script — it's a structural change (see the failure case below).

**Concrete failure case, worked step by step — the hot-key/hot-partition scenario:**

1. An attacker (or a legitimately viral integration) starts hammering `apikey:abc123` at 200K req/s.
2. Every one of those requests hashes to the same Redis Cluster slot → same physical shard, because Redis Cluster's hash-slot assignment is per-key, and this is one key.
3. That shard's single-threaded event loop is now spending 100% of its time executing this key's Lua script; other keys that happen to hash to the same shard (unrelated tenants!) start queuing behind it — their `/v1/check` latency spikes even though *they* aren't the abusive traffic.
4. Decision Service instances calling this shard start timing out (per the stated fail-open behavior), so they fall back to the local approximate limiter — which has no knowledge of the true global count, so it under-enforces, and the abusive key gets *more* traffic through, not less, exactly when it should be clamped harder.
5. This is a cascading failure: one hot key degrades unrelated tenants sharing its shard, and the fail-open safety mechanism actively works against containment for the offending key.

**The fix — sharded/probabilistic local counting for known-hot keys:**
Split a single logical key's capacity across N sub-keys (e.g., `apikey:abc123:0` .. `apikey:abc123:7`), each on a different shard (achieved by suffixing before hashing, or using Redis Cluster hash tags deliberately *avoided* here — the whole point is to *not* force them onto one shard), each holding `capacity/N` tokens. The Decision Service picks a sub-key via `hash(request_id) % N` (or round-robin) for each check. This trades perfect precision (the *true* aggregate count is now approximate, since a burst could unevenly hit one sub-shard) for eliminating the single-shard bottleneck — an explicit, named instance of the throughput/precision tradeoff called out in Section 9. This sharding is applied selectively: static config for known high-volume tenants, plus a runtime "hot key detector" (sampling shard command rates) that can dynamically promote a key into sharded mode without a deploy.

---

### Deep Dive 2: Sharding/Partition-Key Strategy for the Counter Store

**Partition key reasoning, argued:** the natural, obvious choice is to hash the *rate-limit key itself* (`apikey:abc123`, `ip:203.0.113.5`) to determine the shard — this is in fact what's used above, and it's correct for the common case because it guarantees every check for a given key lands on the same shard, which is *required* for the atomic script to see consistent state. The wrong-but-tempting alternative is to partition by something time-based, e.g., putting the current time-window into the partition key (`ratelimit:{window}:{key}`) to make window rollover trivial. Walking through what breaks: if you partition by time window instead of by logical key, then all traffic *in the same window* lands on the same shard *regardless of which key it's for* — you've turned a key-uniform hash distribution into a **globally synchronized hot shard that rotates every window**, because every single request across every tenant in the system is hashing to "whatever shard owns the current window" at the same moment. This is strictly worse than the single-hot-key problem in Deep Dive 1 — instead of one abusive key overloading one shard, *all* traffic overloads one shard, cluster-wide, on a clock. Time should be a *value* in the record (the `last_refill` field), never a component of the partition key, precisely because partition keys should distribute independent units of contention, and time is shared by definition across every entity in the system.

**What changes under 10x/100x load:** at 10x, add shards and let Redis Cluster's consistent-hashing slot migration redistribute — no logical change. At 100x, the aggregate key cardinality (250M → potentially 25B if this reflects real user growth, not just traffic) starts to matter for memory, not just ops/sec: at that cardinality, the TTL-based self-eviction (Deep Dive 1's schema) becomes load-bearing rather than a nice-to-have, since without it idle long-tail keys would exhaust cluster memory before hot keys ever became the bottleneck.

**Bookkeeping mechanism:** the `PEXPIRE` set on every write *is* the consistency mechanism here — there's no separate cleanup job, no cold-key sweep; expiry is self-managing and colocated with the write that would otherwise leave the key stale. This avoids a whole class of "background reaper" distributed-systems complexity that a naive design would introduce.

---

### Deep Dive 3: Cross-Region Synchronization for Global Limits

**The problem, precisely:** a premium tenant's API key has one logical limit (e.g., 10,000 req/min) that must hold *in aggregate* across US, EU, and APAC regional clusters, each running its own regional Counter Store for latency reasons (Section 9's chosen tradeoff rules out synchronous cross-region consensus per request).

**Mechanism — regional local counting + async gossip aggregation with a bounded staleness watermark:**

```
-- Each region maintains its own LOCAL counter (same Lua script as Deep Dive 1),
-- PLUS a locally-tracked "last known global share" that's periodically refreshed:

HSET globalratelimit:{key_hash}:region:us-east
  local_tokens        <float>
  last_refill         <int64>
  global_capacity_share <float>   -- this region's current allotment of the global capacity
  watermark            <int64>    -- timestamp of the last successful cross-region sync

-- A background sync process (every ~500ms-1s) runs per key-with-global-scope:
--   1. each region publishes its local consumption delta since last sync to a
--      lightweight pub/sub topic (or a central low-QPS aggregator, since this is
--      only for the "premium tier" subset — explicitly NOT all 250M keys)
--   2. the aggregator (or each region, if using pure gossip) computes total
--      consumption across regions and redistributes global_capacity_share
--      proportionally to each region's recent demand (a region seeing more
--      traffic gets a larger share on the next epoch)
--   3. watermark is updated on successful sync; if a region's watermark goes
--      stale beyond a threshold (e.g., 5s), that region unilaterally clamps
--      its local share down to a conservative floor (fail toward under-admission
--      for the GLOBAL limit specifically, since this is the one case where
--      over-admission has real billing/abuse consequences for premium tenants)
```

**Concrete failure/edge case — the split-brain during a sync partition:**

1. US and EU regions are each locally admitting requests against their last-known `global_capacity_share` (say 6,000 and 4,000 req/min respectively, summing to the 10,000 global limit).
2. A network partition breaks the aggregator's connectivity to the EU region.
3. EU keeps admitting up to its last-known 4,000 share — correctly, per the fail-open-ish design — but US, seeing genuinely rising demand and no updated signal from EU, might naively try to reclaim "unused" capacity it *assumes* EU isn't using.
4. If US's redistribution logic isn't watermark-aware, it could bump its own share to 8,000 based on stale assumptions, and now US(8,000) + EU(4,000) = 12,000, exceeding the global 10,000 by 20% — a real over-admission, not just a race-window blip.
5. **The watermark is exactly what prevents step 4**: a region is only allowed to *increase* its own claimed share if its own watermark is fresh (proving it's still in the sync group); a region that hasn't heard from the aggregator recently can only ever hold steady or clamp down, never expand — this converts a potentially unbounded split-brain over-admission into a bounded one (worst case: sum of all regions' last-synced shares, which is exactly the global limit, held constant until sync resumes).

**What changes to fix it, concretely:** the corrected redistribution rule is asymmetric by design — *decrease your local share unilaterally on any signal of staleness; only increase your local share on a freshly-confirmed sync* — this single asymmetry is the actual mechanism (not "add more consensus," which would violate the latency NFR this whole design exists to protect).

---

### Step 3: Worked Follow-Up Questions

**1. "Walk me through what happens if the aggregator itself (in the global-limit sync) goes down."**
Every region's watermark ages past the staleness threshold simultaneously, so every region clamps to its last-known share and holds — the global limit becomes effectively "frozen" at whatever the last good distribution was, which under-serves regions with growing demand but never over-admits. This is a deliberate consequence of the asymmetric rule above: an aggregator outage degrades to *conservative*, not *unsafe*. Recovery: when the aggregator returns, it should not simply resume normal-cadence sync — it should run one "catch-up" epoch that explicitly reconciles based on actual consumption during the outage (pulled from each region's local counters) before returning to steady-state redistribution, to avoid an immediate over-correction spike.

**2. "How would you detect a hot key before it becomes an incident, rather than reactively?"**
Sample command execution counts per key at the Redis Cluster proxy/client layer (most clients expose per-key command stats, or use `MONITOR`-derived sampling in a shadow process, never in the hot path itself) with a sliding 10s window; a key crossing a percentile-based threshold relative to its shard's peers (not an absolute threshold, since different tenants have legitimately different baseline volumes) gets flagged and auto-promoted into the sharded-sub-key mode from Deep Dive 1, with the promotion itself being a config push through the existing pub/sub propagation path — so detection and mitigation reuse infrastructure that already exists rather than requiring new plumbing.

**3. "Why token bucket over sliding-window-log, given sliding-window-log is more precise?"**
Sliding-window-log requires storing a timestamp per request (or a sorted set of them) to know exactly which requests fall in the trailing window — at 4M ops/sec this means unbounded-ish per-key memory growth proportional to request rate within the window, not O(1) like token bucket's two scalars. The precision gain (exact windowing vs. token bucket's smoothed approximation) doesn't justify an order-of-magnitude memory cost increase at this scale; sliding-window-log would be the right choice for a low-QPS, high-precision-requirement limiter (e.g., a compliance-driven quota with legal implications), which this isn't.

**4. "What's your rollback story if a bad config push sets a critical tenant's limit too low?"**
Config changes propagate via the pub/sub push from Section 8, so the fix is symmetric and equally fast — push a corrected rule, same <5s propagation target applies to the fix as to the original mistake. The mitigating control is upstream of the technical propagation speed: a staged/canary rollout for config changes (push to 1% of Decision Service instances' regions first, watch the deny-rate metric from Section 10's observability appendix, then complete rollout) catches this before full blast radius, which matters more than fast rollback given that even a few seconds of a critical tenant being wrongly throttled at 429 has real business cost.

**5. "How do you prevent the idempotency `decision_id` cache from itself becoming a hot-key/memory problem?"**
It's a separate, short-TTL (2s) keyspace from the main counter state, so its cardinality is bounded by (requests per 2s window) rather than by total key count — at 4M ops/sec that's roughly 8M entries at steady state, each tiny (just the cached decision result), which is a small, self-bounding structure that doesn't share fate with the main counter hot-key risk; it can live in the same Redis Cluster but should be monitored as a distinct metric so its growth doesn't get conflated with genuine counter-state growth.

**6. "At 100x scale, does the single-region Decision Service fleet itself become a bottleneck, independent of the Counter Store?"**
The Decision Service is stateless, so it scales horizontally trivially — but the real constraint at 100x is connection count to the Counter Store cluster: naive one-connection-per-request patterns would exhaust Redis's connection limits long before CPU becomes the issue, so this requires connection pooling with pipelining at the Decision Service layer, and likely moving from a simple client-side hashing scheme to a smarter proxy layer (e.g., a local Redis Cluster proxy sidecar) to avoid each Decision Service instance holding O(shards) connections × O(instances) — which is the kind of quadratic-connection-count trap that's invisible at 1x and becomes the actual limiting factor at 100x, not the script logic itself.

**7. "Why not just use the SDK's local approximate limiter as the primary mechanism and skip the Counter Store entirely for cost savings?"**
Local-only limiting means each Decision Service instance enforces the limit against *its own* traffic slice only, with zero visibility into what other instances are doing — the effective global limit becomes (configured limit × number of Decision Service instances), which is unbounded as the fleet autoscales, defeating the entire purpose. Local limiting is correctly used here only as a degraded fallback under a stated, monitored, and alerted-on failure condition (Counter Store unreachable), never as the steady-state design.

**8. "How would per-tenant limit changes interact with in-flight requests that already read the old config?"**
Because the Lua script reads `capacity`/`refill_rate` from cached fields on the counter record itself (not fetched fresh from config on every call — that would be a second round trip, violating the latency NFR), a config change doesn't take effect until the next write to that key updates the cached values; this is an accepted, bounded staleness window (worst case: one full refill cycle for that key), consistent with the already-stated 5s propagation target, and should be called out explicitly rather than assumed away, since a candidate claiming "changes apply immediately" without acknowledging this cache layer is glossing over a real consistency gap.

**Remaining follow-ups (short prompts, no full worked answer required in an interview):**
- How would you rate-limit websocket/streaming connections rather than discrete requests?
- What changes if `cost` can be fractional or request-size-dependent?
- How do you test this system for correctness under simulated network partitions?
- What's the blast radius if the Redis Cluster's own gossip protocol has a bug?
- How would you support a "burst allowance" on top of steady-state limits?
- Should the audit/analytics pipeline ever feed back into rate-limit decisions in real time (adaptive limiting)?
- How do you avoid thundering-herd retries from clients when many keys reset at the same window boundary?
- What's your migration strategy for changing a key's algorithm (e.g., fixed-window to token-bucket) without a discontinuity?

---

## Final Section — Staff-Level Summary

**Key architectural decisions:**
- Single-round-trip atomic Lua script as the concurrency-control primitive, eliminating the check-then-write race entirely rather than managing it with locks/CAS retries.
- Key-hash-based sharding (never time-based), with dynamic sub-key sharding as an escape valve for hot keys — precision traded for throughput, explicitly and selectively.
- Asymmetric (decrease-freely, increase-only-when-fresh) redistribution rule for cross-region global limits — the one mechanism that converts an unbounded split-brain risk into a bounded one without paying consensus latency.

**Biggest tradeoffs:**
- Fail-open with local approximate fallback trades strict correctness for availability — correct for a protection mechanism, would be wrong for a security boundary or a billing system.
- Global limits are eventually-consistent by design; a candidate proposing strict cross-region consensus here would be over-engineering against the stated NFRs.

**Biggest risks:**
- Hot-key detection is reactive-by-sampling unless explicitly built as a proactive control-plane feature — a candidate who doesn't raise this leaves a real production gap.
- The idempotency `decision_id` mechanism is easy to hand-wave; without it, client retry storms during Counter Store hiccups silently double-consume quota.

**Scorecard**

| Dimension | Score |
|---|---|
| Problem Framing | 9/10 |
| Requirements | 8/10 |
| NFRs | 8/10 |
| Capacity Planning | 9/10 |
| Data Modeling | 8/10 |
| Architecture | 9/10 |
| Tradeoffs | 9/10 |
| Failure Analysis | 9/10 |
| Product Thinking | 7/10 |
| **Overall** | **8.5/10** |

**Path to Senior Staff / Principal:** the gap from this answer to Principal is less about any single mechanism and more about organizational leverage — a Principal-level answer would spend more time on how this system becomes a *platform primitive* other teams build on (a self-service SDK/config experience that prevents every team from reinventing rate limiting badly), how the hot-key detector's signal could be shared with a broader anomaly-detection/abuse-prevention system rather than being single-purpose, and a sharper articulation of which specific business risk (a large customer's outage vs. a security incident vs. infra cost) each tradeoff decision is actually protecting against — Staff-level nails the mechanism; Principal-level ties the mechanism explicitly back to which stakeholder's pain it prevents and how it composes with adjacent systems already in the org.
