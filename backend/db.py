"""MongoDB connection singleton using Motor (async driver)."""

import os
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

_client: AsyncIOMotorClient | None = None
_db: AsyncIOMotorDatabase | None = None


def get_mongo_uri() -> str:
    return os.getenv("MONGODB_URI", "mongodb://localhost:27017/rolewise")


async def connect_db() -> AsyncIOMotorDatabase:
    """Connect to MongoDB and return the database handle."""
    global _client, _db
    if _db is not None:
        return _db
    uri = get_mongo_uri()
    _client = AsyncIOMotorClient(uri)
    # Extract DB name from URI, default to 'rolewise'
    db_name = uri.rsplit("/", 1)[-1].split("?")[0] or "rolewise"
    _db = _client[db_name]

    # Create indexes for performance
    try:
        # Questions collection
        await _db.questions.create_index("slug", unique=True)
        # Compound index for list queries
        await _db.questions.create_index([
            ("status", 1), 
            ("track", 1), 
            ("difficulty", 1), 
            ("versions.role", 1)
        ])

        # User progress collection
        await _db.user_progress.create_index([
            ("userId", 1), 
            ("questionSlug", 1)
        ], unique=True)
        
        # Agent drafts
        await _db.agent_drafts.create_index("slug", unique=True)
        await _db.agent_drafts.create_index("status")
    except Exception as e:
        print(f"Warning: Failed to create indexes: {e}")

    return _db


async def close_db() -> None:
    """Close MongoDB connection."""
    global _client, _db
    if _client is not None:
        _client.close()
        _client = None
        _db = None


def get_db() -> AsyncIOMotorDatabase:
    """Get the current database handle. Must call connect_db() first."""
    if _db is None:
        raise RuntimeError("Database not connected. Call connect_db() first.")
    return _db
