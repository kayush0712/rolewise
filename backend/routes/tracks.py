"""Tracks read-only endpoints."""

from fastapi import APIRouter, HTTPException

from db import get_db

router = APIRouter()


from async_lru import alru_cache

@alru_cache(maxsize=1)
async def _cached_list_tracks():
    db = get_db()
    cursor = db.tracks.find()
    return [doc async for doc in cursor]


@router.get("")
async def list_tracks():
    """List all tracks."""
    return await _cached_list_tracks()


@alru_cache(maxsize=32)
async def _cached_get_track(slug: str):
    db = get_db()
    return await db.tracks.find_one({"_id": slug})


@router.get("/{slug}")
async def get_track(slug: str):
    """Get a single track by slug."""
    doc = await _cached_get_track(slug)
    if not doc:
        raise HTTPException(status_code=404, detail="Track not found")
    return doc
