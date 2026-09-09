"""Tracks read-only endpoints."""

from fastapi import APIRouter, HTTPException

from db import get_db

router = APIRouter()


@router.get("")
async def list_tracks():
    """List all tracks."""
    db = get_db()
    cursor = db.tracks.find()
    return [doc async for doc in cursor]


@router.get("/{slug}")
async def get_track(slug: str):
    """Get a single track by slug."""
    db = get_db()
    doc = await db.tracks.find_one({"_id": slug})
    if not doc:
        raise HTTPException(status_code=404, detail="Track not found")
    return doc
