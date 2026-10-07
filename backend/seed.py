"""Seed MongoDB with all existing content from the TypeScript data files.

Run: python backend/seed.py
Idempotent — checks if data exists before inserting.
"""

import asyncio
import os
import sys
from datetime import datetime

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

# Load .env from backend directory
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
load_dotenv(os.path.join(os.path.dirname(__file__), ".env.example"))

MONGODB_URI = os.getenv("MONGODB_URI")


# ─── Roles Data ───────────────────────────────────────

ROLES = [
    {
        "_id": "sde-1",
        "title": "SDE 1",
        "shortTitle": "SDE 1",
        "band": "L3 / Junior",
        "summary": "Prove you can ship a correct solution, explain tradeoffs in plain language, and keep scope tight.",
        "interviewMix": [
            {"track": "coding", "weight": 50},
            {"track": "lld", "weight": 25},
            {"track": "hld", "weight": 10},
            {"track": "behavioral", "weight": 15},
        ],
        "bar": [
            "Working, tested code with clear edge cases",
            "Simple class or API design without over-engineering",
            "Honest communication when you are stuck",
        ],
    },
    {
        "_id": "sde-2",
        "title": "SDE 2",
        "shortTitle": "SDE 2",
        "band": "L4 / Mid",
        "summary": "Show independent ownership: you pick a reasonable design, defend it, and know when to go deeper.",
        "interviewMix": [
            {"track": "coding", "weight": 35},
            {"track": "lld", "weight": 25},
            {"track": "hld", "weight": 25},
            {"track": "behavioral", "weight": 15},
        ],
        "bar": [
            "Correctness plus time/space complexity",
            "Clean module boundaries and APIs",
            "A complete high-level sketch with 1–2 deep dives",
        ],
    },
    {
        "_id": "senior",
        "title": "Senior Engineer",
        "shortTitle": "Senior",
        "band": "L5",
        "summary": "Lead the interview. Interviewers expect structure, capacity thinking, and tradeoffs that match real production.",
        "interviewMix": [
            {"track": "coding", "weight": 20},
            {"track": "lld", "weight": 20},
            {"track": "hld", "weight": 40},
            {"track": "behavioral", "weight": 20},
        ],
        "bar": [
            "Delivery framework under a 45-minute clock",
            "NFRs, bottlenecks, and failure modes named early",
            "Stories that show technical leadership, not just tickets",
        ],
    },
    {
        "_id": "staff",
        "title": "Staff Engineer",
        "shortTitle": "Staff",
        "band": "L6",
        "summary": "Operate across teams. Designs should include org constraints, evolution, and how you would actually land the work.",
        "interviewMix": [
            {"track": "coding", "weight": 10},
            {"track": "lld", "weight": 15},
            {"track": "hld", "weight": 45},
            {"track": "behavioral", "weight": 30},
        ],
        "bar": [
            "Multi-service designs with explicit consistency models",
            "Migration, rollout, and observability as first-class",
            "Influence: aligning stakeholders and reducing blast radius",
        ],
    },
    {
        "_id": "principal",
        "title": "Principal Engineer",
        "shortTitle": "Principal",
        "band": "L7+",
        "summary": "Set the technical direction. Expect ambiguous prompts, company-scale constraints, and strategy as much as boxes.",
        "interviewMix": [
            {"track": "coding", "weight": 5},
            {"track": "lld", "weight": 10},
            {"track": "hld", "weight": 50},
            {"track": "behavioral", "weight": 35},
        ],
        "bar": [
            "Problem framing before solutioning",
            "Platform vs product tradeoffs and 3-year evolution",
            "Risk, cost, and org design called out without being asked",
        ],
    },
]

# ─── Tracks Data ──────────────────────────────────────

TRACKS = [
    {
        "_id": "coding",
        "title": "Coding",
        "shortTitle": "Code",
        "summary": "Data structures and algorithms at the depth your level is actually scored on — not every LeetCode tag.",
    },
    {
        "_id": "lld",
        "title": "Low-level design",
        "shortTitle": "LLD",
        "summary": "Classes, APIs, and object model. Translate a product prompt into code a teammate would want to maintain.",
    },
    {
        "_id": "hld",
        "title": "High-level design",
        "shortTitle": "HLD",
        "summary": "Distributed systems: requirements, APIs, data flow, capacity, and the deep dives that decide your level.",
    },
    {
        "_id": "behavioral",
        "title": "Behavioral",
        "shortTitle": "People",
        "summary": "Ownership, conflict, and impact stories calibrated to junior vs staff expectations.",
    },
]

# ─── Questions Data (with role-versioned structure) ───

# The Dropbox breakdown content
DROPBOX_BREAKDOWN = {
    "focusAreas": ["Scalability", "Distributed Systems", "Consistency", "Reliability"],
    "targetRole": "Senior Software Engineer",
    "totalSections": 25,
    "completedSections": 18,
    "sections": [
        {
            "id": "understand",
            "stepNumber": 1,
            "label": "UNDERSTAND",
            "title": "Understand the Problem",
            "blocks": [
                {"type": "text", "content": "Dropbox is a cloud-based file storage and synchronization service. Users can store files on Dropbox's servers and access them from any device. Files are automatically synchronized across all connected devices in real time."},
                {"type": "requirements", "core": ["Upload files from any device", "Download files from any device", "Share files with other users", "Automatically synchronize files across devices"], "outOfScope": ["File editing", "Browser-based file viewing"]},
            ],
        },
        {
            "id": "requirements",
            "stepNumber": 2,
            "label": "REQUIREMENTS",
            "title": "Requirements",
            "blocks": [
                {"type": "functional-nonfunctional", "functional": ["Upload files", "Download files", "Share files", "Synchronize files"], "nonFunctional": ["High availability", "Durability", "Scalability", "Low latency", "Strong reliability"]},
                {"type": "callout", "variant": "warning", "title": "Interviewer's Lens", "content": "At the Senior level, be prepared to explain why file storage and metadata storage should be treated differently."},
            ],
        },
        {
            "id": "entities",
            "stepNumber": 3,
            "label": "ENTITIES",
            "title": "Core Entities",
            "blocks": [
                {"type": "entity-table", "entities": [
                    {"name": "User", "purpose": "Authenticated account that owns files and devices"},
                    {"name": "File", "purpose": "Binary content stored in blob storage with metadata"},
                    {"name": "Folder", "purpose": "Hierarchical grouping of files and sub-folders"},
                    {"name": "FileVersion", "purpose": "Snapshot of a file at a given point in time"},
                    {"name": "Device", "purpose": "A registered client device belonging to a user"},
                ]},
            ],
        },
        {
            "id": "api-design",
            "stepNumber": 4,
            "label": "API DESIGN",
            "title": "API Design",
            "blocks": [
                {"type": "api-table", "endpoints": [
                    {"method": "POST", "endpoint": "/files", "description": "Upload a new file or initiate chunked upload"},
                    {"method": "GET", "endpoint": "/files/:id", "description": "Download file by ID"},
                    {"method": "DELETE", "endpoint": "/files/:id", "description": "Permanently delete a file"},
                    {"method": "POST", "endpoint": "/files/:id/share", "description": "Share file with another user"},
                    {"method": "GET", "endpoint": "/files/:id/versions", "description": "List all versions of a file"},
                ]},
            ],
        },
        {
            "id": "high-level",
            "stepNumber": 5,
            "label": "SOLUTION EVOLUTION",
            "title": "How the Design Evolves",
            "blocks": [
                {"type": "evolution", "options": [
                    {"number": "01", "label": "Naive", "description": "Client → Backend → Local Storage", "pros": ["Simple to implement"], "cons": ["Doesn't scale. Single point of failure."], "recommended": False},
                    {"number": "02", "label": "Better", "description": "Client → Backend → Blob Storage", "pros": ["Scales file storage independently"], "cons": ["Files still pass through app server."], "recommended": False},
                    {"number": "03", "label": "Production", "description": "Client → API → Metadata DB\nClient → Blob Storage (direct)", "pros": ["Minimal server load. Metadata separated. Scalable."], "cons": ["More complex to coordinate."], "recommended": True},
                ]},
            ],
        },
        {
            "id": "hld",
            "stepNumber": 6,
            "label": "HIGH-LEVEL DESIGN",
            "title": "High-Level Design",
            "blocks": [
                {"type": "architecture-flow", "nodes": [
                    {"label": "Client", "type": "supporting"},
                    {"label": "API Gateway", "type": "critical"},
                    {"label": "Metadata Service", "type": "critical"},
                    {"label": "Blob Storage", "type": "critical"},
                    {"label": "Sync Service", "type": "critical"},
                    {"label": "Metadata DB", "type": "supporting"},
                ], "connections": [
                    {"from": "Client", "to": "API Gateway", "style": "unidirectional"},
                    {"from": "API Gateway", "to": "Metadata Service", "style": "unidirectional"},
                    {"from": "Blob Storage", "to": "Metadata Service", "style": "bidirectional"},
                    {"from": "Metadata Service", "to": "Sync Service", "style": "unidirectional"},
                    {"from": "Sync Service", "to": "Metadata DB", "style": "unidirectional"},
                ], "explanation": "Metadata (file name, path, permissions, version) and file contents have vastly different storage and scaling characteristics. Metadata is small and relational — it belongs in a structured database. File contents are large binary blobs — they belong in object storage."},
            ],
        },
        {
            "id": "deep-dive",
            "stepNumber": 7,
            "label": "DEEP DIVE",
            "title": "Handling Large Files",
            "blocks": [
                {"type": "upload-comparison", "options": [
                    {"label": "Traditional Upload", "description": "Client → App Server → Storage", "details": "File is uploaded to the application server, which then writes to storage. Doubles bandwidth usage and creates a server bottleneck."},
                    {"label": "Direct Upload", "description": "Client → Presigned URL → Blob Storage", "details": "Client requests a presigned URL from the API, then uploads directly to blob storage. Server is never in the data path.", "recommended": True},
                ]},
                {"type": "callout", "variant": "definition", "title": "Presigned URLs", "content": "Presigned URLs are time-limited tokens issued by your API that grant a client temporary permission to upload directly to or download from blob storage (e.g. S3, GCS) without exposing permanent credentials."},
            ],
        },
        {
            "id": "tradeoffs",
            "stepNumber": 8,
            "label": "TRADE-OFFS",
            "title": "Key Trade-offs",
            "blocks": [
                {"type": "comparison", "title": "Consistency vs Availability", "optionA": {"label": "OPTION A", "description": "Strong consistency — all devices see the same state immediately"}, "optionB": {"label": "OPTION B", "description": "Eventual consistency — changes propagate asynchronously"}, "recommendation": "Eventual consistency", "rationale": "Dropbox-class products tolerate brief sync delays. Strong consistency across regions is prohibitively expensive."},
                {"type": "comparison", "title": "Synchronous vs Asynchronous Processing", "optionA": {"label": "OPTION A", "description": "Upload completes only after file is fully processed"}, "optionB": {"label": "OPTION B", "description": "Upload returns immediately; processing happens in background"}, "recommendation": "Async processing", "rationale": "Decouples upload latency from indexing, thumbnail generation, and virus scanning. Better user experience."},
                {"type": "comparison", "title": "Single-region vs Multi-region", "optionA": {"label": "OPTION A", "description": "All data and compute in one region"}, "optionB": {"label": "OPTION B", "description": "Data replicated across multiple geographic regions"}, "recommendation": "Start single-region", "rationale": "Multi-region adds significant complexity. Introduce it only when latency or compliance requirements justify the cost."},
                {"type": "comparison", "title": "SQL vs NoSQL", "optionA": {"label": "OPTION A", "description": "Relational DB for all metadata — ACID guarantees, complex queries"}, "optionB": {"label": "OPTION B", "description": "Document/wide-column store for metadata — horizontal scale"}, "recommendation": "SQL for metadata", "rationale": "File metadata is relational and benefits from ACID. Use object storage for blobs, not a NoSQL store."},
            ],
        },
    ],
}


URL_SHORTENER_BREAKDOWN = {
    "focusAreas": ["Database Schema", "Encoding Algorithms", "Caching Strategy", "Abuse Prevention"],
    "targetRole": "SDE-2 / Mid-Level",
    "totalSections": 10,
    "completedSections": 10,
    "sections": [
        {
            "id": "understand",
            "stepNumber": 1,
            "label": "CONTEXT",
            "title": "Interview Context",
            "blocks": [
                {"type": "text", "content": "URL Shortener (like bit.ly) is the classic 'Hello World' of system design. Because it's well-known, interviewers use it to probe deep into practical execution — not just drawing boxes. They want to see you write out the database schema, handle concurrency, and navigate cache invalidation."},
                {"type": "callout", "variant": "warning", "title": "The Trap", "content": "Don't just say 'I will use a NoSQL database and put a cache in front of it.' You must explain exactly what happens when two users try to shorten the same URL, how collision is avoided, and how the connection pool behaves under load."},
            ],
        },
        {
            "id": "requirements",
            "stepNumber": 2,
            "label": "REQUIREMENTS",
            "title": "Requirements",
            "blocks": [
                {"type": "functional-nonfunctional", "functional": ["Given a long URL, return a short URL", "Given a short URL, redirect to the long URL", "Track click analytics (volume, location)", "Custom short links (optional)"], "nonFunctional": ["High availability for redirects", "URL redirection must have low latency (< 50ms)", "Short URLs should not be predictable", "Abuse prevention (rate limiting)"]},
                {"type": "text", "content": "Scale: 100M new URLs/month, 10B redirects/month (1:100 write/read ratio)."}
            ],
        },
        {
            "id": "entities",
            "stepNumber": 3,
            "label": "SCHEMA",
            "title": "Concrete Database Schema",
            "blocks": [
                {"type": "text", "content": "At the mid-level, you must define the schema. A relational database (PostgreSQL) is perfect here due to ACID properties, though a key-value store works if designed correctly."},
                {"type": "entity-table", "entities": [
                    {"name": "urls", "purpose": "id (BIGINT, PK), short_code (VARCHAR(7), UNIQUE INDEX), long_url (VARCHAR(2048)), user_id (INT), created_at (TIMESTAMP)"},
                    {"name": "analytics", "purpose": "id (BIGINT, PK), short_code (VARCHAR(7), INDEX), click_time (TIMESTAMP), ip_address (VARCHAR(45)), referer (VARCHAR(255))"},
                ]},
                {"type": "callout", "variant": "info", "title": "Index Considerations", "content": "The redirect path queries by `short_code`. Therefore, a UNIQUE INDEX on `short_code` is mandatory. The `long_url` doesn't strictly need an index unless we want to prevent duplicate short links for the same long URL (which requires an index and adds write latency)."},
            ],
        },
        {
            "id": "api-design",
            "stepNumber": 4,
            "label": "API DESIGN",
            "title": "API Design",
            "blocks": [
                {"type": "api-table", "endpoints": [
                    {"method": "POST", "endpoint": "/api/v1/urls", "description": "Body: { long_url: string, custom_alias?: string }. Returns 201 Created with short_url."},
                    {"method": "GET", "endpoint": "/{short_code}", "description": "Returns 301 or 302 Redirect to long_url."},
                ]},
                {"type": "comparison", "title": "Redirect Status Codes", "optionA": {"label": "301 Moved Permanently", "description": "Browser caches the redirect. Reduces server load."}, "optionB": {"label": "302 Found", "description": "Browser does NOT cache the redirect. Hits server every time."}, "recommendation": "302 Found", "rationale": "If analytics tracking is a requirement, we must use 302 so the browser hits our server on every click. If latency/load is the only concern, 301 is better."},
            ],
        },
        {
            "id": "deep-dive-encoding",
            "stepNumber": 5,
            "label": "DEEP DIVE",
            "title": "Encoding Strategy: Hash vs Base62",
            "blocks": [
                {"type": "text", "content": "How do we generate the 7-character short code?"},
                {"type": "comparison", "title": "Encoding Approaches", "optionA": {"label": "Hash (MD5) + Base62", "description": "Hash long URL, take first 7 chars."}, "optionB": {"label": "Unique ID Generator + Base62", "description": "Generate unique integer, convert to Base62."}, "recommendation": "Unique ID + Base62", "rationale": "Hashing causes collisions. Generating a unique integer (via Snowflake, Ticket Server, or DB auto-increment) and converting it to Base62 (A-Z, a-z, 0-9) guarantees uniqueness. A 64-bit integer easily fits into 7 Base62 characters (62^7 = 3.5 trillion URLs)."},
                {"type": "callout", "variant": "warning", "title": "The Concurrency Trap", "content": "If you use a centralized DB auto-increment ID, it becomes a single point of failure and a write bottleneck. Better approach: Use ZooKeeper or a Redis-based Ticket Server to allocate 'ranges' (e.g., 1-100,000) to individual app servers. The app server hands out IDs from memory, eliminating DB round-trips for ID generation."},
            ],
        },
        {
            "id": "hld",
            "stepNumber": 6,
            "label": "ARCHITECTURE",
            "title": "High-Level Design",
            "blocks": [
                {"type": "architecture-flow", "nodes": [
                    {"label": "Client", "type": "supporting"},
                    {"label": "Load Balancer", "type": "critical"},
                    {"label": "Web Servers", "type": "critical"},
                    {"label": "Redis Cache", "type": "critical"},
                    {"label": "PostgreSQL", "type": "critical"},
                    {"label": "Range Allocator (ZooKeeper)", "type": "supporting"},
                ], "connections": [
                    {"from": "Client", "to": "Load Balancer", "style": "unidirectional"},
                    {"from": "Load Balancer", "to": "Web Servers", "style": "unidirectional"},
                    {"from": "Web Servers", "to": "Range Allocator (ZooKeeper)", "style": "unidirectional"},
                    {"from": "Web Servers", "to": "Redis Cache", "style": "bidirectional"},
                    {"from": "Web Servers", "to": "PostgreSQL", "style": "bidirectional"},
                ], "explanation": "On POST: Web server gets an ID from its local range (provisioned by ZooKeeper), encodes to Base62, writes to Postgres, and returns. On GET: Web server checks Redis. If miss, queries Postgres, updates Redis, and redirects."},
            ],
        },
        {
            "id": "deep-dive-caching",
            "stepNumber": 7,
            "label": "DEEP DIVE",
            "title": "Caching & Connection Pooling",
            "blocks": [
                {"type": "text", "content": "At 10B reads/month (~4,000 reads/sec), the database will struggle if every read misses the cache. An LRU (Least Recently Used) eviction policy in Redis is ideal, as a small percentage of links (e.g., viral tweets) generate the vast majority of traffic (Pareto principle)."},
                {"type": "callout", "variant": "definition", "title": "Cache Stampede", "content": "If a highly popular link expires in Redis, thousands of requests will hit the database simultaneously. Fix: Use a probabilistic early expiration, or a distributed mutex (only let one thread query the DB and update the cache while others wait)."},
                {"type": "text", "content": "Connection Pooling: Don't open a new Postgres connection per request. Configure connection pools (e.g., PgBouncer) to multiplex thousands of client connections onto a small number of actual DB connections."},
            ],
        },
        {
            "id": "deep-dive-analytics",
            "stepNumber": 8,
            "label": "DEEP DIVE",
            "title": "Analytics Pipeline",
            "blocks": [
                {"type": "text", "content": "Synchronously writing to the `analytics` table on every redirect will spike redirect latency. Analytics is a classic asynchronous workload."},
                {"type": "callout", "variant": "info", "title": "Implementation", "content": "The web server drops an event into a Kafka topic (`redirect_events`) or an in-memory queue. A background worker cluster consumes from Kafka, batches the writes (e.g., 1,000 at a time), and inserts them into an OLAP database (like ClickHouse) or data lake, which is optimized for analytics aggregations."},
            ],
        },
        {
            "id": "deep-dive-abuse",
            "stepNumber": 9,
            "label": "DEEP DIVE",
            "title": "Abuse Prevention",
            "blocks": [
                {"type": "text", "content": "URL shorteners are heavily targeted by spammers to hide malicious links."},
                {"type": "text", "content": "1. Rate Limiting: Apply a Token Bucket rate limiter per IP/User to prevent automated link generation spam.\\n2. URL Verification: Compare long URLs against Google Safe Browsing API or internal blocklists before shortening.\\n3. CAPTCHA: If an IP exceeds a soft limit, force a CAPTCHA challenge before allowing further creations."},
            ],
        },
        {
            "id": "summary",
            "stepNumber": 10,
            "label": "SUMMARY",
            "title": "Mid-Level Summary",
            "blocks": [
                {"type": "text", "content": "Key implementations: Used a Token Range Allocator (ZooKeeper) + Base62 encoding to guarantee unique, collision-free short codes. Applied Redis LRU caching to handle the 100:1 read-to-write skew, and asynchronous Kafka batching for the analytics pipeline."},
                {"type": "text", "content": "Biggest risks: A Redis cache stampede on viral links. Addressed via mutex locks. Exhaustion of DB connections. Addressed via PgBouncer connection pooling."},
                {"type": "callout", "variant": "info", "title": "Path to Senior", "content": "To elevate this answer to Senior, introduce multi-region active-active architectures. Discuss how to handle global unique ID generation when ranges are split across continents, and how to use Geo-DNS to route users to the nearest cache replica to minimize the 302 redirect latency."},
            ],
        },
    ],
}


NEWS_FEED_BREAKDOWN = {
    "focusAreas": ["Fan-out Models", "Asynchronous Processing", "Data Partitioning", "Caching Strategies"],
    "targetRole": "Senior Software Engineer",
    "totalSections": 10,
    "completedSections": 10,
    "sections": [
        {
            "id": "understand",
            "stepNumber": 1,
            "label": "CONTEXT",
            "title": "Interview Context",
            "blocks": [
                {"type": "text", "content": "The News Feed is a foundational system design question. It tests your ability to handle massive read/write asymmetry and data fan-out. The interviewer wants to see how you balance the user experience (low latency reads) against system cost (high storage/compute on writes)."},
                {"type": "callout", "variant": "warning", "title": "The Celebrity Problem", "content": "You MUST address the 'Justin Bieber problem' (or 'Celebrity Problem'). If someone with 100M followers makes a post, computing their followers' feeds using a naive push-model will completely crash your system."},
            ],
        },
        {
            "id": "requirements",
            "stepNumber": 2,
            "label": "REQUIREMENTS",
            "title": "Requirements",
            "blocks": [
                {"type": "functional-nonfunctional", "functional": ["User can publish a post (text/image)", "User can view a news feed of posts from people they follow", "The feed is sorted by time or relevance"], "nonFunctional": ["High availability (feed must always load)", "Low latency (feed generation < 200ms)", "Eventual consistency is acceptable for new posts"]},
                {"type": "text", "content": "Scale: 300M DAU, each user fetches feed 5 times/day = 1.5B read requests/day (~17,000 QPS). Users post 10M times/day (~115 QPS). Extreme read-heavy workload (150:1 read-to-write ratio)."}
            ],
        },
        {
            "id": "entities",
            "stepNumber": 3,
            "label": "SCHEMA",
            "title": "Data Model",
            "blocks": [
                {"type": "text", "content": "We need tables to represent the social graph and the posts."},
                {"type": "entity-table", "entities": [
                    {"name": "user", "purpose": "id (BIGINT), username, profile_pic_url"},
                    {"name": "post", "purpose": "id (BIGINT, Time-sorted like Snowflake), user_id (BIGINT), content (TEXT), media_url (TEXT), created_at (TIMESTAMP)"},
                    {"name": "user_follow", "purpose": "follower_id (BIGINT), followee_id (BIGINT), created_at (TIMESTAMP). Primary Key is (follower_id, followee_id)"},
                ]},
                {"type": "callout", "variant": "info", "title": "Database Choice", "content": "For `user_follow`, a graph database (Neo4j) is overkill. A relational database (Postgres) or wide-column store (Cassandra) works perfectly. Cassandra is excellent here because we can partition by `follower_id` to quickly fetch all `followee_id`s."},
            ],
        },
        {
            "id": "api-design",
            "stepNumber": 4,
            "label": "API DESIGN",
            "title": "API Design",
            "blocks": [
                {"type": "api-table", "endpoints": [
                    {"method": "POST", "endpoint": "/api/v1/posts", "description": "Body: { content, media_url }. Publishes a new post."},
                    {"method": "GET", "endpoint": "/api/v1/feed?cursor={post_id}&limit=20", "description": "Fetches the news feed for the authenticated user."},
                ]},
                {"type": "text", "content": "Pagination must use cursor-based pagination (e.g., `cursor=post_id`) rather than offset-based. Offset-based pagination (`offset=100`) becomes extremely slow on deep pages and causes duplicate items if new posts are inserted during scrolling."},
            ],
        },
        {
            "id": "deep-dive-fanout",
            "stepNumber": 5,
            "label": "DEEP DIVE",
            "title": "Fan-out Strategies",
            "blocks": [
                {"type": "text", "content": "When User A publishes a post, how do it get to User B's feed? This is called Fan-out."},
                {"type": "comparison", "title": "Fan-out Models", "optionA": {"label": "Fan-out on Write (Push)", "description": "Precompute the feed. When A posts, write the post ID into a cache for every follower."}, "optionB": {"label": "Fan-out on Read (Pull)", "description": "Compute on the fly. When B loads their feed, fetch all followees, then fetch their recent posts and merge."}, "recommendation": "Hybrid Approach", "rationale": "Push is great because reads are O(1) from cache, but it breaks for celebrities (100M writes). Pull is great for celebrities, but too slow if you follow 5,000 people. A Hybrid approach pushes to normal users, but pulls from celebrities on read."},
            ],
        },
        {
            "id": "hld",
            "stepNumber": 6,
            "label": "ARCHITECTURE",
            "title": "High-Level Architecture (Hybrid Model)",
            "blocks": [
                {"type": "architecture-flow", "nodes": [
                    {"label": "API Gateway", "type": "critical"},
                    {"label": "Post Service", "type": "critical"},
                    {"label": "Fan-out Worker", "type": "supporting"},
                    {"label": "Timeline Cache (Redis)", "type": "critical"},
                    {"label": "Feed Generation Service", "type": "critical"},
                    {"label": "Post DB (Cassandra)", "type": "critical"},
                ], "connections": [
                    {"from": "API Gateway", "to": "Post Service", "style": "unidirectional"},
                    {"from": "Post Service", "to": "Post DB (Cassandra)", "style": "unidirectional"},
                    {"from": "Post Service", "to": "Fan-out Worker", "style": "unidirectional"},
                    {"from": "Fan-out Worker", "to": "Timeline Cache (Redis)", "style": "unidirectional"},
                    {"from": "API Gateway", "to": "Feed Generation Service", "style": "bidirectional"},
                    {"from": "Feed Generation Service", "to": "Timeline Cache (Redis)", "style": "bidirectional"},
                ], "explanation": "On Post: Post Service saves to DB and queues a job. Fan-out Worker pushes the Post ID to the Timeline Cache of all active followers (excluding if the poster is a celebrity). On Read: Feed Gen Service gets the user's Timeline Cache, then 'pulls' recent posts from followed celebrities, merges/sorts them in memory, and returns."},
            ],
        },
        {
            "id": "deep-dive-caching",
            "stepNumber": 7,
            "label": "DEEP DIVE",
            "title": "Timeline Cache Details",
            "blocks": [
                {"type": "text", "content": "The Timeline Cache is usually implemented using Redis. We use a Redis List or Sorted Set (ZSET). A ZSET allows us to easily sort by timestamp or an algorithmic score. The key is `feed:user_id`, and the values are `post_id`s (not the full post content, to save memory)."},
                {"type": "callout", "variant": "info", "title": "Memory Optimization", "content": "We do not store the entire history of a user's feed in Redis. We cap the ZSET to the last 500-1000 posts. If a user scrolls past that, we fall back to a slower DB query. We also only keep feeds in cache for 'active' users (e.g., logged in within the last 14 days)."},
            ],
        },
        {
            "id": "deep-dive-ranking",
            "stepNumber": 8,
            "label": "DEEP DIVE",
            "title": "Algorithmic Ranking Pipeline",
            "blocks": [
                {"type": "text", "content": "Chronological sorting is simple (sort by created_at), but modern feeds use relevance ranking."},
                {"type": "text", "content": "Implementation: The Feed Generation Service fetches ~500 post_ids from the cache. It calls a Ranking Service (often gRPC). The Ranking Service fetches features for these posts (e.g., author affinity, engagement rate, image vs text) and runs them through an ML model (like XGBoost or a neural net) to assign a score. The top 20 are returned to the user."},
                {"type": "callout", "variant": "warning", "title": "Latency Budget", "content": "ML inference is slow. To keep the feed latency < 200ms, the Ranking Service must use lightweight models for the 'first pass' ranking, and compute heavy features asynchronously in the background via data pipelines (e.g., Flink/Spark)."},
            ],
        },
        {
            "id": "tradeoffs",
            "stepNumber": 9,
            "label": "TRADE-OFFS",
            "title": "Key Trade-offs",
            "blocks": [
                {"type": "comparison", "title": "Post Storage", "optionA": {"label": "Postgres (Sharded)", "description": "Strong consistency, harder to scale writes."}, "optionB": {"label": "Cassandra", "description": "Eventual consistency, massive write scalability."}, "recommendation": "Cassandra", "rationale": "News feeds are highly write-intensive globally and do not require strict ACID transactions for posts. Cassandra's wide-column model is perfectly suited for time-series append-only data like posts."},
                {"type": "comparison", "title": "Celebrity Threshold", "optionA": {"label": "Static Threshold (>500k followers)", "description": "Easy to implement, hardcoded rule."}, "optionB": {"label": "Dynamic based on read/write ratio", "description": "Complex, highly accurate."}, "recommendation": "Static Threshold", "rationale": "A static threshold (e.g., > 1M followers) is significantly easier to operationalize and test than a dynamic one. You can store 'is_celebrity' as a boolean flag on the user profile."},
            ],
        },
        {
            "id": "summary",
            "stepNumber": 10,
            "label": "SUMMARY",
            "title": "Senior-Level Summary",
            "blocks": [
                {"type": "text", "content": "Key implementations: A Hybrid Fan-out architecture (Push for normal users, Pull for celebrities) to balance O(1) read latency against write explosion. Used Redis ZSETs for fast timeline retrieval (capping at 500 items to save memory), and Cassandra for scalable, highly-available post storage."},
                {"type": "text", "content": "Biggest risks: The 'thundering herd' problem when a celebrity posts and millions pull simultaneously. Addressed by aggressively caching celebrity posts in a CDN or separate read-through cache."},
                {"type": "callout", "variant": "info", "title": "Path to Staff", "content": "To elevate this to Staff level, discuss multi-region active-active architectures (how to ensure a post made in Tokyo appears in a feed in New York within seconds). Discuss Kafka partitioned by user_id to ensure causal ordering of events, and how to handle GDPR 'right to be forgotten' cascades through the caches."},
            ],
        },
    ],
}


RATE_LIMITER_BREAKDOWN = {
    "focusAreas": ["Algorithms", "Redis", "Race Conditions", "Gateway Integration"],
    "targetRole": "SDE-2 / Mid-Level",
    "totalSections": 10,
    "completedSections": 10,
    "sections": [
        {
            "id": "understand",
            "stepNumber": 1,
            "label": "CONTEXT",
            "title": "Interview Context",
            "blocks": [
                {"type": "text", "content": "The Rate Limiter is a standard mid-level system design question. While Staff engineers might be asked to build a highly available, decentralized mesh rate limiter (using CRDTs), SDE-2 and Senior candidates are usually expected to design a centralized, Redis-backed rate limiter that sits at an API Gateway."},
                {"type": "callout", "variant": "warning", "title": "The Trap", "content": "Do not just name algorithms. You must be able to explain how to implement them in Redis, specifically discussing the race conditions (read-modify-write) that occur when two concurrent requests hit the same counter."},
            ],
        },
        {
            "id": "requirements",
            "stepNumber": 2,
            "label": "REQUIREMENTS",
            "title": "Requirements",
            "blocks": [
                {"type": "functional-nonfunctional", "functional": ["Limit requests per user, IP, or API endpoint", "Return HTTP 429 Too Many Requests when limit exceeded", "Provide HTTP headers indicating remaining quota (X-RateLimit-Remaining)"], "nonFunctional": ["Extremely low latency (cannot add > 5ms to API requests)", "High accuracy (no dropped limits under concurrency)", "High availability (should fail open if the limiter dies)"]},
                {"type": "text", "content": "Scale: 10M DAU, 50,000 requests per second globally."}
            ],
        },
        {
            "id": "algorithms",
            "stepNumber": 3,
            "label": "ALGORITHMS",
            "title": "Algorithm Selection",
            "blocks": [
                {"type": "comparison", "title": "Rate Limiting Algorithms", "optionA": {"label": "Fixed Window", "description": "Reset count every minute (e.g., 00:00 to 00:01)."}, "optionB": {"label": "Token Bucket", "description": "Refill tokens at a constant rate. Requests consume tokens."}, "recommendation": "Token Bucket", "rationale": "Fixed Window has a boundary spike problem (users can send 2x their limit if they span the minute boundary). Token Bucket smooths out traffic, allows for occasional bursts, and is memory-efficient (just storing a count and a timestamp)."},
            ],
        },
        {
            "id": "deep-dive-redis",
            "stepNumber": 4,
            "label": "DEEP DIVE",
            "title": "Redis Data Model",
            "blocks": [
                {"type": "text", "content": "We store the state in an in-memory datastore like Redis because disk databases (Postgres) are too slow for <5ms latency requirements."},
                {"type": "callout", "variant": "info", "title": "Token Bucket Schema", "content": "Key: `rate:user_id:123`\\nValue (Hash): `{ 'tokens': 8, 'last_refill': 1632145000 }`\\n\\nWhen a request comes in, we calculate how many tokens to add based on `now - last_refill`. If `tokens > 0`, we decrement and allow. Else, we reject."},
            ],
        },
        {
            "id": "deep-dive-race",
            "stepNumber": 5,
            "label": "DEEP DIVE",
            "title": "Handling Race Conditions",
            "blocks": [
                {"type": "text", "content": "The biggest technical hurdle: If two requests arrive at exactly the same millisecond, they might both read `tokens=1`, both decrement, and both succeed. You just allowed 2 requests when only 1 token was left."},
                {"type": "comparison", "title": "Concurrency Solutions", "optionA": {"label": "Redis Locks / Mutex", "description": "Lock the key, read, write, unlock."}, "optionB": {"label": "Lua Scripting", "description": "Send the logic to Redis to execute atomically."}, "recommendation": "Lua Scripting", "rationale": "Locks kill performance and introduce deadlock risks. Redis is single-threaded. By sending a small Lua script to Redis (EVAL), the entire read-modify-write operation happens atomically without locks, guaranteeing correctness and maximum throughput."},
            ],
        },
        {
            "id": "hld",
            "stepNumber": 6,
            "label": "ARCHITECTURE",
            "title": "High-Level Architecture",
            "blocks": [
                {"type": "architecture-flow", "nodes": [
                    {"label": "Client", "type": "supporting"},
                    {"label": "Load Balancer", "type": "supporting"},
                    {"label": "API Gateway", "type": "critical"},
                    {"label": "Rate Limiter Worker (Sidecar)", "type": "critical"},
                    {"label": "Redis Cluster", "type": "critical"},
                    {"label": "Backend Services", "type": "supporting"},
                ], "connections": [
                    {"from": "Client", "to": "Load Balancer", "style": "unidirectional"},
                    {"from": "Load Balancer", "to": "API Gateway", "style": "unidirectional"},
                    {"from": "API Gateway", "to": "Rate Limiter Worker (Sidecar)", "style": "bidirectional"},
                    {"from": "Rate Limiter Worker (Sidecar)", "to": "Redis Cluster", "style": "bidirectional"},
                    {"from": "API Gateway", "to": "Backend Services", "style": "unidirectional"},
                ], "explanation": "The API Gateway delegates the decision to a local sidecar or library. The limiter runs the Lua script against the Redis Cluster. If allowed, the Gateway proxies the request to the Backend. If rejected, it immediately returns HTTP 429."},
            ],
        },
        {
            "id": "deep-dive-scale",
            "stepNumber": 7,
            "label": "DEEP DIVE",
            "title": "Scaling Redis",
            "blocks": [
                {"type": "text", "content": "At 50,000 QPS, a single Redis node might survive, but it's dangerously close to maxing out a single core (Redis usually tops out around 80k-100k ops/sec per core)."},
                {"type": "callout", "variant": "info", "title": "Sharding", "content": "We must deploy a Redis Cluster. We shard the data using consistent hashing on the `user_id` or `IP`. This distributes the 50k QPS across 5-10 Redis nodes, giving us plenty of headroom."},
            ],
        },
        {
            "id": "api-design",
            "stepNumber": 8,
            "label": "API DESIGN",
            "title": "Client Experience",
            "blocks": [
                {"type": "text", "content": "A good API doesn't just block users; it tells them *why* and *when* they can try again."},
                {"type": "api-table", "endpoints": [
                    {"method": "HEADERS", "endpoint": "X-Ratelimit-Remaining", "description": "Tells the client how many requests they have left in the current window."},
                    {"method": "HEADERS", "endpoint": "X-Ratelimit-Reset", "description": "Timestamp (epoch) of when the limit will fully reset."},
                    {"method": "HEADERS", "endpoint": "Retry-After", "description": "Returned only on 429. Tells the client to sleep for X seconds."},
                ]},
            ],
        },
        {
            "id": "tradeoffs",
            "stepNumber": 9,
            "label": "TRADE-OFFS",
            "title": "Key Trade-offs",
            "blocks": [
                {"type": "comparison", "title": "Failure Mode", "optionA": {"label": "Fail Closed", "description": "If Redis is down, reject all traffic (500 Error)."}, "optionB": {"label": "Fail Open", "description": "If Redis is down, allow all traffic through."}, "recommendation": "Fail Open", "rationale": "Rate limiting is a defensive mechanism, not a critical business path. If the limiter breaks, it's better to risk overwhelming the backend than to guarantee a 100% outage for all customers. Set tight timeouts (e.g., 20ms) on Redis calls to trigger the fail-open fast."},
            ],
        },
        {
            "id": "summary",
            "stepNumber": 10,
            "label": "SUMMARY",
            "title": "Mid-Level Summary",
            "blocks": [
                {"type": "text", "content": "Key implementations: Selected the Token Bucket algorithm for its smooth traffic shaping and memory efficiency. Stored state in a sharded Redis Cluster to handle 50k QPS. Used Lua Scripts to guarantee atomic read-modify-write operations, preventing race conditions."},
                {"type": "text", "content": "Biggest risks: Redis node failure causing an outage. Addressed by designing the Gateway to 'Fail Open' on Redis timeouts, ensuring the core platform remains available."},
                {"type": "callout", "variant": "info", "title": "Path to Senior", "content": "To elevate this to Senior, discuss Multi-DC (Multi-Datacenter) routing. If a user is active in both US-East and US-West, how do you synchronize their rate limits across continents? (Hint: You usually don't synchronize synchronously; you either allocate local quotas or use eventual consistency)."},
            ],
        },
    ],
}


CHAT_SYSTEM_BREAKDOWN = {
    "focusAreas": ["WebSocket Management", "Message Ordering", "Database Schema", "Push Notifications"],
    "targetRole": "SDE-2 / Mid-Level",
    "totalSections": 10,
    "completedSections": 10,
    "sections": [
        {
            "id": "understand",
            "stepNumber": 1,
            "label": "CONTEXT",
            "title": "Interview Context",
            "blocks": [
                {"type": "text", "content": "Chat systems (like WhatsApp or Messenger) are primarily stateful connection management problems disguised as database problems. The interviewer wants to know how you route messages to a user whose IP address constantly changes as they switch from WiFi to Cellular."},
                {"type": "callout", "variant": "warning", "title": "The Trap", "content": "HTTP is stateless and unidirectional (client requests, server responds). You cannot build a real-time chat app by having the client 'poll' the server every second for new messages. You must explicitly discuss persistent, bidirectional connections (WebSockets)."},
            ],
        },
        {
            "id": "requirements",
            "stepNumber": 2,
            "label": "REQUIREMENTS",
            "title": "Requirements",
            "blocks": [
                {"type": "functional-nonfunctional", "functional": ["1:1 chat and Group chat (up to 100 people)", "Online/Offline presence indicator", "Store chat history", "Push notifications for offline users"], "nonFunctional": ["Low latency delivery (< 100ms)", "High availability (can't lose messages)", "Scales to 50M DAU"]},
                {"type": "text", "content": "Scale: 50M DAU sending 40 messages/day = 2B messages/day. Peak traffic ~50,000 messages/sec."}
            ],
        },
        {
            "id": "entities",
            "stepNumber": 3,
            "label": "SCHEMA",
            "title": "Data Model",
            "blocks": [
                {"type": "text", "content": "We need highly scalable storage for messages. Cassandra or HBase are standard choices due to their write-heavy optimizations."},
                {"type": "entity-table", "entities": [
                    {"name": "messages", "purpose": "message_id (BIGINT), channel_id (BIGINT), sender_id (BIGINT), content (TEXT), created_at (TIMESTAMP)"},
                    {"name": "channels", "purpose": "channel_id (BIGINT), type (ENUM: 1on1, group), created_at (TIMESTAMP)"},
                    {"name": "channel_members", "purpose": "channel_id (BIGINT), user_id (BIGINT), last_read_message_id (BIGINT)"},
                ]},
                {"type": "callout", "variant": "info", "title": "Message ID Generation", "content": "Do NOT use database auto-increment for `message_id`. Use a Snowflake ID generator. This guarantees global uniqueness and preserves time-ordering, allowing clients to simply sort by `message_id` to display conversations accurately."},
            ],
        },
        {
            "id": "api-design",
            "stepNumber": 4,
            "label": "API DESIGN",
            "title": "Connection & API Protocols",
            "blocks": [
                {"type": "comparison", "title": "Communication Protocols", "optionA": {"label": "HTTP Long Polling", "description": "Client opens request, server holds it until a message arrives."}, "optionB": {"label": "WebSockets", "description": "Bidirectional, persistent TCP connection."}, "recommendation": "WebSockets", "rationale": "WebSockets carry vastly less overhead than Long Polling. Once the handshake is complete, sending a message is just framing a few bytes over an open TCP socket, easily hitting the < 100ms latency requirement."},
                {"type": "text", "content": "While receiving messages must use WebSockets, sending messages or uploading media can still use standard HTTP POST requests for simplicity, though sending via the WebSocket is also acceptable."},
            ],
        },
        {
            "id": "hld",
            "stepNumber": 5,
            "label": "ARCHITECTURE",
            "title": "High-Level Architecture",
            "blocks": [
                {"type": "architecture-flow", "nodes": [
                    {"label": "Client A", "type": "supporting"},
                    {"label": "API Gateway", "type": "critical"},
                    {"label": "Chat Server (WebSocket)", "type": "critical"},
                    {"label": "Session Service (Redis)", "type": "critical"},
                    {"label": "Message Queue (Kafka)", "type": "critical"},
                    {"label": "Database (Cassandra)", "type": "supporting"},
                    {"label": "Client B", "type": "supporting"},
                ], "connections": [
                    {"from": "Client A", "to": "API Gateway", "style": "unidirectional"},
                    {"from": "API Gateway", "to": "Chat Server (WebSocket)", "style": "bidirectional"},
                    {"from": "Chat Server (WebSocket)", "to": "Session Service (Redis)", "style": "bidirectional"},
                    {"from": "Chat Server (WebSocket)", "to": "Message Queue (Kafka)", "style": "unidirectional"},
                    {"from": "Message Queue (Kafka)", "to": "Database (Cassandra)", "style": "unidirectional"},
                    {"from": "Message Queue (Kafka)", "to": "Chat Server (WebSocket)", "style": "unidirectional"},
                ], "explanation": "The core problem: Client A is connected to Chat Server #1. Client B is connected to Chat Server #99. How does Server #1 send a message to B? It queries the Session Service (Redis) to find out B is on Server #99, then routes the message to Server #99 via an internal Message Queue (Kafka/Redis PubSub)."},
            ],
        },
        {
            "id": "deep-dive-routing",
            "stepNumber": 6,
            "label": "DEEP DIVE",
            "title": "Message Routing & Delivery",
            "blocks": [
                {"type": "text", "content": "Let's walk through the exact flow when User A sends a message to User B:"},
                {"type": "text", "content": "1. User A sends payload to Chat Server #1.\\n2. Server #1 generates a Snowflake `message_id` and queues it to Kafka to be saved to Cassandra.\\n3. Server #1 asks Session Service (Redis): 'Which server holds User B's WebSocket?'\\n4. If Redis says 'Server #99', Server #1 publishes to a Kafka topic that Server #99 listens to.\\n5. Server #99 receives the message and pushes it down the WebSocket to User B."},
                {"type": "callout", "variant": "info", "title": "Offline Users", "content": "What if Redis says User B is not connected? Server #1 instead routes the message to a Push Notification Service (APNs/FCM) to wake up User B's phone."},
            ],
        },
        {
            "id": "deep-dive-presence",
            "stepNumber": 7,
            "label": "DEEP DIVE",
            "title": "Online Presence (Green Dot)",
            "blocks": [
                {"type": "text", "content": "Managing the 'Online' status for 50M users is notoriously difficult. If you update a database every time a user opens/closes the app, you will crush the database."},
                {"type": "callout", "variant": "definition", "title": "Heartbeat Pattern", "content": "When a client is connected, it sends a 'ping' over the WebSocket every 5 seconds. The Chat Server updates a Redis key with a TTL of 10 seconds: `SET presence:user_id ONLINE EX 10`. If the connection drops ungracefully, the key expires on its own, marking the user offline."},
                {"type": "text", "content": "To show the green dot to a user's friends, we don't push presence changes globally (O(N^2) problem). Instead, when a user opens the app, they 'Pull' the presence of their active chat list from Redis."},
            ],
        },
        {
            "id": "deep-dive-sync",
            "stepNumber": 8,
            "label": "DEEP DIVE",
            "title": "State Synchronization",
            "blocks": [
                {"type": "text", "content": "When a user comes back online after being offline for 2 days, how do they get missed messages?"},
                {"type": "text", "content": "The client tracks its `last_seen_message_id`. On connect, it sends an HTTP request: `GET /messages?channel_id=X&after=last_seen_message_id`. The server queries Cassandra and returns the delta. This makes the client the source of truth for its own sync state."},
            ],
        },
        {
            "id": "tradeoffs",
            "stepNumber": 9,
            "label": "TRADE-OFFS",
            "title": "Key Trade-offs",
            "blocks": [
                {"type": "comparison", "title": "Delivery Guarantees", "optionA": {"label": "At-Most-Once", "description": "Fire and forget. Fast, but messages get lost on network drops."}, "optionB": {"label": "At-Least-Once", "description": "Server waits for client ACK. If no ACK, server retries."}, "recommendation": "At-Least-Once", "rationale": "Users hate lost messages. We require the client to send an ACK back over the WebSocket. If the server doesn't get the ACK within 5 seconds, it re-sends. The client must use the `message_id` to deduplicate on their end."},
            ],
        },
        {
            "id": "summary",
            "stepNumber": 10,
            "label": "SUMMARY",
            "title": "Mid-Level Summary",
            "blocks": [
                {"type": "text", "content": "Key implementations: Used WebSockets for bidirectional low-latency communication. Managed routing via a centralized Redis Session Store, and decoupled database writes via Kafka. Used a Snowflake ID for chronological, globally unique message IDs."},
                {"type": "text", "content": "Biggest risks: Managing stateful WebSocket servers. When a server goes down for deployment, 500,000 users disconnect and immediately reconnect, causing a 'Thundering Herd'. Addressed via exponential backoff in the client code."},
                {"type": "callout", "variant": "info", "title": "Path to Senior", "content": "To elevate this answer, discuss End-to-End Encryption (E2EE). Explain how the server never sees plaintext, but only routes encrypted ciphertexts, requiring a Key Management Service (like Signal Protocol) to distribute public keys between users."},
            ],
        },
    ],
}

QUESTIONS = [
    {
        "slug": "design-dropbox",
        "title": "Design Dropbox",
        "track": "hld",
        "difficulty": "foundation",
        "timeboxMinutes": 40,
        "prompt": "Design a file storage and synchronization system that allows users to upload, download, share, and synchronize files across devices.",
        "outline": ["Understand the problem and core requirements", "Functional and non-functional requirements", "Core entities: User, File, Folder, FileVersion, Device", "API design for upload, download, share, and version management", "Solution evolution from naive to production architecture", "High-level design with metadata/blob separation", "Deep dive: handling large files with presigned URLs", "Key trade-offs: consistency, processing, regions, storage"],
        "sources": ["https://github.com/donnemartin/system-design-primer"],
        "status": "published",
        "discoveredBy": None,
        "versions": [
            {"role": "sde-2", "levelBar": "Working API design with clear entity model and basic upload/download flow.", "breakdown": DROPBOX_BREAKDOWN},
            {"role": "senior", "levelBar": "Metadata vs blob separation, presigned URLs, and consistency trade-offs explained.", "breakdown": DROPBOX_BREAKDOWN},
            {"role": "staff", "levelBar": "Multi-region strategy, chunked upload pipeline, and sync conflict resolution.", "breakdown": DROPBOX_BREAKDOWN},
            {"role": "principal", "levelBar": "Platform-level file storage, compliance (GDPR deletion), cost modeling at scale.", "breakdown": DROPBOX_BREAKDOWN},
        ],
    },
    {
        "slug": "url-shortener",
        "title": "Design a URL shortener",
        "track": "hld",
        "difficulty": "foundation",
        "timeboxMinutes": 45,
        "prompt": "Design a service like bit.ly: users submit a long URL and receive a short link that redirects with high availability.",
        "outline": ["Functional vs non-functional requirements", "API: create, redirect, analytics, auth", "Encoding strategy (hash vs counter) and collision handling", "Data model, cache, and 301 vs 302", "Scale: write path, read-heavy redirects, abuse and rate limits"],
        "sources": ["https://github.com/donnemartin/system-design-primer", "https://news.ycombinator.com"],
        "status": "published",
        "discoveredBy": None,
        "versions": [
            {"role": "sde-2", "levelBar": "A working API, a table, a cache, and a clear encoding choice.", "breakdown": URL_SHORTENER_BREAKDOWN},
            {"role": "senior", "levelBar": "Capacity numbers, cache TTL, and what happens when two writers collide.", "breakdown": URL_SHORTENER_BREAKDOWN},
            {"role": "staff", "levelBar": "Global uniqueness, analytics pipeline, custom domains, and a rollout that does not break old links.", "breakdown": URL_SHORTENER_BREAKDOWN},
            {"role": "principal", "levelBar": "Multi-region, GDPR deletion, partner SLAs, and how this becomes a platform other teams consume.", "breakdown": URL_SHORTENER_BREAKDOWN},
        ],
    },
    {
        "slug": "news-feed",
        "title": "Design a news feed",
        "track": "hld",
        "difficulty": "core",
        "timeboxMinutes": 45,
        "prompt": "Design the home feed for a social product: posts from people you follow, ranked, with likes and near-real-time updates.",
        "outline": ["Read vs write fan-out and celebrity problem", "Feed generation service and ranking signals", "Storage: posts, graph, precomputed timelines", "Push notifications and unread state", "Consistency: what is allowed to be stale"],
        "sources": ["https://github.com/donnemartin/system-design-primer"],
        "status": "published",
        "discoveredBy": None,
        "versions": [
            {"role": "senior", "levelBar": "Fan-out on write vs read, a timeline store, and pagination.", "breakdown": NEWS_FEED_BREAKDOWN},
            {"role": "staff", "levelBar": "Hybrid fan-out, ranking model isolation, and how you recover a corrupt timeline.", "breakdown": NEWS_FEED_BREAKDOWN},
            {"role": "principal", "levelBar": "Company-wide feed platform, experimentation, and cost of precompute at 100M DAU.", "breakdown": NEWS_FEED_BREAKDOWN},
        ],
    },
    {
        "slug": "rate-limiter",
        "title": "Design a rate limiter",
        "track": "hld",
        "difficulty": "foundation",
        "timeboxMinutes": 40,
        "prompt": "Protect an API gateway so clients cannot exceed N requests per window, consistently across many machines.",
        "outline": ["Algorithms: token bucket, leaky bucket, fixed and sliding window", "Where it lives: gateway vs sidecar vs library", "Redis counters, Lua, and clock skew", "Headers, 429, and burst vs sustained limits", "Per-user, per-IP, and per-endpoint rules"],
        "sources": ["https://github.com/donnemartin/system-design-primer"],
        "status": "published",
        "discoveredBy": None,
        "versions": [
            {"role": "sde-2", "levelBar": "Name an algorithm and put counters in Redis.", "breakdown": RATE_LIMITER_BREAKDOWN},
            {"role": "senior", "levelBar": "Accuracy vs memory, race conditions, and client-facing headers.", "breakdown": RATE_LIMITER_BREAKDOWN},
            {"role": "staff", "levelBar": "Multi-DC limits, rule config as data, and graceful degradation if Redis is down.", "breakdown": RATE_LIMITER_BREAKDOWN},
        ],
    },
    {
        "slug": "chat-system",
        "title": "Design a chat system",
        "track": "hld",
        "difficulty": "core",
        "timeboxMinutes": 45,
        "prompt": "Design 1:1 and group messaging with online presence, unread counts, and media attachments.",
        "outline": ["WebSocket vs long-poll and connection management", "Message store, fan-out to group members", "Ordering, retries, and exactly-once vs at-least-once", "Presence service and unread badges", "Media pipeline and encryption at rest"],
        "sources": ["https://github.com/donnemartin/system-design-primer"],
        "status": "published",
        "discoveredBy": None,
        "versions": [
            {"role": "senior", "levelBar": "Connection layer, message table, and a story for offline users.", "breakdown": CHAT_SYSTEM_BREAKDOWN},
            {"role": "staff", "levelBar": "Partitioning conversations, fan-out for large groups, and delivery receipts.", "breakdown": CHAT_SYSTEM_BREAKDOWN},
            {"role": "principal", "levelBar": "Compliance holds, e2e encryption tradeoffs, and a multi-tenant chat platform.", "breakdown": CHAT_SYSTEM_BREAKDOWN},
        ],
    },
    {
        "slug": "parking-lot",
        "title": "Design a parking lot",
        "track": "lld",
        "difficulty": "foundation",
        "timeboxMinutes": 35,
        "prompt": "Model a parking lot with multiple floors, vehicle types, tickets, and hourly billing.",
        "outline": ["Entities: Lot, Floor, Spot, Vehicle, Ticket, Pricing", "Spot allocation strategy by vehicle size", "Entry/exit flows and concurrency at gates", "Fees, receipts, and occupancy queries", "What changes if we add EV charging or reservations"],
        "sources": ["https://github.com/ashishps1/awesome-low-level-design"],
        "status": "published",
        "discoveredBy": None,
        "versions": [
            {"role": "sde-1", "levelBar": "Clear classes and a happy-path park/leave flow."},
            {"role": "sde-2", "levelBar": "Strategy for assignment and a testable pricing module."},
            {"role": "senior", "levelBar": "Concurrency, extension points, and why you did not over-abstract."},
        ],
    },
    {
        "slug": "lru-cache",
        "title": "Implement an LRU cache",
        "track": "lld",
        "difficulty": "foundation",
        "timeboxMinutes": 30,
        "prompt": "Build get/put with O(1) average time and a fixed capacity that evicts the least recently used key.",
        "outline": ["Node structure and map from key to node", "Move-to-front on get/put", "Eviction on overflow", "Generics, nulls, and capacity of zero", "Optional: TTL, metrics, and locking"],
        "sources": ["https://github.com/ashishps1/awesome-low-level-design"],
        "status": "published",
        "discoveredBy": None,
        "versions": [
            {"role": "sde-1", "levelBar": "Correct O(1) get/put with a walkthrough of eviction."},
            {"role": "sde-2", "levelBar": "Clean API, tests, and a note on concurrency."},
            {"role": "senior", "levelBar": "When LRU is the wrong policy and how you would shard a cache."},
        ],
    },
    {
        "slug": "splitwise",
        "title": "Design Splitwise",
        "track": "lld",
        "difficulty": "core",
        "timeboxMinutes": 40,
        "prompt": "Users add expenses in a group. The system tracks who owes whom and can simplify the debt graph.",
        "outline": ["User, Group, Expense, Split types (equal, exact, percent)", "Balance sheet vs event log", "Simplify: min cash-flow heuristic vs exact min transfers", "Invariants and rounding", "What is hard about concurrent edits"],
        "sources": ["https://github.com/ashishps1/awesome-low-level-design"],
        "status": "published",
        "discoveredBy": None,
        "versions": [
            {"role": "sde-2", "levelBar": "Correct split types and a balance map."},
            {"role": "senior", "levelBar": "Simplify algorithm, rounding, and an audit log."},
            {"role": "staff", "levelBar": "Multi-currency, idempotent APIs, and consistency under concurrent adds."},
        ],
    },
    {
        "slug": "two-pointers-family",
        "title": "Two pointers and sliding window",
        "track": "coding",
        "difficulty": "foundation",
        "timeboxMinutes": 25,
        "prompt": "Given an array or string, find a subarray/substring that meets a constraint (sum, uniqueness, or pair target).",
        "outline": ["When two pointers beat nested loops", "Expand/contract window invariants", "Off-by-one and empty input", "Talk complexity out loud before coding", "One follow-up: streaming or very large input"],
        "sources": ["https://leetcode.com/explore/interview/card/top-interview-questions-easy/"],
        "status": "published",
        "discoveredBy": None,
        "versions": [
            {"role": "sde-1", "levelBar": "A correct window with tests for empty and all-invalid cases."},
            {"role": "sde-2", "levelBar": "Clean helper functions and a second variant without restarting from scratch."},
        ],
    },
    {
        "slug": "graphs-bfs-dfs",
        "title": "Graph traversal: BFS and DFS",
        "track": "coding",
        "difficulty": "core",
        "timeboxMinutes": 30,
        "prompt": "You are given a graph or grid. Search, shortest path in unweighted graphs, or connected components.",
        "outline": ["Adjacency list vs matrix", "Visited set and cycle handling", "BFS for shortest unweighted path", "DFS recursion vs explicit stack", "Follow-up: topological sort or union-find"],
        "sources": ["https://leetcode.com/explore/interview/card/top-interview-questions-medium/"],
        "status": "published",
        "discoveredBy": None,
        "versions": [
            {"role": "sde-1", "levelBar": "Correct traversal that does not infinite-loop."},
            {"role": "sde-2", "levelBar": "Clean modeling of the graph and complexity."},
            {"role": "senior", "levelBar": "How this maps to a production job (crawler, build system) and failure modes."},
        ],
    },
    {
        "slug": "conflict-with-a-peer",
        "title": "A time you disagreed with a peer",
        "track": "behavioral",
        "difficulty": "foundation",
        "timeboxMinutes": 8,
        "prompt": "Tell me about a time you disagreed with a teammate on a technical or product decision. What happened?",
        "outline": ["Situation in two sentences", "The actual disagreement (not personality)", "What you tried, including listening", "The decision and your part in it", "What you changed afterward"],
        "sources": [],
        "status": "published",
        "discoveredBy": None,
        "versions": [
            {"role": "sde-1", "levelBar": "A real example, no blame, a concrete outcome."},
            {"role": "sde-2", "levelBar": "You influenced the design, not just complied."},
            {"role": "senior", "levelBar": "You de-risked the team and left a written decision."},
            {"role": "staff", "levelBar": "You aligned multiple teams and protected the user/org, not your ego."},
            {"role": "principal", "levelBar": "You changed a principle or process so the conflict does not recur at scale."},
        ],
    },
    {
        "slug": "incident-ownership",
        "title": "Owning an incident",
        "track": "behavioral",
        "difficulty": "core",
        "timeboxMinutes": 8,
        "prompt": "Walk through an outage or serious bug. How did you detect, mitigate, communicate, and prevent recurrence?",
        "outline": ["Detection and severity", "Mitigation vs root cause", "Who you updated and when", "The real root cause, not the symptom", "The durable fix (test, alert, design, process)"],
        "sources": [],
        "status": "published",
        "discoveredBy": None,
        "versions": [
            {"role": "senior", "levelBar": "You drove mitigation and a blameless write-up."},
            {"role": "staff", "levelBar": "You coordinated across services and reduced class-of-failure risk."},
            {"role": "principal", "levelBar": "You changed the platform so this class of incident is harder org-wide."},
        ],
    },
]


async def seed():
    """Seed all collections."""
    client = AsyncIOMotorClient(MONGODB_URI)
    db_name = MONGODB_URI.rsplit("/", 1)[-1].split("?")[0] or "rolewise"
    db = client[db_name]

    now = datetime.utcnow()

    # Seed roles
    existing_roles = await db.roles.count_documents({})
    if existing_roles == 0:
        await db.roles.insert_many(ROLES)
        print(f"✓ Seeded {len(ROLES)} roles")
    else:
        print(f"⊘ Roles already exist ({existing_roles}), skipping")

    # Seed tracks
    existing_tracks = await db.tracks.count_documents({})
    if existing_tracks == 0:
        await db.tracks.insert_many(TRACKS)
        print(f"✓ Seeded {len(TRACKS)} tracks")
    else:
        print(f"⊘ Tracks already exist ({existing_tracks}), skipping")

    # Seed questions
    print("Upserting questions...")
    for q in QUESTIONS:
        q["updatedAt"] = now
        await db.questions.update_one(
            {"slug": q["slug"]},
            {"$set": q, "$setOnInsert": {"createdAt": now}},
            upsert=True
        )
    print(f"✓ Upserted {len(QUESTIONS)} questions")

    # Create indexes
    await db.questions.create_index("slug", unique=True)
    await db.questions.create_index("track")
    await db.questions.create_index("status")
    await db.questions.create_index("versions.role")
    await db.agent_drafts.create_index("status")
    await db.agent_drafts.create_index("slug")
    await db.user_progress.create_index([("userId", 1), ("questionSlug", 1)], unique=True)
    print("✓ Created indexes")

    client.close()
    print("\n✅ Seed complete!")


if __name__ == "__main__":
    asyncio.run(seed())
