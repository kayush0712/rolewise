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

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/rolewise")


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
            {"role": "sde-2", "levelBar": "A working API, a table, a cache, and a clear encoding choice."},
            {"role": "senior", "levelBar": "Capacity numbers, cache TTL, and what happens when two writers collide."},
            {"role": "staff", "levelBar": "Global uniqueness, analytics pipeline, custom domains, and a rollout that does not break old links."},
            {"role": "principal", "levelBar": "Multi-region, GDPR deletion, partner SLAs, and how this becomes a platform other teams consume."},
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
            {"role": "senior", "levelBar": "Fan-out on write vs read, a timeline store, and pagination."},
            {"role": "staff", "levelBar": "Hybrid fan-out, ranking model isolation, and how you recover a corrupt timeline."},
            {"role": "principal", "levelBar": "Company-wide feed platform, experimentation, and cost of precompute at 100M DAU."},
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
            {"role": "sde-2", "levelBar": "Name an algorithm and put counters in Redis."},
            {"role": "senior", "levelBar": "Accuracy vs memory, race conditions, and client-facing headers."},
            {"role": "staff", "levelBar": "Multi-DC limits, rule config as data, and graceful degradation if Redis is down."},
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
            {"role": "senior", "levelBar": "Connection layer, message table, and a story for offline users."},
            {"role": "staff", "levelBar": "Partitioning conversations, fan-out for large groups, and delivery receipts."},
            {"role": "principal", "levelBar": "Compliance holds, e2e encryption tradeoffs, and a multi-tenant chat platform."},
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
    existing_questions = await db.questions.count_documents({})
    if existing_questions == 0:
        for q in QUESTIONS:
            q["createdAt"] = now
            q["updatedAt"] = now
        await db.questions.insert_many(QUESTIONS)
        print(f"✓ Seeded {len(QUESTIONS)} questions")
    else:
        print(f"⊘ Questions already exist ({existing_questions}), skipping")

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
